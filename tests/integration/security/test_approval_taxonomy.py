from __future__ import annotations

import unittest

from packages.security import (
    ApprovalClass,
    PolicyDecision,
    RiskLevel,
    SecurityPolicy,
    SecurityRequest,
    default_policy_rules,
)


class ApprovalTaxonomyIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = SecurityPolicy.default()

    def test_default_rules_cover_required_surfaces(self) -> None:
        self.assertEqual(
            set(default_policy_rules()),
            {
                ApprovalClass.READ,
                ApprovalClass.WRITE,
                ApprovalClass.EXEC,
                ApprovalClass.NETWORK,
                ApprovalClass.MESSAGING,
                ApprovalClass.VOICE_DEVICE,
            },
        )

    def test_read_is_allow_and_low_risk(self) -> None:
        result = self.policy.evaluate(
            SecurityRequest(
                request_id="req-read",
                approval_class=ApprovalClass.READ,
                operation="read-session-state",
            )
        )
        self.assertEqual(result.decision, PolicyDecision.ALLOW)
        self.assertEqual(result.risk_level, RiskLevel.LOW)
        self.assertTrue(result.approved)
        self.assertIn("audit-read", result.required_controls)

    def test_write_defaults_to_consent_then_allows_after_acknowledgement(self) -> None:
        pending = self.policy.evaluate(
            SecurityRequest(
                request_id="req-write",
                approval_class=ApprovalClass.WRITE,
                operation="persist-artifact",
            )
        )
        self.assertEqual(pending.decision, PolicyDecision.ALLOW_WITH_CONSENT)
        self.assertEqual(pending.risk_level, RiskLevel.MODERATE)
        self.assertIn("confirm-change", pending.required_controls)

        approved = self.policy.evaluate(
            SecurityRequest(
                request_id="req-write-consented",
                approval_class=ApprovalClass.WRITE,
                operation="persist-artifact",
                consent_given=True,
            )
        )
        self.assertEqual(approved.decision, PolicyDecision.ALLOW)
        self.assertTrue(approved.approved)

    def test_exec_is_reviewed_as_high_risk(self) -> None:
        result = self.policy.evaluate(
            SecurityRequest(
                request_id="req-exec",
                approval_class=ApprovalClass.EXEC,
                operation="run-shell-command",
            )
        )
        self.assertEqual(result.decision, PolicyDecision.REVIEW)
        self.assertEqual(result.risk_level, RiskLevel.HIGH)
        self.assertIn("sandbox", result.required_controls)
        self.assertFalse(result.decision.is_terminal)

    def test_network_external_triggers_review_and_audit_event(self) -> None:
        result = self.policy.evaluate(
            SecurityRequest(
                request_id="req-network",
                approval_class=ApprovalClass.NETWORK,
                operation="fetch-remote-resource",
                is_external=True,
            )
        )
        self.assertEqual(result.decision, PolicyDecision.REVIEW)
        self.assertEqual(result.risk_level, RiskLevel.CRITICAL)
        self.assertIn("boundary-review", result.required_controls)

        audit = result.to_audit_event()
        self.assertEqual(audit.request_id, "req-network")
        self.assertEqual(audit.decision, PolicyDecision.REVIEW)
        self.assertEqual(audit.approval_class, ApprovalClass.NETWORK)

    def test_messaging_can_be_approved_for_trusted_target_with_consent(self) -> None:
        result = self.policy.evaluate(
            SecurityRequest(
                request_id="req-msg",
                approval_class=ApprovalClass.MESSAGING,
                operation="send-message",
                target_trusted=True,
                consent_given=True,
            )
        )
        self.assertEqual(result.decision, PolicyDecision.ALLOW)
        self.assertEqual(result.risk_level, RiskLevel.MODERATE)
        self.assertIn("recipient-check", result.required_controls)
        self.assertIn("trusted-target", result.matched_factors)

    def test_untrusted_messaging_requires_review(self) -> None:
        result = self.policy.evaluate(
            SecurityRequest(
                request_id="req-msg-untrusted",
                approval_class=ApprovalClass.MESSAGING,
                operation="send-message",
                target_trusted=False,
            )
        )
        self.assertEqual(result.decision, PolicyDecision.REVIEW)
        self.assertEqual(result.risk_level, RiskLevel.HIGH)
        self.assertIn("recipient-verification", result.required_controls)
        self.assertIn("untrusted-target", result.matched_factors)

    def test_voice_device_requires_boundary_controls(self) -> None:
        result = self.policy.evaluate(
            SecurityRequest(
                request_id="req-voice",
                approval_class=ApprovalClass.VOICE_DEVICE,
                operation="open-microphone",
                recording_enabled=True,
            )
        )
        self.assertEqual(result.decision, PolicyDecision.REVIEW)
        self.assertEqual(result.risk_level, RiskLevel.CRITICAL)
        self.assertIn("recording-consent", result.required_controls)
        self.assertIn("voice-boundary", result.matched_factors)

    def test_missing_rule_fails_closed(self) -> None:
        broken_policy = SecurityPolicy(rules={})
        result = broken_policy.evaluate(
            SecurityRequest(
                request_id="req-missing",
                approval_class=ApprovalClass.READ,
                operation="read-session-state",
            )
        )
        self.assertEqual(result.decision, PolicyDecision.DENY)
        self.assertEqual(result.risk_level, RiskLevel.CRITICAL)
        self.assertIn("register-policy-rule", result.required_controls)
        self.assertIn("missing-rule", result.matched_factors)


if __name__ == "__main__":
    unittest.main()
