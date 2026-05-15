"""Filesystem helpers for elephant-local identity files.

`ELEPHANT.md` is the authored (human-editable) copy of an elephant's self-introduction.
It is no longer the runtime source of truth — the kernel reads
`State.elephant_identity_text` from the DB at turn time. The file exists so
operators and skill authors can version-control and edit the identity in a
familiar plain-text format.

The write path must mirror changes into the State row; see
:func:`apps.cli.runtime_profile.save_elephant_identity` for the canonical side.
"""

from __future__ import annotations

from pathlib import Path

ELEPHANT_IDENTITY_FILENAME = "ELEPHANT.md"


def elephant_identity_file_path(elephant_root: Path) -> Path:
    return elephant_root / ELEPHANT_IDENTITY_FILENAME


def read_elephant_identity_file(elephant_root: Path) -> str | None:
    path = elephant_identity_file_path(elephant_root)
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8").strip()
    return text or None


def write_elephant_identity_file(elephant_root: Path, content: str) -> Path:
    text = str(content or "").strip()
    if not text:
        raise ValueError("elephant identity content must not be empty")
    path = elephant_identity_file_path(elephant_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")
    return path


def ensure_elephant_identity_file(elephant_root: Path, content: str) -> Path:
    path = elephant_identity_file_path(elephant_root)
    if not path.exists():
        return write_elephant_identity_file(elephant_root, content)
    return path
