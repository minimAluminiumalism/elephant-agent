"""Token usage helpers for dashboard operations."""

from __future__ import annotations

from collections.abc import Mapping
import json
import sqlite3
from typing import Any


def _json_loads(value: object, fallback: Any) -> Any:
    if value is None:
        return fallback
    try:
        return json.loads(str(value))
    except (TypeError, ValueError, json.JSONDecodeError):
        return fallback


def _query(
    connection: sqlite3.Connection,
    sql: str,
    params: tuple[object, ...] = (),
) -> list[dict[str, Any]]:
    try:
        rows = connection.execute(sql, params).fetchall()
    except sqlite3.Error:
        return []
    return [dict(row) for row in rows]


def _int_value(value: object) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _cache_hit_rate_label(cached_tokens: int, prompt_tokens: int) -> str:
    if prompt_tokens <= 0:
        return "n/a"
    return f"{(cached_tokens / prompt_tokens) * 100:.1f}%"


def _cache_summary(*, cached_tokens: int, prompt_tokens: int, creation_tokens: int) -> str:
    if prompt_tokens <= 0:
        return "No input token usage recorded for this query."
    label = _cache_hit_rate_label(cached_tokens, prompt_tokens)
    creation_note = f"; {creation_tokens} cache-write token(s)" if creation_tokens else ""
    return f"{label} cache hit ({cached_tokens}/{prompt_tokens} input token(s) cached{creation_note})."


def normalize_token_usage_row(row: Mapping[str, Any]) -> dict[str, Any]:
    record = dict(row)
    metadata_payload = _json_loads(record.pop("metadata_json", None), {})
    metadata = dict(metadata_payload) if isinstance(metadata_payload, Mapping) else {}
    prompt_tokens = _int_value(record.get("prompt_tokens"))
    cached_tokens = _int_value(
        metadata.get("cached_prompt_tokens")
        or metadata.get("cachedPromptTokens")
        or metadata.get("cache_read_input_tokens")
    )
    creation_tokens = _int_value(
        metadata.get("cache_creation_prompt_tokens")
        or metadata.get("cacheCreationPromptTokens")
        or metadata.get("cache_creation_input_tokens")
    )
    cache_usage_reported = bool(
        metadata.get("cache_usage_reported")
        or metadata.get("cacheUsageReported")
        or "cached_prompt_tokens" in metadata
        or "cachedPromptTokens" in metadata
        or "cache_read_input_tokens" in metadata
        or "cache_creation_prompt_tokens" in metadata
        or "cacheCreationPromptTokens" in metadata
        or "cache_creation_input_tokens" in metadata
    )
    record["metadata"] = metadata
    record["cached_prompt_tokens"] = cached_tokens
    record["cache_creation_prompt_tokens"] = creation_tokens
    record["cache_usage_reported"] = cache_usage_reported
    record["cachedPromptTokens"] = cached_tokens
    record["cacheCreationPromptTokens"] = creation_tokens
    record["cacheUsageReported"] = cache_usage_reported
    if cache_usage_reported:
        cache_hit_rate_label = _cache_hit_rate_label(cached_tokens, prompt_tokens)
        cache_summary = _cache_summary(
            cached_tokens=cached_tokens,
            prompt_tokens=prompt_tokens,
            creation_tokens=creation_tokens,
        )
    else:
        cache_hit_rate_label = "n/a"
        cache_summary = "Cache usage was not reported by the provider for this query."
    record["cache_hit_rate_label"] = cache_hit_rate_label
    record["cache_summary"] = cache_summary
    record["cacheHitRateLabel"] = cache_hit_rate_label
    record["cacheSummary"] = cache_summary
    if cache_usage_reported and prompt_tokens > 0:
        cache_hit_rate = round(cached_tokens / prompt_tokens, 4)
        record["cache_hit_rate"] = cache_hit_rate
        record["cacheHitRate"] = cache_hit_rate
    return record


