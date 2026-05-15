"""Top-level operator dashboard launcher for local Elephant Agent checkouts."""

from __future__ import annotations

from argparse import SUPPRESS, ArgumentParser
from collections.abc import Mapping
from dataclasses import dataclass, replace
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from typing import Any
import urllib.error
import urllib.request
import webbrowser

import typer

from apps.cli.cli_main_support import CliCardSection, _print_cli_card
from apps.cli.typer_support import run_typer_app


REPO_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_APP_DIR = REPO_ROOT / "apps" / "dashboard"
DASHBOARD_PACKAGE_PATH = DASHBOARD_APP_DIR / "package.json"
DASHBOARD_NODE_MODULES = DASHBOARD_APP_DIR / "node_modules"
DASHBOARD_DIST_DIR = DASHBOARD_APP_DIR / "dist"
DASHBOARD_DIST_INDEX = DASHBOARD_DIST_DIR / "index.html"
API_PROBE_TIMEOUT_SECONDS = 0.35
API_CONSOLE_PROBE_TIMEOUT_SECONDS = 15.0
API_READY_WAIT_SECONDS = 20.0
API_READY_POLL_INTERVAL_SECONDS = 0.3
DASHBOARD_API_LOG_FILENAME = "dashboard-api.log"
DASHBOARD_UI_LOG_FILENAME = "dashboard-ui.log"


@dataclass(frozen=True, slots=True)
class DashboardLaunchPlan:
    state_dir: Path
    api_database: Path
    api_host: str
    api_port: int
    ui_host: str
    ui_port: int
    dashboard_assets_present: bool
    dashboard_static_assets_present: bool
    frontend_dependencies_present: bool
    npm_available: bool

    @property
    def api_url(self) -> str:
        return f"http://{self.api_host}:{self.api_port}"

    @property
    def ui_url(self) -> str:
        return f"http://{self.ui_host}:{self.ui_port}"


def _build_parser(
    *,
    default_state_dir: Path | None = None,
) -> ArgumentParser:
    parser = ArgumentParser(
        prog="elephant dashboard",
        description="Launch the local operator dashboard when frontend assets are present.",
    )
    parser.add_argument("--state-dir", default=default_state_dir, type=Path, help=SUPPRESS)
    parser.add_argument("--api-database", default=None, type=Path, help="Override the API database path.")
    parser.add_argument("--api-host", default="127.0.0.1")
    parser.add_argument("--api-port", default=8000, type=int)
    parser.add_argument("--host", dest="ui_host", default="127.0.0.1")
    parser.add_argument("--port", dest="ui_port", default=4174, type=int)
    parser.add_argument("--open", dest="open", action="store_true", default=True, help="Open the dashboard URL in the default browser.")
    parser.add_argument("--no-open", dest="open", action="store_false", help="Print the dashboard URL without opening a browser.")
    parser.add_argument(
        "--reuse-api",
        action="store_true",
        help="Attach to an existing healthy API on the requested API port instead of starting a fresh API.",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip the one-time dashboard frontend build check before launching.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the launch plan and readiness notes without starting any processes.",
    )
    return parser


def _build_plan(args) -> DashboardLaunchPlan:
    state_dir = Path(args.state_dir).expanduser()
    api_database = (
        Path(args.api_database).expanduser()
        if args.api_database is not None
        else state_dir / "elephant.sqlite3"
    )
    return DashboardLaunchPlan(
        state_dir=state_dir,
        api_database=api_database,
        api_host=str(args.api_host),
        api_port=int(args.api_port),
        ui_host=str(args.ui_host),
        ui_port=int(args.ui_port),
        dashboard_assets_present=DASHBOARD_PACKAGE_PATH.exists(),
        dashboard_static_assets_present=DASHBOARD_DIST_INDEX.exists(),
        frontend_dependencies_present=DASHBOARD_NODE_MODULES.exists(),
        npm_available=shutil.which("npm") is not None,
    )


