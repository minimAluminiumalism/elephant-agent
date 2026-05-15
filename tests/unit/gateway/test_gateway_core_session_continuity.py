from __future__ import annotations

import unittest
from datetime import datetime, timezone

from packages.gateway_core import (
    GatewayAccountRef,
    GatewayConversationRef,
    GatewayCoreDependencies,
    GatewayCoreService,
    GatewayIdentityKey,
    GatewayIdentityRecord,
    GatewayInboundMessage,
    GatewayRouteState,
    GatewaySenderRef,
    InMemoryGatewayIdentityStore,
    InMemoryGatewaySessionStore,
)
from packages.security.runtime import SecurityPolicy


class GatewayCoreSessionContinuityTest(unittest.TestCase):
    def _core(self) -> GatewayCoreService:
        self.identity_store = InMemoryGatewayIdentityStore()
        self.session_store = InMemoryGatewaySessionStore()
        return GatewayCoreService(
            GatewayCoreDependencies(
                identity_store=self.identity_store,
                session_store=self.session_store,
                security_policy=SecurityPolicy.default(),
                default_profile_id="you",
            )
        )

    def _inbound(self, conversation_id: str = "chat-1") -> GatewayInboundMessage:
        return GatewayInboundMessage(
            event_id="evt-1",
            account=GatewayAccountRef(adapter_id="messaging.weixin", account_id="wx-account"),
            conversation=GatewayConversationRef(conversation_id=conversation_id, chat_type="direct"),
            sender=GatewaySenderRef(external_user_id="wx-user"),
            body="hello",
        )

    def test_rebinding_existing_conversation_preserves_episode_pin(self) -> None:
        core = self._core()
        key = GatewayIdentityKey(
            adapter_id="messaging.weixin",
            account_id="wx-account",
            conversation_id="chat-1",
        )
        now = datetime(2026, 5, 7, tzinfo=timezone.utc)
        self.session_store.save(
            GatewayRouteState(
                session_id="episode:pinned",
                profile_id="you",
                status="active",
                started_at=now,
                updated_at=now,
            )
        )
        self.identity_store.save(
            GatewayIdentityRecord(
                mapping_id="mapping:wx",
                key=key,
                session_id="episode:pinned",
                state_id="state:zoey",
                elephant_id="zoey",
                episode_id="episode:pinned",
                created_at=now,
                updated_at=now,
            )
        )

        rebound = core.bind_elephant(self._inbound(), elephant_id="zoey", state_id="state:zoey")

        self.assertEqual(rebound.session_id, "episode:pinned")
        self.assertEqual(rebound.episode_id, "episode:pinned")
        routed = core.route_inbound(self._inbound())
        self.assertEqual(routed.identity.episode_id, "episode:pinned")
        self.assertEqual(routed.session.session_id, "episode:pinned")


if __name__ == "__main__":
    unittest.main()
