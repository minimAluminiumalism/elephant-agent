from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3
import tarfile
import tempfile
import unittest

from apps.upgrade_command import (
    ManagedRuntimeSnapshot,
    create_pre_upgrade_backup,
    discover_running_runtimes,
    pip_upgrade_command,
    restart_argv_for_runtime,
)


class UpgradeCommandTest(unittest.TestCase):
    def test_pip_upgrade_command_resolves_channel_and_explicit_spec(self) -> None:
        dev = pip_upgrade_command(channel="dev", pip_spec=None)
        self.assertEqual(dev[-2:], ["--pre", "elephant"])

        stable = pip_upgrade_command(channel="stable", pip_spec=None)
        self.assertEqual(stable[-1], "elephant")
        self.assertNotIn("--pre", stable)

        explicit = pip_upgrade_command(channel="dev", pip_spec="/tmp/elephant.whl")
        self.assertEqual(explicit[-1], "/tmp/elephant.whl")
        self.assertNotIn("elephant", explicit[-1:])

    def test_discover_running_runtimes_reads_runtime_records(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            gateway_dir = root / "gateway"
            state_dir = root / "herd"
            gateway_dir.mkdir()
            pid_path = gateway_dir / "feishu-long-connection.pid"
            record_path = gateway_dir / "feishu-long-connection.runtime.json"
            pid_path.write_text(f"{os.getpid()}\n", encoding="utf-8")
            record_path.write_text(
                json.dumps(
                    {
                        "service_key": "feishu",
                        "target": "long-connection",
                        "status": "running",
                        "pid": os.getpid(),
                        "pid_path": str(pid_path),
                        "state_dir": str(gateway_dir),
                        "cli_state_dir": str(state_dir),
                        "account_id": "ops-feishu",
                    }
                ),
                encoding="utf-8",
            )

            runtimes = discover_running_runtimes(
                gateway_state_dir=gateway_dir,
                cli_state_dir=state_dir,
            )

        self.assertEqual(len(runtimes), 1)
        runtime = runtimes[0]
        self.assertEqual(runtime.service_key, "feishu")
        self.assertEqual(runtime.target, "long-connection")
        self.assertEqual(runtime.account_id, "ops-feishu")

    def test_restart_argv_for_gateway_and_cron(self) -> None:
        gateway = ManagedRuntimeSnapshot(
            service_key="discord",
            target="gateway",
            pid=123,
            pid_path=Path("gateway/discord-gateway.pid"),
            record_path=Path("gateway/discord-gateway.runtime.json"),
            state_dir=Path("gateway"),
            cli_state_dir=Path("herd"),
            account_id="ops-discord",
        )
        self.assertEqual(
            restart_argv_for_runtime(gateway),
            [
                "gateway",
                "discord",
                "start",
                "ops-discord",
                "--transport",
                "gateway",
                "--detach",
                "--state-dir",
                "gateway",
                "--cli-state-dir",
                "herd",
            ],
        )

        cron = ManagedRuntimeSnapshot(
            service_key="cron",
            target="scheduler",
            pid=456,
            pid_path=Path("gateway/cron-scheduler.pid"),
            record_path=Path("gateway/cron-scheduler.runtime.json"),
            state_dir=Path("gateway"),
            cli_state_dir=Path("herd"),
            interval_seconds=30.0,
        )
        self.assertEqual(
            restart_argv_for_runtime(cron),
            [
                "cron",
                "start",
                "--detach",
                "--target",
                "scheduler",
                "--state-dir",
                "gateway",
                "--cli-state-dir",
                "herd",
                "--interval-seconds",
                "30",
            ],
        )

    def test_pre_upgrade_backup_excludes_venv_and_copies_sqlite_safely(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw) / "elephant-home"
            db_path = home / "herd" / "state" / "elephant.sqlite3"
            db_path.parent.mkdir(parents=True)
            with sqlite3.connect(db_path) as connection:
                connection.execute("CREATE TABLE facts(id TEXT PRIMARY KEY, value TEXT)")
                connection.execute("INSERT INTO facts(id, value) VALUES('one', 'stored')")
            (home / "venv").mkdir()
            (home / "venv" / "marker.txt").write_text("skip", encoding="utf-8")
            (home / "config.yaml").write_text("runtime: {}\n", encoding="utf-8")

            archive = create_pre_upgrade_backup(home)
            extract_dir = Path(raw) / "extract"
            extract_dir.mkdir()
            with tarfile.open(archive, "r:gz") as tar:
                tar.extractall(extract_dir)

            restored_db = extract_dir / "elephant-home" / "herd" / "state" / "elephant.sqlite3"
            with sqlite3.connect(restored_db) as connection:
                row = connection.execute("SELECT value FROM facts WHERE id = 'one'").fetchone()

            self.assertEqual(row[0], "stored")
            self.assertTrue((extract_dir / "elephant-home" / "config.yaml").exists())
            self.assertFalse((extract_dir / "elephant-home" / "venv").exists())


if __name__ == "__main__":
    unittest.main()
