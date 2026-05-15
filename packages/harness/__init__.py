"""Long-horizon harness support for Elephant Agent.

This package owns the subsystems that let a single task run for 24h+ unattended:

* ``retry_policy`` — generic exponential-backoff wrapper that understands
  Retry-After, classifies errors into retryable vs permanent, and persists
  :class:`packages.contracts.runtime.RetryState` so resume replays reuse
  the same idempotency key.
* ``supervisor`` — heartbeat + crash-scan + timer-wake driver. Poll loop
  reads ``list_loop_checkpoints`` every interval, decides whether to
  reclaim a zombie Loop or wake a ripe timer, and clears the
  pending_tool_call / partial_assistant bookkeeping via resume_support.

Other subsystems listed in the Phase 4 master plan (event bus, network
probe, CLI daemon wiring, budget policy typing) live alongside this
package in later commits. Everything here is dependency-light so the
kernel and storage layers can import without pulling adapters or apps.
"""

from .retry_policy import (
    RetryDecision,
    RetryPolicy,
    Retryable,
    classify_error,
    parse_retry_after,
    with_retry,
)
from .supervisor import (
    DEFAULT_HEARTBEAT_FRESH_TTL_SECONDS,
    DEFAULT_HEARTBEAT_STALE_TTL_SECONDS,
    DEFAULT_SUPERVISOR_INTERVAL_SECONDS,
    SupervisorDecision,
    SupervisorRepository,
    SupervisorTickResult,
    run_supervisor_loop,
    scan_once,
)

__all__ = [
    "DEFAULT_HEARTBEAT_FRESH_TTL_SECONDS",
    "DEFAULT_HEARTBEAT_STALE_TTL_SECONDS",
    "DEFAULT_SUPERVISOR_INTERVAL_SECONDS",
    "RetryDecision",
    "RetryPolicy",
    "Retryable",
    "SupervisorDecision",
    "SupervisorRepository",
    "SupervisorTickResult",
    "classify_error",
    "parse_retry_after",
    "run_supervisor_loop",
    "scan_once",
    "with_retry",
]