def _print_plan(plan: DashboardLaunchPlan, *, ready_to_launch: bool) -> None:
    dependency_state = "ready" if plan.frontend_dependencies_present else "missing"
    asset_state = "present" if plan.dashboard_assets_present else "missing"
    static_asset_state = "present" if plan.dashboard_static_assets_present else "missing"
    npm_state = "ready" if plan.npm_available else "missing"
    sections = [
        CliCardSection(
            "Launch plan",
            (
                f"herd_dir · {plan.state_dir}",
                f"api_database · {plan.api_database}",
                f"api_url · {plan.api_url}",
                f"ui_url · {plan.ui_url}",
            ),
        ),
        CliCardSection(
            "Readiness",
            (
                f"dashboard_assets · {asset_state}",
                f"dashboard_static_assets · {static_asset_state}",
                f"npm · {npm_state}",
                f"frontend_dependencies · {dependency_state}",
                f"ready_to_launch · {'yes' if ready_to_launch else 'no'}",
            ),
        ),
    ]
    next_commands: tuple[str, ...] = ()
    if not plan.dashboard_assets_present and not plan.dashboard_static_assets_present:
        sections.append(
            CliCardSection(
                "Recovery",
                (
                    "This install does not include apps/dashboard frontend assets.",
                    "Use a local repo checkout and its launcher when you need the operator web surface.",
                ),
            )
        )
    elif plan.dashboard_assets_present and not plan.dashboard_static_assets_present and not plan.frontend_dependencies_present:
        sections.append(
            CliCardSection(
                "Recovery",
                (
                    "Install the dashboard frontend dependencies first:",
                    "npm --prefix apps/dashboard ci",
                ),
            )
        )
        next_commands = ("npm --prefix apps/dashboard ci", "elephant dashboard")
    _print_cli_card(
        "Elephant Agent dashboard",
        "Operator dashboard launch plan over the live CLI state database.",
        sections=tuple(sections),
        next_commands=next_commands,
    )


def _terminate_process(process: subprocess.Popen[str] | None) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def _dashboard_log_path(plan: DashboardLaunchPlan, *, kind: str) -> Path:
    filename = DASHBOARD_API_LOG_FILENAME if kind == "api" else DASHBOARD_UI_LOG_FILENAME
    return plan.state_dir / filename


def _open_dashboard_log(plan: DashboardLaunchPlan, *, kind: str):
    path = _dashboard_log_path(plan, kind=kind)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.open("a", encoding="utf-8", buffering=1)


def _api_health_payload(plan: DashboardLaunchPlan) -> Mapping[str, Any] | None:
    request = urllib.request.Request(
        f"{plan.api_url}/healthz",
        headers={"Accept": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=API_PROBE_TIMEOUT_SECONDS) as response:
            if response.status != 200:
                return None
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, TimeoutError, urllib.error.URLError, ValueError):
        return None
    return payload if isinstance(payload, Mapping) else None


def _api_health_ready(payload: Mapping[str, Any] | None) -> bool:
    return payload is not None and payload.get("service") == "elephant-api" and payload.get("status") == "ok"


def _api_dashboard_ready(plan: DashboardLaunchPlan) -> bool:
    request = urllib.request.Request(
        f"{plan.api_url}/v1/internal/dashboard/overview",
        headers={"Accept": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=API_CONSOLE_PROBE_TIMEOUT_SECONDS) as response:
            if response.status != 200:
                return False
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, TimeoutError, urllib.error.URLError, ValueError):
        return False
    return isinstance(payload, Mapping) and isinstance(payload.get("dashboard"), Mapping)


