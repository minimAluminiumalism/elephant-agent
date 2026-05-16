"""Tests for the recall summarisation helper (P1-F)."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.evidence import summarize_recall_hits
from packages.evidence.recall_support import RecallHit


class _SummariseTest(unittest.TestCase):
    def test_empty_returns_empty_string(self) -> None:
        self.assertEqual(summarize_recall_hits(()), "")

    def test_single_hit_has_time_prefix(self) -> None:
        hit = RecallHit(
            title="seed",
            content="Redis is the cache layer",
            kind="knowledge",
            when="2026-04-15",
            score=0.9,
        )
        out = summarize_recall_hits((hit,))
        self.assertIn("[2026-04-15]", out)
        self.assertIn("(knowledge)", out)
        self.assertIn("Redis is the cache layer", out)

    def test_multiple_hits_become_multiline(self) -> None:
        hits = tuple(
            RecallHit(
                title=f"h{i}",
                content=f"content {i}",
                kind="note",
                when="2026-04-15",
                score=0.5,
            )
            for i in range(3)
        )
        out = summarize_recall_hits(hits)
        self.assertEqual(out.count("\n"), 2)  # 3 lines → 2 newlines

    def test_max_lines_cap(self) -> None:
        hits = tuple(
            RecallHit(
                title=f"h{i}",
                content=f"c{i}",
                kind="note",
                when="",
                score=0.5,
            )
            for i in range(10)
        )
        out = summarize_recall_hits(hits, max_lines=3)
        self.assertEqual(out.count("\n"), 2)  # capped at 3 lines

    def test_char_budget_truncates_long_content(self) -> None:
        hit = RecallHit(
            title="long",
            content="x" * 2000,
            kind="note",
            when="2026-04-15",
            score=1.0,
        )
        out = summarize_recall_hits((hit,), char_budget=100)
        # Budget is shared across lines; single line gets most of it.
        self.assertLessEqual(len(out), 200)
        self.assertIn("…", out)

    def test_no_time_when_blank(self) -> None:
        hit = RecallHit(
            title="dateless",
            content="something",
            kind="note",
            when="",
            score=0.5,
        )
        out = summarize_recall_hits((hit,))
        # No "[...]" prefix when when is blank.
        self.assertFalse(out.startswith("["))


if __name__ == "__main__":
    unittest.main()
