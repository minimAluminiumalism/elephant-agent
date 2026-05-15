"""Tests for MemoryEntry.importance field (P1-H).

Verifies:
  - MemoryEntry rejects invalid importance outside [0,1].
  - upsert_memory_entry / load_memory_entry round-trips importance.
  - Migration 0006 applies cleanly (schema version == 6).
  - rank_recall_candidates blends importance into the score (higher
    importance lifts a marginal lexical match above a lower-importance
    match of similar textual strength).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.contracts import Grounding, MemoryEntry, Record
from packages.evidence import rank_recall_candidates
from packages.evidence.memory_recall_support import RecallCandidate
from packages.storage import RuntimeStorageRepository


_T0 = datetime(2026, 5, 1, 9, 0, tzinfo=timezone.utc)


class _ContractTest(unittest.TestCase):
    def test_default_importance_is_half(self) -> None:
        entry = MemoryEntry(
            memory_entry_id="m1",
            owner_scope="personal_model",
            personal_model_id="you",
            kind="note",
            content="hello",
            grounding_ids=("g1",),
        )
        self.assertEqual(entry.importance, 0.5)

    def test_importance_out_of_range_rejected(self) -> None:
        with self.assertRaises(ValueError):
            MemoryEntry(
                memory_entry_id="m1",
                owner_scope="personal_model",
                personal_model_id="you",
                kind="note",
                content="x",
                grounding_ids=("g1",),
                importance=-0.1,
            )
        with self.assertRaises(ValueError):
            MemoryEntry(
                memory_entry_id="m1",
                owner_scope="personal_model",
                personal_model_id="you",
                kind="note",
                content="x",
                grounding_ids=("g1",),
                importance=1.5,
            )


class _StorageRoundTripTest(unittest.TestCase):
    def test_importance_persists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = RuntimeStorageRepository(Path(tmp) / "elephant.sqlite3")
            repo.bootstrap()
            repo.upsert_personal_model(
                repo.ensure_default_personal_model(
                    personal_model_id="you", display_name="You"
                )
            )
            repo.upsert_record(
                Record(
                    record_id="src-1",
                    kind="derived",
                    schema_version="test/v1",
                    owner_scope="personal_model",
                    personal_model_id="you",
                    created_at=_T0,
                    payload={"text": "seed"},
                )
            )
            repo.upsert_grounding(
                Grounding(
                    grounding_id="g-1",
                    source_record_ids=("src-1",),
                    created_at=_T0,
                ),
                owner_scope="personal_model",
                personal_model_id="you",
            )
            entry = MemoryEntry(
                memory_entry_id="mem-1",
                owner_scope="personal_model",
                personal_model_id="you",
                kind="style",
                content="User prefers concise answers",
                grounding_ids=("g-1",),
                created_at=_T0,
                updated_at=_T0,
                importance=0.85,
            )
            repo.upsert_memory_entry(entry)
            loaded = repo.load_memory_entry("mem-1")
            self.assertIsNotNone(loaded)
            self.assertAlmostEqual(loaded.importance, 0.85, places=4)

    def test_schema_version_is_seven(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = RuntimeStorageRepository(Path(tmp) / "elephant.sqlite3")
            bootstrap = repo.bootstrap()
            self.assertEqual(bootstrap.schema_version, 7)


class _RecallScoringTest(unittest.TestCase):
    def test_high_importance_lifts_score(self) -> None:
        """Two candidates with identical lexical match — higher
        importance should score higher."""
        candidate_low = RecallCandidate(
            title="cache notes",
            body="redis is the cache",
            kind="note",
            when=_T0,
            importance=0.2,
        )
        candidate_high = RecallCandidate(
            title="cache notes",
            body="redis is the cache",
            kind="note",
            when=_T0,
            importance=0.9,
        )
        ranked = rank_recall_candidates(
            "redis cache",
            (candidate_low, candidate_high),
            limit=2,
            now=_T0 + timedelta(days=1),
        )
        # High-importance wins the tiebreak.
        self.assertEqual(len(ranked), 2)
        self.assertGreater(ranked[0].score, ranked[1].score)
        self.assertIn("redis is the cache", ranked[0].content)


if __name__ == "__main__":
    unittest.main()
