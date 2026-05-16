"""Shared construction of the durable `SemanticIndexService` + backend.

Both the producer side (episode close hook, personal-model fact indexer,
skill index writer) and the consumer side (recall, skill re-rank)
must read and write the SAME SQLite-backed vector index. If the producer
uses a tempdir path while the consumer uses the runtime state dir, writes
are invisible to reads — that is the exact "indexer wrote it, recall can't
find it" bug we are closing.

This factory derives a single, stable index path from the runtime's state
directory and returns `(service, backend)`. Callers pass both, or just
the service if they only need write access.

Layout:
    <state_dir>/semantic-index/sqlite-vec.sqlite3
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from packages.semantic_index import (
    HybridSemanticSearcher,
    SemanticIndexService,
    SQLiteVecSemanticIndex,
)


__all__ = [
    "SemanticIndexBundle",
    "build_semantic_index_bundle",
    "default_semantic_index_path",
]


def default_semantic_index_path(*, state_dir: Path) -> Path:
    """Return the canonical durable semantic-index file path."""
    base = Path(state_dir) / "semantic-index"
    base.mkdir(parents=True, exist_ok=True)
    return base / "sqlite-vec.sqlite3"


@dataclass(frozen=True, slots=True)
class SemanticIndexBundle:
    """Bundle of the durable service, backend, and searcher.

    Keep a single instance per runtime process so producer and consumer
    observe the same physical file, and share the searcher instance.
    """

    service: SemanticIndexService
    backend: SQLiteVecSemanticIndex
    searcher: HybridSemanticSearcher
    database_path: Path


def build_semantic_index_bundle(
    *,
    repository: Any,
    state_dir: Path,
    database_path: Path | None = None,
) -> SemanticIndexBundle:
    """Build a durable `SemanticIndexService` + backend + searcher.

    `repository` must implement both `SemanticIndexRepository` and
    `SemanticSearchRepository` protocols (`upsert_semantic_index_entry`,
    `list_semantic_index_entries`, `load_record`, ...). The runtime's
    `RuntimeStorageRepository` satisfies both.
    """
    path = Path(database_path) if database_path is not None else default_semantic_index_path(state_dir=state_dir)
    backend = SQLiteVecSemanticIndex(path)
    service = SemanticIndexService(repository=repository, backend=backend)
    searcher = HybridSemanticSearcher(repository=repository, backend=backend)
    return SemanticIndexBundle(
        service=service,
        backend=backend,
        searcher=searcher,
        database_path=path,
    )
