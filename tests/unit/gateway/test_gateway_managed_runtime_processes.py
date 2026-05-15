from __future__ import annotations

from pathlib import Path

from apps.gateway.gateway_main_runtime import _gateway_service_process_matches


def test_gateway_service_process_matches_launcher_for_same_state_dir() -> None:
    command = (
        "/usr/bin/python3 -m apps.launcher gateway weixin start 82524303bd7e@im.bot "
        "--transport ilink --state-dir /Users/example/.elephant/herd "
        "--cli-state-dir /Users/example/.elephant/herd"
    )

    assert _gateway_service_process_matches(
        command,
        service_key="weixin",
        state_dir=Path("/Users/example/.elephant/herd"),
    )


def test_gateway_service_process_match_rejects_other_service_or_state_dir() -> None:
    command = (
        "/usr/bin/python3 -m apps.launcher gateway weixin start "
        "--transport ilink --state-dir /Users/example/.elephant/herd"
    )

    assert not _gateway_service_process_matches(
        command,
        service_key="feishu",
        state_dir=Path("/Users/example/.elephant/herd"),
    )
    assert not _gateway_service_process_matches(
        command,
        service_key="weixin",
        state_dir=Path("/Users/other/.elephant/herd"),
    )


def test_gateway_service_process_match_requires_managed_start_shape() -> None:
    command = "/usr/bin/python3 -m apps.launcher gateway weixin status --state-dir /Users/example/.elephant/herd"

    assert not _gateway_service_process_matches(
        command,
        service_key="weixin",
        state_dir=Path("/Users/example/.elephant/herd"),
    )
