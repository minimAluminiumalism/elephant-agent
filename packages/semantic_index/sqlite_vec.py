"""Pinned sqlite-vec loading and health helpers for the reset semantic index."""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module, metadata
import sqlite3
from typing import Any, Mapping

SQLITE_VEC_PACKAGE = "sqlite-vec"
SQLITE_VEC_MODULE = "sqlite_vec"
SQLITE_VEC_VERSION = "0.1.9"


@dataclass(frozen=True, slots=True)
class SQLiteVecLoadState:
    status: str
    summary: str
    expected_version: str = SQLITE_VEC_VERSION
    installed_version: str = ""
    package_name: str = SQLITE_VEC_PACKAGE
    loaded: bool = False
    metadata: Mapping[str, str] = field(default_factory=dict)

    @property
    def ready(self) -> bool:
        return self.status == "ready" and self.loaded


def sqlite_vec_dependency_state() -> SQLiteVecLoadState:
    installed_version = _installed_version()
    if installed_version is None:
        return _degraded(
            "sqlite-vec is not installed; vector retrieval is disabled.",
            installed_version="",
            reason="missing-package",
        )
    if installed_version != SQLITE_VEC_VERSION:
        return _degraded(
            "sqlite-vec version does not match the reset pin; vector retrieval is disabled.",
            installed_version=installed_version,
            reason="version-mismatch",
        )
    return SQLiteVecLoadState(
        status="ready",
        summary="sqlite-vec dependency matches the reset pin.",
        installed_version=installed_version,
        loaded=False,
        metadata={"reason": "dependency-ready"},
    )


def sqlite_vec_runtime_state() -> SQLiteVecLoadState:
    with sqlite3.connect(":memory:") as connection:
        return load_sqlite_vec_extension(connection)


def load_sqlite_vec_extension(connection: Any) -> SQLiteVecLoadState:
    dependency = sqlite_vec_dependency_state()
    if dependency.status != "ready":
        return dependency
    try:
        sqlite_vec = import_module(SQLITE_VEC_MODULE)
        loader = getattr(sqlite_vec, "load", None)
        if callable(loader):
            _load_with_enabled_extensions(connection, loader)
        else:
            _load_with_extension_path(connection, sqlite_vec)
        runtime_version = _runtime_version(connection)
    except Exception as error:
        return _degraded(
            "sqlite-vec extension could not be loaded; vector retrieval is disabled.",
            installed_version=dependency.installed_version,
            reason=error.__class__.__name__,
            error=str(error),
        )
    return SQLiteVecLoadState(
        status="ready",
        summary="sqlite-vec extension loaded successfully.",
        installed_version=dependency.installed_version,
        loaded=True,
        metadata={"runtime_version": runtime_version},
    )


def _installed_version() -> str | None:
    try:
        return metadata.version(SQLITE_VEC_PACKAGE)
    except metadata.PackageNotFoundError:
        return None


def _load_with_extension_path(connection: Any, sqlite_vec: Any) -> None:
    loadable_path = getattr(sqlite_vec, "loadable_path", None)
    if not callable(loadable_path):
        raise RuntimeError("sqlite_vec exposes neither load() nor loadable_path()")
    enable = getattr(connection, "enable_load_extension", None)
    load = getattr(connection, "load_extension", None)
    if not callable(enable) or not callable(load):
        raise RuntimeError("sqlite connection cannot load sqlite-vec extensions")
    enable(True)
    try:
        load(str(loadable_path()))
    finally:
        enable(False)


def _load_with_enabled_extensions(connection: Any, loader: Any) -> None:
    enable = getattr(connection, "enable_load_extension", None)
    if not callable(enable):
        loader(connection)
        return
    enable(True)
    try:
        loader(connection)
    finally:
        enable(False)


def _runtime_version(connection: Any) -> str:
    row = connection.execute("SELECT vec_version()").fetchone()
    if row is None:
        return ""
    try:
        return str(row[0])
    except (IndexError, KeyError, TypeError):
        return ""


def _degraded(
    summary: str,
    *,
    installed_version: str,
    reason: str,
    error: str = "",
) -> SQLiteVecLoadState:
    metadata = {"reason": reason}
    if error:
        metadata["error"] = error
    return SQLiteVecLoadState(
        status="degraded",
        summary=summary,
        installed_version=installed_version,
        loaded=False,
        metadata=metadata,
    )