def _wait_for_api_overview(
    plan: DashboardLaunchPlan,
    api_process: subprocess.Popen[str] | None,
    *,
    timeout_seconds: float = API_READY_WAIT_SECONDS,
    poll_interval_seconds: float = API_READY_POLL_INTERVAL_SECONDS,
) -> bool:
    """Poll the overview endpoint until it returns 200 or the deadline passes.

    Opening the browser before this endpoint is ready causes the dashboard to
    render a transient "Dashboard inspection unavailable" banner while the API
    finishes bootstrapping its database / provider state. Waiting here removes
    that first-paint error for the common local-startup case while still
    falling through so the launcher never hangs indefinitely on a broken API.
    """
    deadline = time.monotonic() + max(timeout_seconds, 0.0)
    while time.monotonic() < deadline:
        if api_process is not None and api_process.poll() is not None:
            return False
        if _api_dashboard_ready(plan):
            return True
        time.sleep(poll_interval_seconds)
    return False


def _find_free_api_port(plan: DashboardLaunchPlan) -> int:
    for port in range(plan.api_port + 1, plan.api_port + 40):
        candidate = replace(plan, api_port=port)
        if not _api_port_occupied(candidate):
            return port
    raise RuntimeError(f"Could not find a free API port near {plan.api_port}.")


def _api_port_occupied(plan: DashboardLaunchPlan) -> bool:
    return _port_occupied(plan.api_host, plan.api_port)


def _find_free_ui_port(plan: DashboardLaunchPlan) -> int:
    for port in range(plan.ui_port + 1, plan.ui_port + 40):
        if not _port_occupied(plan.ui_host, port):
            return port
    raise RuntimeError(f"Could not find a free dashboard UI port near {plan.ui_port}.")


def _ui_port_occupied(plan: DashboardLaunchPlan) -> bool:
    return _port_occupied(plan.ui_host, plan.ui_port)


def _port_occupied(host: str, port: int) -> bool:
    try:
        with socket.create_connection(
            (host, port),
            timeout=API_PROBE_TIMEOUT_SECONDS,
        ):
            return True
    except OSError:
        return False


def _ui_command(plan: DashboardLaunchPlan) -> list[str]:
    command = ["npm", "--prefix", str(DASHBOARD_APP_DIR), "run", "dev"]
    command.extend(["--", "--host", plan.ui_host, "--port", str(plan.ui_port), "--strictPort"])
    return command


def _static_dashboard_command(plan: DashboardLaunchPlan) -> list[str]:
    return [
        sys.executable,
        "-m",
        "apps.dashboard_static_server",
        "--host",
        plan.ui_host,
        "--port",
        str(plan.ui_port),
        "--database",
        str(plan.api_database),
        "--static-dir",
        str(DASHBOARD_DIST_DIR),
    ]


def _frontend_build_command() -> list[str]:
    return ["npm", "--prefix", str(DASHBOARD_APP_DIR), "run", "build"]


def _run_frontend_build() -> int:
    build = subprocess.run(_frontend_build_command(), cwd=REPO_ROOT, text=True)
    return build.returncode


def _prepare_dashboard_ports(plan: DashboardLaunchPlan, *, reuse_api: bool) -> tuple[DashboardLaunchPlan, bool]:
    reuse_existing_api = False
    if reuse_api:
        api_health = _api_health_payload(plan)
        reuse_existing_api = _api_health_ready(api_health) and _api_dashboard_ready(plan)
    if not reuse_existing_api and _api_port_occupied(plan):
        plan = replace(plan, api_port=_find_free_api_port(plan))
    if _ui_port_occupied(plan):
        plan = replace(plan, ui_port=_find_free_ui_port(plan))
    return plan, reuse_existing_api


def _api_command(plan: DashboardLaunchPlan) -> list[str]:
    return [
        sys.executable,
        "-m",
        "apps.api",
        "--host",
        plan.api_host,
        "--port",
        str(plan.api_port),
        "--database",
        str(plan.api_database),
    ]


def _api_status_label(reuse_existing_api: bool) -> str:
    if reuse_existing_api:
        return "reusing existing healthy API"
    return "starting fresh local API"


def _build_status_label(build_frontend: bool) -> str:
    if build_frontend:
        return "building latest dashboard assets before launch"
    return "skipped by --skip-build"


