"""Tests for `resolve_cron_identity_records` — the single-elephant cron fallback.

When a cron job is created without a bound `elephant_id` (e.g. through the dashboard POST
`/operator/cron` without an `elephant_id` field, or through an older IM handler that did not
populate it), delivery should still succeed if there is exactly one identity registered
for the adapter. With zero or multiple candidate herd the helper returns `()` so the
caller can log and skip rather than spam the wrong chat.
"""

from __future__ import annotations

import unittest

from packages.gateway_core import (
    GatewayIdentityKey,
    GatewayIdentityRecord,
    InMemoryGatewayIdentityStore,
    resolve_cron_identity_records,
)


def _record(adapter_id: str, conversation_id: str, *, elephant_id: str | None) -> GatewayIdentityRecord:
    return GatewayIdentityRecord(
        mapping_id=f"mapping:{adapter_id}:{conversation_id}",
        key=GatewayIdentityKey(
            adapter_id=adapter_id,
            account_id=f"{adapter_id}-account",
            conversation_id=conversation_id,
        ),
        session_id=f"session:{conversation_id}",
        elephant_id=elephant_id,
    )


class ResolveCronIdentityRecordsTest(unittest.TestCase):
    def test_explicit_elephant_id_returns_its_records(self) -> None:
        store = InMemoryGatewayIdentityStore()
        store.save(_record("messaging.weixin", "chat-A", elephant_id="hazel"))
        store.save(_record("messaging.weixin", "chat-B", elephant_id="basil"))

        result = resolve_cron_identity_records(
            identity_store=store,
            adapter_id="messaging.weixin",
            elephant_id="hazel",
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].key.conversation_id, "chat-A")

    def test_missing_elephant_id_falls_back_to_single_elephant(self) -> None:
        store = InMemoryGatewayIdentityStore()
        store.save(_record("messaging.weixin", "chat-A", elephant_id="hazel"))

        result = resolve_cron_identity_records(
            identity_store=store,
            adapter_id="messaging.weixin",
            elephant_id=None,
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].elephant_id, "hazel")

    def test_missing_elephant_id_refuses_when_multiple_elephants(self) -> None:
        store = InMemoryGatewayIdentityStore()
        store.save(_record("messaging.weixin", "chat-A", elephant_id="hazel"))
        store.save(_record("messaging.weixin", "chat-B", elephant_id="basil"))

        result = resolve_cron_identity_records(
            identity_store=store,
            adapter_id="messaging.weixin",
            elephant_id=None,
        )
        self.assertEqual(result, ())

    def test_missing_elephant_id_filters_out_other_adapters(self) -> None:
        # A feishu identity is registered but we ask about weixin with no elephant_id.
        # The fallback only counts weixin identities — so a single weixin elephant is
        # a single-elephant fallback regardless of what other adapters have.
        store = InMemoryGatewayIdentityStore()
        store.save(_record("messaging.weixin", "chat-A", elephant_id="hazel"))
        store.save(_record("messaging.feishu", "chat-X", elephant_id="basil"))

        weixin = resolve_cron_identity_records(
            identity_store=store,
            adapter_id="messaging.weixin",
            elephant_id=None,
        )
        self.assertEqual(len(weixin), 1)
        self.assertEqual(weixin[0].key.adapter_id, "messaging.weixin")

        feishu = resolve_cron_identity_records(
            identity_store=store,
            adapter_id="messaging.feishu",
            elephant_id=None,
        )
        self.assertEqual(len(feishu), 1)
        self.assertEqual(feishu[0].key.adapter_id, "messaging.feishu")

    def test_no_adapter_records_returns_empty(self) -> None:
        store = InMemoryGatewayIdentityStore()
        store.save(_record("messaging.feishu", "chat-X", elephant_id="basil"))

        result = resolve_cron_identity_records(
            identity_store=store,
            adapter_id="messaging.weixin",
            elephant_id=None,
        )
        self.assertEqual(result, ())

    def test_explicit_elephant_id_with_no_match_returns_empty(self) -> None:
        store = InMemoryGatewayIdentityStore()
        store.save(_record("messaging.weixin", "chat-A", elephant_id="hazel"))

        result = resolve_cron_identity_records(
            identity_store=store,
            adapter_id="messaging.weixin",
            elephant_id="unknown-elephant",
        )
        self.assertEqual(result, ())


if __name__ == "__main__":
    unittest.main()
