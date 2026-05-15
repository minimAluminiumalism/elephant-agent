from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import json

from packages.state import (
    ELEPHANT_IDENTITY_FILENAME,
    EXTENSIONS_MANIFEST_FILENAME,
    ProfileLoader,
    ensure_elephant_identity_file,
)


class ProfileFilesTest(unittest.TestCase):
    def test_profile_loader_reads_extension_manifest_and_ignores_identity(self) -> None:
        """ProfileLoader owns only operator extension configuration.

        Identity fields (``display_name``, ``mode``, ``companion``) on disk
        are intentionally ignored — identity flows from the DB State row
        via ``load_runtime_profile``. The loader returns a stub identity
        so callers that still grab ``.state`` don't blow up.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            profile_dir = Path(tmpdir) / "profile"
            profile_dir.mkdir()
            (profile_dir / EXTENSIONS_MANIFEST_FILENAME).write_text(
                json.dumps(
                    {
                        "display_name": "Ignored",
                        "mode": "ignored",
                        "skill_overrides": {"arxiv": {"enabled": True}},
                    }
                ),
                encoding="utf-8",
            )

            loaded = ProfileLoader(profile_dir).load()

            # Identity comes from the DB, not this file — loader returns a stub.
            self.assertEqual(loaded.state.profile_id, "you")
            self.assertEqual(loaded.state.display_name, "You")
            # Extension manifest is passed through so skill / tool consumers see it.
            self.assertEqual(
                loaded.manifest.get("skill_overrides"),
                {"arxiv": {"enabled": True}},
            )

    def test_elephant_identity_file_is_seeded_under_elephant_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            herd_dir = Path(tmpdir) / "herd" / "owen"

            path = ensure_elephant_identity_file(
                herd_dir,
                "# Elephant Identity: Owen\n\nDefault Elephant Identity:\nOwen carries continuity.",
            )

            self.assertEqual(path, herd_dir / ELEPHANT_IDENTITY_FILENAME)
            self.assertTrue(path.exists())
            self.assertIn("Elephant Identity: Owen", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
