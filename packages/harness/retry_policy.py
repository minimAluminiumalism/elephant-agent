"""Generic retry wrapper for long-horizon provider and tool calls.

Current state of the art in the repo is a narrow TLS-handshake fallback in
``packages/models/providers/http.py`` (``_should_retry_with_curl``). Every
other failure mode — connect timeout, read timeout, 5xx, 429, mid-SSE
EOF — raises and fails the Loop. That is fatal for 24h+ runs: a six-hour
research task should not die because a DNS hiccup dropped one request.

This module provides a single ``with_retry`` primitive that:

* classifies the exception (network / http_5xx / http_429 /
  http_4xx_permanent / sse_incomplete / tool_transient / unknown);
* applies exponential backoff with jitter, bounded by a caller-supplied
  deadline and the policy ``max_attempts``;
* honours ``Retry-After`` (both integer seconds and HTTP-date) so we
  never double-hammer a provider that asked us to wait;
* surfaces the attempt count and idempotency key via
  :class:`packages.contracts.runtime.RetryState` so a resume can replay
  with the same key (avoiding double billing / duplicate side-effects).

SSE partial recovery is handled by the caller: if the provider already
yielded bytes, the caller catches the disconnect, persists what it has
via :meth:`LoopCheckpointService.mark_partial_assistant`, and surfaces
an ``sse_incomplete`` :class:`Retryable` to park the Loop for the
network wait condition instead of retrying in-place.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import random
import socket
import time
from typing import Callable, Iterable, TypeVar
from urllib import error as urllib_error

from packages.contracts.runtime import RetryState

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Error classification
# ---------------------------------------------------------------------------

_NETWORK_EXCEPTION_TYPES: tuple[type[BaseException], ...] = (
    ConnectionError,
    TimeoutError,
    socket.timeout,
    socket.gaierror,
    socket.herror,
)

# A retryable 5xx should not include 501 (Not Implemented) — retrying that is
# never productive. 500 / 502 / 503 / 504 / 507 / 509 / 598 / 599 are the
# useful ones in practice.
_RETRYABLE_5XX = frozenset({500, 502, 503, 504, 507, 509, 598, 599})

# Retryable 4xx: 408 Request Timeout and 425 Too Early behave like transient
# failures; 429 Too Many Requests gets its own classification for the sake
# of Retry-After handling.
_RETRYABLE_4XX = frozenset({408, 425})


def classify_error(exc: BaseException) -> str:
    """Return the coarse error class for :class:`RetryPolicy` decisions.

    Classes:

    * ``network`` — connect failures, DNS, socket timeouts, urllib URLError.
    * ``http_429`` — HTTP 429 or 503 with Retry-After in the body.
    * ``http_5xx`` — retryable server errors (500 / 502 / 504 / ...).
    * ``http_4xx_permanent`` — 4xx that we must not retry (401 / 403 / 404 / ...).
    * ``sse_incomplete`` — explicit signal from the SSE caller that
      bytes were already yielded; caller handles resume separately.
    * ``tool_transient`` — raised by tool handlers via :class:`Retryable`.
    * ``unknown`` — everything else.
    """
    if isinstance(exc, Retryable):
        return exc.kind or "unknown"
    status = _http_status_from_exception(exc)
    if status is not None:
        if status in _RETRYABLE_5XX:
            return "http_5xx"
        if status == 429:
            return "http_429"
        if status in _RETRYABLE_4XX:
            return "http_5xx"  # behaves like a transient server hiccup
        if 400 <= status < 500:
            return "http_4xx_permanent"
        if 500 <= status < 600:
            return "http_5xx"
    if isinstance(exc, urllib_error.URLError):
        # urllib wraps socket errors inside URLError.reason; the reason
        # text is the most reliable signal after the exception class
        # itself. Catching everything under URLError keeps DNS + TLS +
        # connect-refused on the same retryable path.
        return "network"
    if isinstance(exc, _NETWORK_EXCEPTION_TYPES):
        return "network"
    return "unknown"


def _http_status_from_exception(exc: BaseException) -> int | None:
    status = getattr(exc, "status_code", None)
    if isinstance(status, int):
        return status
    code = getattr(exc, "code", None)
    if isinstance(code, int):
        return code
    return None


# ---------------------------------------------------------------------------
# Policy + Retry-After parsing
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_attempts: int = 5
    base_backoff_s: float = 1.0
    max_backoff_s: float = 60.0
    jitter_ratio: float = 0.3
    respect_retry_after: bool = True
    retryable_kinds: tuple[str, ...] = (
        "network",
        "http_5xx",
        "http_429",
        "tool_transient",
    )


def parse_retry_after(value: object, *, now: datetime | None = None) -> float | None:
    """Return the number of seconds to wait per a ``Retry-After`` value.

    Accepts integer seconds (RFC 7231 delta-seconds) or an HTTP-date. The
    ``now`` argument exists so tests can pin time; production callers pass
    ``datetime.now(timezone.utc)``. Returns ``None`` for unparseable or
    negative values so the caller can fall back to policy backoff.
    """
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        seconds = float(text)
    except ValueError:
        seconds = None
    if seconds is not None:
        return max(0.0, seconds)
    try:
        when = parsedate_to_datetime(text)
    except (TypeError, ValueError):
        return None
    if when is None:
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    current = now or datetime.now(timezone.utc)
    delta = (when - current).total_seconds()
    return max(0.0, delta)


class Retryable(Exception):
    """Exception wrapper that carries an explicit retry classification.

    Tool handlers and the SSE caller raise ``Retryable(kind=..., ...)`` so
    the wrapper knows how to classify without inspecting the underlying
    error text. ``retry_after_s`` lets callers pin the backoff (for
    example when the provider sent a Retry-After header in the body of a
    streaming error frame).
    """

    def __init__(
        self,
        message: str,
        *,
        kind: str,
        retry_after_s: float | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message)
        self.kind = kind
        self.retry_after_s = retry_after_s
        self.__cause__ = cause


# ---------------------------------------------------------------------------
# Wrapper
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RetryDecision:
    """Outcome of a single retry evaluation, exposed to the on_retry hook."""

    attempt: int
    kind: str
    sleep_seconds: float
    error_detail: str
    next_retry_at: datetime


def with_retry(
    call: Callable[[], T],
    *,
    policy: RetryPolicy = RetryPolicy(),
    deadline: datetime | None = None,
    idempotency_key: str | None = None,
    on_retry: Callable[[RetryDecision], None] | None = None,
    initial_state: RetryState | None = None,
    clock: Callable[[], datetime] | None = None,
    sleeper: Callable[[float], None] | None = None,
    retry_after_of: Callable[[BaseException], float | None] | None = None,
) -> T:
    """Invoke ``call`` with exponential backoff until it succeeds or gives up.

    Parameters
    ----------
    call
        Callable taking no arguments. It must be idempotent with respect
        to the configured ``idempotency_key`` — providers typically
        require the caller to include that key in the request headers.
    policy
        :class:`RetryPolicy` controlling attempts + backoff shape.
    deadline
        If given, the wrapper never sleeps past ``deadline``; a remaining
        budget of zero aborts further retries and re-raises.
    idempotency_key
        Persisted into the raised / returned :class:`RetryState` so the
        resume path can replay with the same key.
    on_retry
        Hook invoked after each transient failure, before the sleep.
    initial_state
        Lets the supervisor thread the previous attempt counter into the
        wrapper (so a crashed run resumes with attempt N rather than 0).
    clock / sleeper / retry_after_of
        Test seams. Production passes ``None``.
    """
    now_fn = clock or (lambda: datetime.now(timezone.utc))
    sleep_fn = sleeper or time.sleep
    retry_after_fn = retry_after_of or _default_retry_after_of

    state = initial_state or RetryState(idempotency_key=idempotency_key)
    if idempotency_key and not state.idempotency_key:
        state = replace(state, idempotency_key=idempotency_key)

    attempt = state.attempt
    while True:
        attempt += 1
        try:
            return call()
        except BaseException as exc:  # noqa: BLE001 — caller gave us a generic callable
            kind = classify_error(exc)
            if kind not in policy.retryable_kinds:
                raise
            if attempt >= policy.max_attempts:
                raise
            retry_after = retry_after_fn(exc) if policy.respect_retry_after else None
            sleep_seconds = _backoff_seconds(policy, attempt=attempt, retry_after_s=retry_after)
            now = now_fn()
            if deadline is not None:
                remaining = (deadline - now).total_seconds()
                if remaining <= 0:
                    raise
                sleep_seconds = min(sleep_seconds, remaining)
            detail = _compact_error_detail(exc)
            next_retry = now + timedelta(seconds=sleep_seconds)
            state = RetryState(
                attempt=attempt,
                last_error_kind=kind,
                last_error_detail=detail,
                next_retry_at=next_retry,
                idempotency_key=state.idempotency_key,
            )
            if on_retry is not None:
                on_retry(
                    RetryDecision(
                        attempt=attempt,
                        kind=kind,
                        sleep_seconds=sleep_seconds,
                        error_detail=detail,
                        next_retry_at=next_retry,
                    )
                )
            if sleep_seconds > 0:
                sleep_fn(sleep_seconds)


def _backoff_seconds(
    policy: RetryPolicy,
    *,
    attempt: int,
    retry_after_s: float | None,
) -> float:
    if retry_after_s is not None and retry_after_s >= 0:
        # Still clamp to max_backoff_s so a misbehaving provider that
        # returns "Retry-After: 3600" does not pin the Loop for an hour.
        return min(float(retry_after_s), policy.max_backoff_s)
    # Standard exponential backoff with equal jitter. Attempts start at 1.
    base = min(policy.base_backoff_s * (2 ** max(0, attempt - 1)), policy.max_backoff_s)
    if policy.jitter_ratio <= 0:
        return base
    jitter = base * policy.jitter_ratio
    return max(0.0, base + random.uniform(-jitter, jitter))


def _compact_error_detail(exc: BaseException) -> str:
    detail = str(exc).strip()
    if not detail:
        detail = type(exc).__name__
    # SSE / HTTP errors can embed enormous bodies; cap it.
    if len(detail) > 320:
        detail = detail[:317] + "..."
    return detail


def _default_retry_after_of(exc: BaseException) -> float | None:
    retry_after_attr = getattr(exc, "retry_after_s", None)
    if isinstance(retry_after_attr, (int, float)):
        return max(0.0, float(retry_after_attr))
    headers = getattr(exc, "headers", None)
    if headers is not None:
        # Handle both Mapping and email.Message-like objects.
        raw = None
        try:
            raw = headers.get("Retry-After")  # type: ignore[union-attr]
        except AttributeError:
            raw = None
        if raw is None:
            try:
                raw = headers["Retry-After"]  # type: ignore[index]
            except (KeyError, TypeError):
                raw = None
        if raw is not None:
            return parse_retry_after(raw)
    return None


__all__ = [
    "RetryDecision",
    "RetryPolicy",
    "Retryable",
    "_NETWORK_EXCEPTION_TYPES",
    "classify_error",
    "parse_retry_after",
    "with_retry",
]


# keep _field_ import used in dataclass slots re-export quiet
_ = field
_ = Iterable