def token_usage_rows_for_session(connection: sqlite3.Connection, session_id: object) -> list[dict[str, Any]]:
    rows = _query(
        connection,
        """
        SELECT steps.step_id AS usage_id, steps.episode_id AS session_id,
               steps.personal_model_id AS profile_id, steps.loop_id AS run_id,
               steps.step_id AS source_event_id, steps.metadata_json,
               steps.created_at
        FROM steps
        WHERE steps.episode_id = ?
          AND (
            steps.metadata_json LIKE '%prompt_tokens%'
            OR steps.metadata_json LIKE '%completion_tokens%'
            OR steps.metadata_json LIKE '%total_tokens%'
          )
        ORDER BY steps.created_at ASC, steps.step_id ASC
        LIMIT 500
        """,
        (session_id,),
    )
    usage_rows: list[dict[str, Any]] = []
    for row in rows:
        metadata = _json_loads(row.get("metadata_json"), {})
        if not isinstance(metadata, Mapping):
            metadata = {}
        prompt_tokens = _int_value(metadata.get("prompt_tokens"))
        completion_tokens = _int_value(metadata.get("completion_tokens"))
        total_tokens = _int_value(metadata.get("total_tokens")) or prompt_tokens + completion_tokens
        if total_tokens <= 0:
            continue
        usage_rows.append(
            normalize_token_usage_row(
                {
                    **row,
                    "provider_id": metadata.get("provider_id") or metadata.get("providerId") or "runtime",
                    "model_id": metadata.get("model_id") or metadata.get("modelId") or "runtime-step",
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "unit": "tokens",
                }
            )
        )
    return usage_rows


def summarize_token_usage(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not rows:
        return None
    prompt_tokens = sum(_int_value(row.get("prompt_tokens")) for row in rows)
    completion_tokens = sum(_int_value(row.get("completion_tokens")) for row in rows)
    total_tokens = sum(_int_value(row.get("total_tokens")) for row in rows)
    cached_tokens = sum(_int_value(row.get("cached_prompt_tokens")) for row in rows)
    creation_tokens = sum(_int_value(row.get("cache_creation_prompt_tokens")) for row in rows)
    cache_usage_reported = any(bool(row.get("cache_usage_reported")) for row in rows)
    summary = {
        "promptTokens": prompt_tokens,
        "completionTokens": completion_tokens,
        "totalTokens": total_tokens,
        "cachedPromptTokens": cached_tokens,
        "cacheCreationPromptTokens": creation_tokens,
        "cacheUsageReported": cache_usage_reported,
        "cacheHitRateLabel": _cache_hit_rate_label(cached_tokens, prompt_tokens) if cache_usage_reported else "n/a",
        "cacheSummary": (
            _cache_summary(
                cached_tokens=cached_tokens,
                prompt_tokens=prompt_tokens,
                creation_tokens=creation_tokens,
            )
            if cache_usage_reported
            else "Cache usage was not reported by the provider for this query."
        ),
    }
    if cache_usage_reported and prompt_tokens > 0:
        summary["cacheHitRate"] = round(cached_tokens / prompt_tokens, 4)
    latest = rows[-1]
    if latest.get("provider_id"):
        summary["providerId"] = latest["provider_id"]
    if latest.get("model_id"):
        summary["modelId"] = latest["model_id"]
    return summary


def cache_usage_fields(run: Mapping[str, Any]) -> dict[str, Any]:
    token_usage = run.get("tokenUsage")
    if not isinstance(token_usage, Mapping):
        return {}
    if not token_usage.get("cacheUsageReported"):
        return {}
    cache_summary = str(token_usage.get("cacheSummary") or "").strip()
    if not cache_summary:
        return {}
    fields: dict[str, Any] = {
        "cacheHitRateLabel": token_usage.get("cacheHitRateLabel") or "n/a",
        "cacheSummary": cache_summary,
        "promptTokens": token_usage.get("promptTokens"),
        "cachedPromptTokens": token_usage.get("cachedPromptTokens"),
        "cacheCreationPromptTokens": token_usage.get("cacheCreationPromptTokens"),
    }
    if token_usage.get("cacheHitRate") is not None:
        fields["cacheHitRate"] = token_usage.get("cacheHitRate")
    return fields
