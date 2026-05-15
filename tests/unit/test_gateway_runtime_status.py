"""Unit tests for console gateway status helpers."""

from __future__ import annotations

import os

from apps.api.api_runtime_console_ops import (
    _gateway_runtime_is_running,
    _gateway_runtime_is_starting,
    _gateway_runtime_status,
    _pid_is_alive,
)


def _row(**content: object) -> dict[str, object]:
    return {"content": dict(content)}


def test_runtime_status_reports_stopped_when_content_missing() -> None:
    assert _gateway_runtime_status({}) == "stopped"


def test_runtime_status_reports_running_without_pid() -> None:
    assert _gateway_runtime_status(_row(status="running")) == "running"


def test_runtime_status_reports_starting_without_pid() -> None:
    assert _gateway_runtime_status(_row(status="starting")) == "starting"


def test_runtime_status_collapses_running_with_dead_pid_to_stopped() -> None:
    # pid 1 is always alive, pid 0 / negative is sentinel; use a very large pid that
    # is virtually guaranteed to be free.
    assert _gateway_runtime_status(_row(status="running", pid=2**31 - 2)) == "stopped"


def test_runtime_status_collapses_starting_with_dead_pid_to_stopped() -> None:
    assert _gateway_runtime_status(_row(status="starting", pid=2**31 - 2)) == "stopped"


def test_runtime_status_recognises_failed_record() -> None:
    assert _gateway_runtime_status(_row(status="failed")) == "failed"


def test_runtime_status_with_live_pid_is_running() -> None:
    assert _gateway_runtime_status(_row(status="running", pid=os.getpid())) == "running"


def test_runtime_is_running_helper_agrees() -> None:
    assert _gateway_runtime_is_running(_row(status="running")) is True
    assert _gateway_runtime_is_running(_row(status="starting")) is False


def test_runtime_is_starting_helper_agrees() -> None:
    assert _gateway_runtime_is_starting(_row(status="starting")) is True
    assert _gateway_runtime_is_starting(_row(status="running")) is False


def test_pid_is_alive_classifies() -> None:
    assert _pid_is_alive(None) is None
    assert _pid_is_alive(0) is False
    assert _pid_is_alive(-1) is False
    assert _pid_is_alive("not a number") is False
    assert _pid_is_alive(os.getpid()) is True
