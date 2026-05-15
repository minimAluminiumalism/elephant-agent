from __future__ import annotations

from pathlib import Path
import unittest
from unittest import mock

from apps import dashboard_command


def _plan() -> dashboard_command.DashboardLaunchPlan:
    return dashboard_command.DashboardLaunchPlan(
        state_dir=Path("/tmp/elephant-state"),
        profile_dir=Path("/tmp/elephant-profile"),
        api_database=Path("/tmp/elephant-state/elephant.sqlite3"),
        api_host="127.0.0.1",
        api_port=8000,
        ui_host="127.0.0.1",
        ui_port=4174,
        dashboard_assets_present=True,
        dashboard_static_assets_present=True,
        frontend_dependencies_present=True,
        npm_available=True,
    )


def _packaged_plan() -> dashboard_command.DashboardLaunchPlan:
    return dashboard_command.DashboardLaunchPlan(
        state_dir=Path("/tmp/elephant-state"),
        profile_dir=Path("/tmp/elephant-profile"),
        api_database=Path("/tmp/elephant-state/elephant.sqlite3"),
        api_host="127.0.0.1",
        api_port=8000,
        ui_host="127.0.0.1",
        ui_port=4174,
        dashboard_assets_present=False,
        dashboard_static_assets_present=True,
        frontend_dependencies_present=False,
        npm_available=False,
    )


