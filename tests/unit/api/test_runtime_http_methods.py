from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
import unittest

from apps.api.api_runtime_http_methods import _dispatch_internal, _dispatch_operator


def _diary_job() -> SimpleNamespace:
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        job_id="cron:diary",
        name="Daily diary",
        schedule_text="0 2 * * *",
        schedule_kind="cron",
        action_kind="learning",
        status="scheduled",
        profile_id=None,
        elephant_id=None,
        payload={"trigger": "diary"},
        created_at=now,
        updated_at=now,
        next_run_at=now,
        last_run_at=None,
        run_count=0,
        last_summary="",
    )


def _dream_job() -> SimpleNamespace:
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        job_id="cron:dream",
        name="Nightly dream",
        schedule_text="0 1 * * *",
        schedule_kind="cron",
        action_kind="learning",
        status="scheduled",
        profile_id=None,
        elephant_id=None,
        payload={"trigger": "dream"},
        created_at=now,
        updated_at=now,
        next_run_at=now,
        last_run_at=None,
        run_count=0,
        last_summary="",
    )


class _CronRuntimeStub:
    def __init__(self, job: SimpleNamespace | None = None) -> None:
        self.job = job
        self.removed_job_id: str | None = None

    def inspect_job(self, job_id: str) -> SimpleNamespace:
        if self.job is None or self.job.job_id != job_id:
            raise KeyError(job_id)
        return self.job

    def remove_job(self, job_id: str) -> SimpleNamespace:
        self.removed_job_id = job_id
        if self.job is None:
            raise KeyError(job_id)
        return self.job


class OperatorCronDispatchTest(unittest.TestCase):
    def test_rejects_delete_for_proactive_system_job(self) -> None:
        app = SimpleNamespace()

        response = _dispatch_operator(app, "DELETE", ("cron", "system:proactive-ask"), None)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.payload["error"], "system_cron_jobs_cannot_be_deleted")

    def test_allows_delete_for_diary_learning_job(self) -> None:
        cron_runtime = _CronRuntimeStub(job=_diary_job())
        app = SimpleNamespace(cron_runtime=cron_runtime)

        response = _dispatch_operator(app, "DELETE", ("cron", "cron:diary"), None)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.payload["cron"]["status"], "removed")
        self.assertEqual(cron_runtime.removed_job_id, "cron:diary")

    def test_rejects_delete_for_nightly_dream_system_job(self) -> None:
        cron_runtime = _CronRuntimeStub(job=_dream_job())
        app = SimpleNamespace(cron_runtime=cron_runtime)

        response = _dispatch_operator(app, "DELETE", ("cron", "cron:dream"), None)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.payload["error"], "system_cron_jobs_cannot_be_deleted")
        self.assertIsNone(cron_runtime.removed_job_id)

    def test_manual_run_for_proactive_system_job_uses_special_handler(self) -> None:
        calls: list[str] = []

        def run_proactive_ask_now() -> dict[str, object]:
            calls.append("run")
            return {"cron": {"run": {"outcome": "success"}}}

        app = SimpleNamespace(run_proactive_ask_now=run_proactive_ask_now)

        response = _dispatch_operator(app, "POST", ("cron", "system:proactive-ask", "run"), b"{}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(calls, ["run"])
        self.assertEqual(response.payload["cron"]["run"]["outcome"], "success")


class InternalDiaryDispatchTest(unittest.TestCase):
    def test_delete_diary_entry_routes_to_internal_method(self) -> None:
        calls: list[str] = []

        def delete_diary_entry(*, entry_date: str) -> dict[str, object]:
            calls.append(entry_date)
            return {"status": "deleted", "entry_date": entry_date, "deleted": True}

        app = SimpleNamespace(delete_diary_entry=delete_diary_entry)

        response = _dispatch_internal(app, "DELETE", ("diary", "2026-05-14"), None)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(calls, ["2026-05-14"])
        self.assertEqual(response.payload["status"], "deleted")

    def test_delete_diary_entry_rejects_bad_date(self) -> None:
        def delete_diary_entry(*, entry_date: str) -> dict[str, object]:
            raise ValueError("entry_date must be YYYY-MM-DD")

        app = SimpleNamespace(delete_diary_entry=delete_diary_entry)

        response = _dispatch_internal(app, "DELETE", ("diary", "bad"), None)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.payload["error"], "entry_date must be YYYY-MM-DD")


if __name__ == "__main__":
    unittest.main()
