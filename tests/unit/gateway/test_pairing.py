from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest

from packages.gateway_core import FileGatewayPairingStore, PAIRING_CODE_LENGTH


class FileGatewayPairingStoreTest(unittest.TestCase):
    def test_create_approve_and_revoke_pairing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            now = datetime(2026, 4, 19, 10, 0, tzinfo=timezone.utc)
            store = FileGatewayPairingStore(Path(tmpdir), clock=lambda: now)

            request = store.create_request(
                platform="Feishu",
                external_user_id="user-1",
                display_name="User One",
                metadata={"chat_id": "chat-1"},
            )
            self.assertEqual(len(request.code), PAIRING_CODE_LENGTH)
            self.assertTrue((Path(tmpdir) / "feishu-pending.json").exists())

            approval = store.approve(platform="feishu", code=request.code.lower())

            self.assertIsNotNone(approval)
            self.assertTrue(store.is_approved(platform="feishu", external_user_id="user-1"))
            self.assertTrue((Path(tmpdir) / "feishu-approved.json").exists())
            self.assertEqual(store.pending_requests(platform="feishu"), ())
            self.assertTrue(store.revoke(platform="feishu", external_user_id="user-1"))
            self.assertFalse(store.is_approved(platform="feishu", external_user_id="user-1"))

    def test_expired_pairing_cannot_be_approved(self) -> None:
        current = datetime(2026, 4, 19, 10, 0, tzinfo=timezone.utc)

        def clock() -> datetime:
            return current

        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileGatewayPairingStore(Path(tmpdir), clock=clock)
            request = store.create_request(platform="discord", external_user_id="user-2")
            current = current + timedelta(hours=2)

            self.assertIsNone(store.approve(platform="discord", code=request.code))
            self.assertFalse(store.is_approved(platform="discord", external_user_id="user-2"))


if __name__ == "__main__":
    unittest.main()
