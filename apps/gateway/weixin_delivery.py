"""Markdown normalization and delivery chunking helpers for Weixin."""

from __future__ import annotations

import re as _re

_HEADER_RE = _re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_FENCE_RE = _re.compile(r"^```([^\n`]*)\s*$")


def _normalize_markdown_blocks(content: str) -> str:
    lines = content.splitlines()
    result: list[str] = []
    in_code_block = False
    blank_run = 0

    for raw_line in lines:
        line = raw_line.rstrip()
        if _FENCE_RE.match(line.strip()):
            in_code_block = not in_code_block
            result.append(line)
            blank_run = 0
            continue

        if in_code_block:
            result.append(line)
            continue

        if not line.strip():
            blank_run += 1
            if blank_run <= 1:
                result.append("")
            continue

        blank_run = 0
        result.append(line)

    return "\n".join(result).strip()


def _split_markdown_blocks(content: str) -> list[str]:
    if not content:
        return []

    blocks: list[str] = []
    lines = content.splitlines()
    current: list[str] = []
    in_code_block = False

    for raw_line in lines:
        line = raw_line.rstrip()
        if _FENCE_RE.match(line.strip()):
            if not in_code_block and current:
                blocks.append("\n".join(current).strip())
                current = []
            current.append(line)
            in_code_block = not in_code_block
            if not in_code_block:
                blocks.append("\n".join(current).strip())
                current = []
            continue

        if in_code_block:
            current.append(line)
            continue

        if not line.strip():
            if current:
                blocks.append("\n".join(current).strip())
                current = []
            continue
        current.append(line)

    if current:
        blocks.append("\n".join(current).strip())
    return [block for block in blocks if block]


def _split_delivery_units_for_weixin(content: str) -> list[str]:
    units: list[str] = []

    for block in _split_markdown_blocks(content):
        if _FENCE_RE.match(block.splitlines()[0].strip()):
            units.append(block)
            continue

        current: list[str] = []
        for raw_line in block.splitlines():
            line = raw_line.rstrip()
            if not line.strip():
                if current:
                    units.append("\n".join(current).strip())
                    current = []
                continue

            is_continuation = bool(current) and raw_line.startswith((" ", "\t"))
            if is_continuation:
                current.append(line)
                continue

            if current:
                units.append("\n".join(current).strip())
            current = [line]

        if current:
            units.append("\n".join(current).strip())

    return [unit for unit in units if unit]


def _pack_markdown_blocks_for_weixin(content: str, max_length: int) -> list[str]:
    from .platforms.weixin import WeixinMessagingAdapter

    if len(content) <= max_length:
        return [content]

    packed: list[str] = []
    current = ""
    for block in _split_markdown_blocks(content):
        candidate = block if not current else f"{current}\n\n{block}"
        if len(candidate) <= max_length:
            current = candidate
            continue
        if current:
            packed.append(current)
            current = ""
        if len(block) <= max_length:
            current = block
            continue
        packed.extend(WeixinMessagingAdapter.truncate_message(block, max_length))
    if current:
        packed.append(current)
    return packed


def _split_text_for_weixin_delivery(
    content: str,
    max_length: int,
    split_per_line: bool = False,
) -> list[str]:
    if not content:
        return []
    if split_per_line:
        if len(content) <= max_length and "\n" not in content:
            return [content]
        chunks: list[str] = []
        for unit in _split_delivery_units_for_weixin(content):
            if len(unit) <= max_length:
                chunks.append(unit)
                continue
            chunks.extend(_pack_markdown_blocks_for_weixin(unit, max_length))
        return [c for c in chunks if c] or [content]

    if len(content) <= max_length:
        return [content]
    return _pack_markdown_blocks_for_weixin(content, max_length) or [content]
