"""Tests for per-turn ephemeral suffix injection.

The invariants this module protects:

1. The injection only rewrites the LAST user message, and only in a new
   tuple — prior messages are returned by identity, so the stable prefix
   the provider caches stays byte-identical across turns.
2. The original `PromptMessage` objects are never mutated (they are frozen
   dataclasses — this is a belt-and-braces check).
3. Empty blocks short-circuit to the input tuple's identity so no-op calls
   are cheap.
"""

from __future__ import annotations

from typing import Any

from packages.contracts.runtime import PromptMessage
from packages.models.ephemeral_injection import (
    append_ephemeral_suffix_to_last_user,
    ephemeral_blocks_as_user_suffix,
    recall_block_contents,
    safe_call_block_builder,
    strip_recall_blocks,
)


def _msg(role: str, content: str) -> PromptMessage:
    return PromptMessage(role=role, content=content)


def test_ephemeral_blocks_become_user_message_suffix() -> None:
    out = ephemeral_blocks_as_user_suffix(
        blocks=(
            "Current-turn recall support:\n- [rapport] be direct\n",
            "",
        )
    )

    assert out == "Current-turn recall support:\n- [rapport] be direct"


def test_no_blocks_returns_input_tuple_identity() -> None:
    msgs = (_msg("user", "hi"), _msg("assistant", "hello"))
    out = append_ephemeral_suffix_to_last_user(msgs, blocks=())
    assert out is msgs  # identity — nothing to inject, so don't copy


def test_all_empty_blocks_is_noop() -> None:
    msgs = (_msg("user", "hi"),)
    out = append_ephemeral_suffix_to_last_user(msgs, blocks=("", "", ""))
    assert out is msgs


def test_appends_suffix_to_last_user_only() -> None:
    msgs = (
        _msg("user", "first"),
        _msg("assistant", "reply"),
        _msg("user", "second"),
    )
    out = append_ephemeral_suffix_to_last_user(
        msgs,
        blocks=("<elephant:memory>\nA\n</elephant:memory>",),
    )
    # First two messages are the SAME Python objects — critical so the
    # provider's prefix cache still hits on them across turns.
    assert out[0] is msgs[0]
    assert out[1] is msgs[1]
    # Last user is a NEW frozen object carrying the suffix.
    assert out[2] is not msgs[2]
    assert out[2].role == "user"
    assert out[2].content.startswith("second\n\n<elephant:memory>")
    assert out[2].content.endswith("</elephant:memory>")


def test_original_messages_are_not_mutated() -> None:
    original = _msg("user", "keep me")
    msgs = (original,)
    out = append_ephemeral_suffix_to_last_user(msgs, blocks=("<elephant:memory>b</elephant:memory>",))
    # Frozen dataclass: this assertion confirms nothing mutated in place.
    assert original.content == "keep me"
    assert out[0].content != "keep me"


def test_multiple_blocks_joined_with_blank_line() -> None:
    msgs = (_msg("user", "q"),)
    out = append_ephemeral_suffix_to_last_user(
        msgs,
        blocks=(
            "<elephant:memory>\nA\n</elephant:memory>",
            "<elephant:focus>\nB\n</elephant:focus>",
        ),
    )
    content = out[0].content
    assert "<elephant:memory>" in content
    assert "<elephant:focus>" in content
    # User text is preserved at the front, blocks follow it in the given order.
    assert content.startswith("q\n\n<elephant:memory>")
    assert content.index("q") < content.index("<elephant:memory>")
    assert content.index("<elephant:memory>") < content.index("<elephant:focus>")


def test_no_user_message_is_noop() -> None:
    msgs = (_msg("assistant", "only me"), _msg("tool", "r"))
    out = append_ephemeral_suffix_to_last_user(msgs, blocks=("<elephant:memory>y</elephant:memory>",))
    assert out is msgs


def test_injects_into_the_LAST_user_not_the_first() -> None:
    msgs = (
        _msg("user", "first user"),
        _msg("assistant", "reply"),
        _msg("user", "second user"),
        _msg("assistant", "reply2"),
        _msg("user", "third user"),
    )
    out = append_ephemeral_suffix_to_last_user(msgs, blocks=("<elephant:memory>Y</elephant:memory>",))
    # Only the last user turn is suffixed. All prior turns stay identical.
    assert out[0] is msgs[0]
    assert out[2] is msgs[2]
    assert out[4] is not msgs[4]
    assert out[4].content.startswith("third user\n\n<elephant:memory>Y")
    assert out[4].content.endswith("</elephant:memory>")


def test_empty_content_last_user_gets_just_the_suffix() -> None:
    msgs = (_msg("user", ""),)
    out = append_ephemeral_suffix_to_last_user(msgs, blocks=("<elephant:memory>Z</elephant:memory>",))
    # Edge case: when the user text is empty, we still deliver the block so
    # the agent has something to look at on this turn.
    assert out[0].content
    assert "<elephant:memory>Z</elephant:memory>" in out[0].content


def test_recall_block_contents_extracts_embedded_suffix() -> None:
    content = "question\n\nCurrent-turn recall support:\n- [note] remembered\n"

    assert recall_block_contents(content) == ("Current-turn recall support:\n- [note] remembered",)


def test_strip_recall_blocks_preserves_user_text_only() -> None:
    content = "question\n\nCurrent-turn recall support:\n- [note] remembered\n\n\nfollow up"

    assert strip_recall_blocks(content) == "question\n\nfollow up"


def test_safe_call_block_builder_swallows_exceptions() -> None:
    def _boom(*args: Any, **kwargs: Any) -> str:
        raise RuntimeError("should not propagate")

    assert safe_call_block_builder(_boom) == ""


def test_safe_call_block_builder_handles_none() -> None:
    assert safe_call_block_builder(None) == ""


def test_safe_call_block_builder_coerces_to_str() -> None:
    def _builder() -> Any:
        return 123  # non-string

    assert safe_call_block_builder(_builder) == "123"