class DashboardCommandTest(unittest.TestCase):
    def test_reuses_existing_healthy_api_when_requested(self) -> None:
        ui_process = mock.Mock()
        ui_process.poll.side_effect = [None, None, None]
        ui_process.returncode = 0

        with (
            mock.patch.object(
                dashboard_command,
                "_api_health_payload",
                return_value={"service": "elephant-api", "status": "ok"},
            ),
            mock.patch.object(dashboard_command, "_api_dashboard_ready", return_value=True),
            mock.patch.object(dashboard_command, "_api_port_occupied", return_value=True),
            mock.patch.object(dashboard_command, "_ui_port_occupied", return_value=False),
            mock.patch.object(dashboard_command.subprocess, "Popen", return_value=ui_process) as popen,
            mock.patch.object(dashboard_command.time, "sleep", side_effect=[None, KeyboardInterrupt]),
            mock.patch.object(dashboard_command, "_print_cli_card"),
        ):
            result = dashboard_command._run_dashboard(
                _plan(),
                open_browser=False,
                build_frontend=False,
                reuse_api=True,
            )

        self.assertEqual(result, 0)
        self.assertEqual(popen.call_count, 1)
        self.assertEqual(popen.call_args.args[0][0], "npm")
        self.assertEqual(popen.call_args.kwargs["env"]["ELEPHANT_DASHBOARD_API_AUTO_START"], "0")

    def test_default_starts_fresh_api_when_requested_port_has_healthy_api(self) -> None:
        api_process = mock.Mock()
        api_process.poll.return_value = None
        api_process.returncode = 0
        ui_process = mock.Mock()
        ui_process.poll.return_value = None
        ui_process.returncode = 0

        with (
            mock.patch.object(
                dashboard_command,
                "_api_health_payload",
                return_value={"service": "elephant-api", "status": "ok"},
            ),
            mock.patch.object(dashboard_command, "_api_dashboard_ready", return_value=True),
            mock.patch.object(dashboard_command, "_api_port_occupied", side_effect=[True, False]),
            mock.patch.object(dashboard_command, "_ui_port_occupied", return_value=False),
            mock.patch.object(dashboard_command.subprocess, "Popen", side_effect=[api_process, ui_process]) as popen,
            mock.patch.object(dashboard_command.time, "sleep", side_effect=[None, None, KeyboardInterrupt]),
            mock.patch.object(dashboard_command, "_print_cli_card"),
        ):
            result = dashboard_command._run_dashboard(
                _plan(),
                open_browser=False,
                build_frontend=False,
            )

        self.assertEqual(result, 0)
        self.assertEqual(popen.call_count, 2)
        self.assertEqual(popen.call_args_list[0].args[0][6], "8001")
        self.assertEqual(popen.call_args_list[1].kwargs["env"]["VITE_ELEPHANT_API_BASE_URL"], "http://127.0.0.1:8001")

    def test_unhealthy_occupied_api_port_uses_next_free_port(self) -> None:
        api_process = mock.Mock()
        api_process.poll.return_value = None
        api_process.returncode = 0
        ui_process = mock.Mock()
        ui_process.poll.return_value = None
        ui_process.returncode = 0

        with (
            mock.patch.object(dashboard_command, "_api_health_payload", return_value=None),
            mock.patch.object(dashboard_command, "_api_port_occupied", side_effect=[True, False]),
            mock.patch.object(dashboard_command, "_ui_port_occupied", return_value=False),
            mock.patch.object(dashboard_command.subprocess, "Popen", side_effect=[api_process, ui_process]) as popen,
            mock.patch.object(dashboard_command.time, "sleep", side_effect=[None, None, KeyboardInterrupt]),
            mock.patch.object(dashboard_command, "_print_cli_card"),
        ):
            result = dashboard_command._run_dashboard(_plan(), open_browser=False, build_frontend=False)

        self.assertEqual(result, 0)
        self.assertEqual(popen.call_count, 2)
        self.assertEqual(popen.call_args_list[0].args[0][6], "8001")
        self.assertEqual(popen.call_args_list[1].kwargs["env"]["VITE_ELEPHANT_API_BASE_URL"], "http://127.0.0.1:8001")

    def test_launch_redirects_api_and_ui_output_to_state_log_files(self) -> None:
        api_process = mock.Mock()
        api_process.poll.return_value = None
        api_process.returncode = 0
        ui_process = mock.Mock()
        ui_process.poll.return_value = None
        ui_process.returncode = 0
        api_log = mock.Mock()
        ui_log = mock.Mock()

        with (
            mock.patch.object(dashboard_command, "_api_port_occupied", return_value=False),
            mock.patch.object(dashboard_command, "_ui_port_occupied", return_value=False),
            mock.patch.object(dashboard_command, "_open_dashboard_log", side_effect=[api_log, ui_log]) as open_log,
            mock.patch.object(dashboard_command.subprocess, "Popen", side_effect=[api_process, ui_process]) as popen,
            mock.patch.object(dashboard_command.time, "sleep", side_effect=[None, None, KeyboardInterrupt]),
            mock.patch.object(dashboard_command, "_print_cli_card"),
        ):
            result = dashboard_command._run_dashboard(_plan(), open_browser=False, build_frontend=False)

        self.assertEqual(result, 0)
        self.assertEqual(open_log.call_args_list[0].kwargs["kind"], "api")
        self.assertEqual(open_log.call_args_list[1].kwargs["kind"], "ui")
        self.assertIs(popen.call_args_list[0].kwargs["stdout"], api_log)
        self.assertIs(popen.call_args_list[1].kwargs["stdout"], ui_log)
        self.assertIs(popen.call_args_list[0].kwargs["stderr"], dashboard_command.subprocess.STDOUT)
        self.assertIs(popen.call_args_list[1].kwargs["stderr"], dashboard_command.subprocess.STDOUT)
        api_log.close.assert_called_once_with()
        ui_log.close.assert_called_once_with()

    def test_occupied_ui_port_uses_next_free_port(self) -> None:
        api_process = mock.Mock()
        api_process.poll.return_value = None
        api_process.returncode = 0
        ui_process = mock.Mock()
        ui_process.poll.return_value = None
        ui_process.returncode = 0

        with (
            mock.patch.object(dashboard_command, "_api_port_occupied", return_value=False),
            mock.patch.object(dashboard_command, "_ui_port_occupied", return_value=True),
            mock.patch.object(dashboard_command, "_port_occupied", side_effect=lambda _host, port: port == 4174),
            mock.patch.object(dashboard_command.subprocess, "Popen", side_effect=[api_process, ui_process]) as popen,
            mock.patch.object(dashboard_command.time, "sleep", side_effect=[None, None, KeyboardInterrupt]),
            mock.patch.object(dashboard_command, "_print_cli_card"),
        ):
            result = dashboard_command._run_dashboard(_plan(), open_browser=False, build_frontend=False)

        self.assertEqual(result, 0)
        self.assertEqual(popen.call_args_list[1].args[0][-1], "--strictPort")
        self.assertIn("4175", popen.call_args_list[1].args[0])

    def test_builds_frontend_before_launch(self) -> None:
        api_process = mock.Mock()
        api_process.poll.return_value = None
        api_process.returncode = 0
        ui_process = mock.Mock()
        ui_process.poll.return_value = None
        ui_process.returncode = 0

        with (
            mock.patch.object(dashboard_command, "_run_frontend_build", return_value=0) as build,
            mock.patch.object(dashboard_command, "_api_port_occupied", return_value=False),
            mock.patch.object(dashboard_command, "_ui_port_occupied", return_value=False),
            mock.patch.object(dashboard_command.subprocess, "Popen", side_effect=[api_process, ui_process]),
            mock.patch.object(dashboard_command.time, "sleep", side_effect=[None, None, KeyboardInterrupt]),
            mock.patch.object(dashboard_command, "_print_cli_card"),
        ):
            result = dashboard_command._run_dashboard(_plan(), open_browser=False)

        self.assertEqual(result, 0)
        build.assert_called_once_with()

    def test_packaged_dashboard_uses_static_server_without_npm(self) -> None:
        ui_process = mock.Mock()
        ui_process.poll.side_effect = [None, None, None]
        ui_process.returncode = 0

        with (
            mock.patch.object(dashboard_command, "_api_port_occupied", return_value=False),
            mock.patch.object(dashboard_command, "_ui_port_occupied", return_value=False),
            mock.patch.object(dashboard_command.subprocess, "Popen", return_value=ui_process) as popen,
            mock.patch.object(dashboard_command.time, "sleep", side_effect=[None, KeyboardInterrupt]),
            mock.patch.object(dashboard_command, "_print_cli_card"),
        ):
            result = dashboard_command._run_dashboard(_packaged_plan(), open_browser=False)

        self.assertEqual(result, 0)
        self.assertEqual(popen.call_count, 1)
        command = popen.call_args.args[0]
        self.assertEqual(command[:3], [dashboard_command.sys.executable, "-m", "apps.dashboard_static_server"])
        self.assertIn("--static-dir", command)

    def test_browser_opens_by_default(self) -> None:
        ui_process = mock.Mock()
        ui_process.poll.side_effect = [None, None, None]
        ui_process.returncode = 0
        with (
            mock.patch.object(dashboard_command, "_api_health_payload", return_value={"service": "elephant-api", "status": "ok"}),
            mock.patch.object(dashboard_command, "_api_dashboard_ready", return_value=True),
            mock.patch.object(dashboard_command, "_ui_port_occupied", return_value=False),
            mock.patch.object(dashboard_command.subprocess, "Popen", return_value=ui_process),
            mock.patch.object(dashboard_command.time, "sleep", side_effect=[None, KeyboardInterrupt]),
            mock.patch.object(dashboard_command.webbrowser, "open", return_value=True) as open_browser,
            mock.patch.object(dashboard_command, "_print_cli_card"),
        ):
            result = dashboard_command._run_dashboard(
                _plan(),
                open_browser=True,
                build_frontend=False,
                reuse_api=True,
            )

        self.assertEqual(result, 0)
        open_browser.assert_called_once_with("http://127.0.0.1:4174")


if __name__ == "__main__":
    unittest.main()
