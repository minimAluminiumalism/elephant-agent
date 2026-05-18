from __future__ import annotations

import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
from types import TracebackType
from typing import Self


ROOT = Path(__file__).resolve().parents[3]


def stop_recorded_background_processes(state_dir: Path, *, timeout: float = 5.0) -> None:
    """Best-effort cleanup for background workers started by installed CLI tests."""
    pid_candidates: list[int] = []
    for record_path, keys in (
        (state_dir / "learning-worker.runtime.json", ("pid",)),
        (state_dir / "embedding-bootstrap.json", ("background_pid",)),
    ):
        try:
            payload = json.loads(record_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        for key in keys:
            try:
                pid = int(payload.get(key) or 0)
            except (TypeError, ValueError):
                continue
            if pid > 0:
                pid_candidates.append(pid)

    for pid in pid_candidates:
        _terminate_pid(pid, timeout=timeout)


def _terminate_pid(pid: int, *, timeout: float) -> None:
    try:
        os.kill(pid, 0)
    except OSError:
        return
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        return
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except OSError:
            return
        time.sleep(0.1)
    try:
        os.kill(pid, signal.SIGKILL)
    except OSError:
        return


class InstalledElephantEnvironment:
    """Fresh editable install of the public ``elephant`` command."""

    def __init__(self) -> None:
        self._tempdir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self._tempdir.name)
        self.venv_dir = self.root / "venv"
        self.home_dir = self.root / "elephant-home"
        self.state_dir = self.home_dir / "herd"

    def __enter__(self) -> Self:
        self.install_editable()
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc: BaseException | None,
        _traceback: TracebackType | None,
    ) -> None:
        self.cleanup()

    @property
    def python_bin(self) -> Path:
        if os.name == "nt":
            return self.venv_dir / "Scripts" / "python.exe"
        return self.venv_dir / "bin" / "python"

    @property
    def elephant_bin(self) -> Path:
        if os.name == "nt":
            return self.venv_dir / "Scripts" / "elephant.exe"
        return self.venv_dir / "bin" / "elephant"

    def env(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        env = os.environ.copy()
        env["ELEPHANT_HOME"] = str(self.home_dir)
        env.setdefault("TERM", "xterm-256color")
        env.setdefault("COLUMNS", "120")
        env.setdefault("LINES", "40")
        if extra:
            env.update(extra)
        return env

    def install_editable(self) -> None:
        subprocess.run(
            [sys.executable, "-m", "venv", str(self.venv_dir)],
            cwd=ROOT,
            check=True,
            text=True,
        )
        subprocess.run(
            [str(self.python_bin), "-m", "pip", "install", "-e", "."],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
            timeout=600,
        )

    def run(
        self,
        *args: str,
        env: dict[str, str] | None = None,
        timeout: int = 120,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [str(self.elephant_bin), *args],
            cwd=self.root,
            env=env or self.env(),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        if check and result.returncode != 0:
            raise AssertionError(
                "command failed: "
                + " ".join([str(self.elephant_bin), *args])
                + f"\nexit={result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )
        return result

    def stop_daemon(self, *, timeout: int = 30) -> subprocess.CompletedProcess[str]:
        return self.run(
            "daemon",
            "stop",
            "--state-dir",
            str(self.state_dir),
            "--timeout",
            "5",
            "--force",
            timeout=timeout,
            check=False,
        )

    def cleanup(self) -> None:
        try:
            self.stop_daemon(timeout=15)
            stop_recorded_background_processes(self.state_dir)
        finally:
            self._tempdir.cleanup()