def _use_source_dashboard(plan: DashboardLaunchPlan) -> bool:
    return plan.dashboard_assets_present and plan.frontend_dependencies_present and plan.npm_available


def _use_packaged_dashboard(plan: DashboardLaunchPlan) -> bool:
    return plan.dashboard_static_assets_present and not _use_source_dashboard(plan)


def _run_dashboard(
    plan: DashboardLaunchPlan,
    *,
    open_browser: bool,
    build_frontend: bool = True,
    reuse_api: bool = False,
) -> int:
    if not plan.dashboard_assets_present and not plan.dashboard_static_assets_present:
        _print_plan(plan, ready_to_launch=False)
        return 1
    if plan.dashboard_assets_present and not plan.dashboard_static_assets_present and not plan.npm_available:
        _print_cli_card(
            "Elephant Agent dashboard",
            "npm is required to launch the dashboard frontend.",
            sections=(CliCardSection("Recovery", ("Install Node.js and npm, then rerun `elephant dashboard`.",)),),
        )
        return 1
    if plan.dashboard_assets_present and not plan.dashboard_static_assets_present and not plan.frontend_dependencies_present:
        _print_plan(plan, ready_to_launch=False)
        return 1
    use_packaged_dashboard = _use_packaged_dashboard(plan)
    if build_frontend and _use_source_dashboard(plan):
        build_status = _run_frontend_build()
        if build_status != 0:
            return build_status or 1
        plan = replace(plan, dashboard_static_assets_present=DASHBOARD_DIST_INDEX.exists())
        use_packaged_dashboard = False
    plan, reuse_existing_api = _prepare_dashboard_ports(
        plan,
        reuse_api=False if use_packaged_dashboard else reuse_api,
    )
    api_command = _api_command(plan)
    api_log_path = _dashboard_log_path(plan, kind="api")
    ui_log_path = _dashboard_log_path(plan, kind="ui")

    ui_env = os.environ.copy()
    ui_env["VITE_ELEPHANT_API_BASE_URL"] = plan.api_url
    ui_env["ELEPHANT_DASHBOARD_API_AUTO_START"] = "0"

    _print_cli_card(
        "Elephant Agent dashboard",
        "Launching the operator dashboard against the live CLI state database.",
        sections=(
            CliCardSection(
                "Endpoints",
                (
                    f"api_url · {plan.api_url}",
                    f"ui_url · {plan.ui_url}",
                    f"api_database · {plan.api_database}",
                    f"api_status · {'same-process packaged API' if use_packaged_dashboard else _api_status_label(reuse_existing_api)}",
                    f"frontend_build · {'using packaged dashboard assets' if use_packaged_dashboard else _build_status_label(build_frontend)}",
                ),
            ),
            CliCardSection(
                "Logs",
                (
                    f"ui_log · {ui_log_path}",
                    f"api_log · {api_log_path}" if not (use_packaged_dashboard or reuse_existing_api) else "api_log · reused packaged or external API process",
                ),
            ),
        ),
    )

    api_process: subprocess.Popen[str] | None = None
    ui_process: subprocess.Popen[str] | None = None
    api_log_stream = None
    ui_log_stream = None
    try:
        if use_packaged_dashboard:
            ui_log_stream = _open_dashboard_log(plan, kind="ui")
            ui_process = subprocess.Popen(
                _static_dashboard_command(plan),
                cwd=REPO_ROOT,
                text=True,
                stdout=ui_log_stream,
                stderr=subprocess.STDOUT,
            )
        elif not reuse_existing_api:
            api_log_stream = _open_dashboard_log(plan, kind="api")
            api_process = subprocess.Popen(
                api_command,
                cwd=REPO_ROOT,
                text=True,
                stdout=api_log_stream,
                stderr=subprocess.STDOUT,
            )
            time.sleep(0.5)
            if api_process.poll() is not None:
                return api_process.returncode or 1
        if not use_packaged_dashboard:
            ui_log_stream = _open_dashboard_log(plan, kind="ui")
            ui_process = subprocess.Popen(
                _ui_command(plan),
                cwd=REPO_ROOT,
                env=ui_env,
                text=True,
                stdout=ui_log_stream,
                stderr=subprocess.STDOUT,
            )
        time.sleep(0.8)
        if ui_process.poll() is not None:
            return ui_process.returncode or 1
        # Wait for the Operator API to be serving dashboard overviews before
        # opening the browser. This prevents the first paint from rendering
        # the "Dashboard inspection unavailable" error during API bootstrap.
        if api_process is not None:
            _wait_for_api_overview(plan, api_process)
        opened = False
        if open_browser:
            opened = webbrowser.open(plan.ui_url)
        if not opened:
            print(f"Elephant Agent dashboard URL: {plan.ui_url}")
        while True:
            if api_process is not None and api_process.poll() is not None:
                return api_process.returncode or 1
            if ui_process.poll() is not None:
                return ui_process.returncode or 1
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopping Elephant Agent dashboard...")
        return 0
    finally:
        _terminate_process(ui_process)
        _terminate_process(api_process)
        if ui_log_stream is not None:
            ui_log_stream.close()
        if api_log_stream is not None:
            api_log_stream.close()


