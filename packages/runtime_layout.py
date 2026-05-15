from __future__ import annotations

from collections.abc import Mapping
import os
from pathlib import Path
from urllib.parse import quote


EnvMapping = Mapping[str, str]
_DEFAULT_ELEPHANT_HOME = Path.home() / ".elephant"


def _environ(environ: EnvMapping | None = None) -> EnvMapping:
    return environ if environ is not None else os.environ


def default_install_root(*, environ: EnvMapping | None = None) -> Path:
    env = _environ(environ)
    override = env.get("ELEPHANT_HOME")
    if override:
        return Path(override).expanduser()
    return _DEFAULT_ELEPHANT_HOME


def default_cli_state_dir(*, environ: EnvMapping | None = None) -> Path:
    env = _environ(environ)
    override = env.get("ELEPHANT_HERD_DIR")
    if override:
        return Path(override).expanduser()
    return default_install_root(environ=env) / "herd"


def default_gateway_state_dir(*, environ: EnvMapping | None = None) -> Path:
    """Gateway shares the CLI's state dir: one DB per install."""
    return default_cli_state_dir(environ=environ)


def default_skills_dir(*, environ: EnvMapping | None = None, install_root: Path | None = None) -> Path:
    env = _environ(environ)
    override = env.get("ELEPHANT_SKILLS_DIR")
    if override:
        return Path(override).expanduser()
    root = install_root.expanduser() if install_root is not None else default_install_root(environ=env)
    return root / "skills"


def default_builtin_skills_dir(
    *,
    environ: EnvMapping | None = None,
    install_root: Path | None = None,
) -> Path:
    env = _environ(environ)
    override = env.get("ELEPHANT_BUILTIN_SKILLS_DIR")
    if override:
        return Path(override).expanduser()
    return default_skills_dir(environ=env, install_root=install_root) / "builtin"


def default_installed_skills_dir(
    *,
    environ: EnvMapping | None = None,
    install_root: Path | None = None,
) -> Path:
    env = _environ(environ)
    override = env.get("ELEPHANT_INSTALLED_SKILLS_DIR") or env.get("ELEPHANT_SHARED_SKILLS_DIR")
    if override:
        return Path(override).expanduser()
    return default_skills_dir(environ=env, install_root=install_root) / "installed"


def default_authored_skills_dir(
    *,
    environ: EnvMapping | None = None,
    install_root: Path | None = None,
) -> Path:
    env = _environ(environ)
    override = env.get("ELEPHANT_AUTHORED_SKILLS_DIR")
    if override:
        return Path(override).expanduser()
    return default_skills_dir(environ=env, install_root=install_root) / "authored"


def default_skill_search_cache_dir(
    *,
    environ: EnvMapping | None = None,
    install_root: Path | None = None,
) -> Path:
    env = _environ(environ)
    override = env.get("ELEPHANT_SKILL_SEARCH_CACHE_DIR")
    if override:
        return Path(override).expanduser()
    return default_skills_dir(environ=env, install_root=install_root) / ".cache" / "search"


def default_cron_dir(*, environ: EnvMapping | None = None, install_root: Path | None = None) -> Path:
    env = _environ(environ)
    override = env.get("ELEPHANT_CRON_DIR")
    if override:
        return Path(override).expanduser()
    root = install_root.expanduser() if install_root is not None else default_install_root(environ=env)
    return root / "cron"


def default_workspaces_dir(*, environ: EnvMapping | None = None, install_root: Path | None = None) -> Path:
    env = _environ(environ)
    override = env.get("ELEPHANT_WORKSPACES_DIR") or env.get("ELEPHANT_ELEPHANT_FILES_DIR")
    if override:
        return Path(override).expanduser()
    root = install_root.expanduser() if install_root is not None else default_install_root(environ=env)
    return root / "workspaces"


def default_pairing_dir(*, environ: EnvMapping | None = None, install_root: Path | None = None) -> Path:
    env = _environ(environ)
    override = env.get("ELEPHANT_PAIRING_DIR")
    if override:
        return Path(override).expanduser()
    root = install_root.expanduser() if install_root is not None else default_install_root(environ=env)
    return root / "pairing"


def infer_install_root_from_state_dir(
    state_dir: Path,
    *,
    environ: EnvMapping | None = None,
) -> Path:
    env = _environ(environ)
    override = env.get("ELEPHANT_HOME")
    if override:
        return Path(override).expanduser()
    resolved_state = state_dir.expanduser().resolve()
    if resolved_state.name in {"herd", "state"} and resolved_state.parent != resolved_state:
        return resolved_state.parent
    return resolved_state


def elephant_file_path(
    elephant_id: str,
    *,
    environ: EnvMapping | None = None,
    install_root: Path | None = None,
) -> Path:
    key = quote(elephant_id.strip(), safe="")
    if not key:
        raise ValueError("elephant id is required")
    return default_workspaces_dir(environ=environ, install_root=install_root) / key


__all__ = [
    "default_authored_skills_dir",
    "default_builtin_skills_dir",
    "default_cli_state_dir",
    "default_cron_dir",
    "default_gateway_state_dir",
    "default_install_root",
    "default_installed_skills_dir",
    "default_pairing_dir",
    "default_skill_search_cache_dir",
    "default_skills_dir",
    "default_workspaces_dir",
    "infer_install_root_from_state_dir",
    "elephant_file_path",
]
