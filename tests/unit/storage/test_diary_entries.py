from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from packages.contracts import DiaryEntry
from packages.storage import RuntimeStorageRepository


class DiaryEntryStorageTest(unittest.TestCase):
    def test_delete_diary_entry_removes_one_personal_model_date(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repository = RuntimeStorageRepository(Path(tmpdir) / "elephant.sqlite3")
            repository.bootstrap()
            repository.upsert_diary_entry(
                DiaryEntry(
                    entry_id="diary:one",
                    personal_model_id="you",
                    entry_date="2026-05-14",
                    content="today",
                    generated_at=datetime.now(timezone.utc),
                )
            )
            repository.upsert_diary_entry(
                DiaryEntry(
                    entry_id="diary:other",
                    personal_model_id="other",
                    entry_date="2026-05-14",
                    content="other",
                    generated_at=datetime.now(timezone.utc),
                )
            )

            deleted = repository.delete_diary_entry(personal_model_id="you", entry_date="2026-05-14")

            self.assertTrue(deleted)
            self.assertIsNone(repository.load_diary_entry(personal_model_id="you", entry_date="2026-05-14"))
            self.assertIsNotNone(repository.load_diary_entry(personal_model_id="other", entry_date="2026-05-14"))
            self.assertFalse(repository.delete_diary_entry(personal_model_id="you", entry_date="2026-05-14"))


if __name__ == "__main__":
    unittest.main()