def build_typer_app(
    *,
    default_state_dir: Path | None = None,
) -> typer.Typer:
    app = typer.Typer(
        name="elephant dashboard",
        help="Launch the local operator dashboard when frontend assets are present.",
        no_args_is_help=False,
        rich_markup_mode="rich",
        add_completion=False,
    )

    @app.callback(invoke_without_command=True)
    def main_callback(
        state_dir: Path = typer.Option(default_state_dir, "--state-dir", hidden=True),
        api_database: Path | None = typer.Option(None, "--api-database", help="Override the API database path."),
        api_host: str = typer.Option("127.0.0.1", "--api-host", help="Host for the local API surface."),
        api_port: int = typer.Option(8000, "--api-port", help="Port for the local API surface."),
        ui_host: str = typer.Option("127.0.0.1", "--host", help="Host for the dashboard UI."),
        ui_port: int = typer.Option(4174, "--port", help="Port for the dashboard UI."),
        open_browser: bool = typer.Option(True, "--open/--no-open", help="Open the dashboard URL in the default browser."),
        reuse_api: bool = typer.Option(False, "--reuse-api", help="Attach to an existing healthy API when available on the requested port."),
        skip_build: bool = typer.Option(False, "--skip-build", help="Skip the one-time dashboard frontend build check before launch."),
        dry_run: bool = typer.Option(False, "--dry-run", help="Print the launch plan without starting any processes."),
    ) -> None:
        args = typer.main.get_command(app).make_context(
            "elephant dashboard",
            [],
            resilient_parsing=True,
        )
        del args
        class _Args:
            pass

        parsed = _Args()
        parsed.state_dir = state_dir
        parsed.api_database = api_database
        parsed.api_host = api_host
        parsed.api_port = api_port
        parsed.ui_host = ui_host
        parsed.ui_port = ui_port
        parsed.open = open_browser
        parsed.reuse_api = reuse_api
        parsed.skip_build = skip_build
        parsed.dry_run = dry_run
        plan = _build_plan(parsed)
        ready_to_launch = _use_source_dashboard(plan) or plan.dashboard_static_assets_present
        if dry_run:
            _print_plan(plan, ready_to_launch=ready_to_launch)
            raise typer.Exit(0)
        raise typer.Exit(
            _run_dashboard(
                plan,
                open_browser=bool(open_browser),
                build_frontend=not bool(skip_build),
                reuse_api=bool(reuse_api),
            )
        )

    return app


def command_main(
    argv: list[str] | None = None,
    *,
    default_state_dir: Path | None = None,
) -> int:
    return run_typer_app(
        build_typer_app(
            default_state_dir=default_state_dir,
        ),
        argv,
        prog_name="elephant dashboard",
    )


__all__ = ["command_main", "build_typer_app"]
