"""Recall query planning for multilingual history and claim search.

This module intentionally keeps deterministic heuristics small and explicit.
They are weak signals that can abstain, not a replacement for semantic search.
The planner is responsible for separating query operators (time / recap /
verification intent) from the topic core that retrieval should match.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata

__all__ = [
    "RecallQueryPlan",
    "normalize_recall_query",
    "plan_recall_query",
]

_RECALL_BLOCK_RE = re.compile(
    r"Current-turn recall support:[ \t]*(?:\r?\n[ \t]*-[^\n]*)*",
    re.IGNORECASE,
)
_WORD_RE = re.compile(r"[A-Za-z0-9_./:-]+")
_CJK_RE = re.compile(r"[\u3400-\u9fff\uf900-\ufaff]")

_RECENT_EN_RE = re.compile(
    r"\b(recently|lately|latest|last\s+time|last\s+turn|just\s+now|earlier\s+today)\b",
    re.IGNORECASE,
)
_CURRENT_EN_RE = re.compile(
    r"\b(now|current|currently|today|right\s+now|at\s+the\s+moment|this\s+week)\b",
    re.IGNORECASE,
)
_HISTORICAL_EN_RE = re.compile(
    r"\b(previously|before|historically|originally|at\s+first|why)\b",
    re.IGNORECASE,
)
_RECAP_EN_RE = re.compile(
    r"\b(what\s+(did|have)\s+we\s+(talk|talked|discuss|discussed|chat|chatted)\s+(about\s+)?|we\s+(talked|discussed|chatted)\s+(about\s+)?|recap|summari[sz]e)\b",
    re.IGNORECASE,
)
_VERIFY_EN_RE = re.compile(
    r"\b(verify|confirm|check|still|up\s+to\s+date|accurate|correct)\b",
    re.IGNORECASE,
)

_RECENT_CJK_TERMS = ("最近", "近来", "近期", "刚刚", "刚才", "上次", "这次")
_CURRENT_CJK_TERMS = ("现在", "当前", "目前", "当下", "今天", "今日")
_HISTORICAL_CJK_TERMS = ("之前", "以前", "过去", "当初", "历史", "为什么", "为何")
_VERIFY_CJK_TERMS = ("确认", "核实", "验证", "还准", "还对", "是否准确", "是不是最新")
_RECAP_CJK_RE = re.compile(
    r"(我们|咱们)?\s*(聊|讨论|说|谈)(了|过)?(一些什么|一些啥|些什么|些啥|什么事|啥事|哪些|什么|啥|一些|些|内容|话题)?|回顾一下|总结一下|复盘一下"
)
_TRAILING_RECAP_CJK_RE = re.compile(r"(什么|啥|哪些|内容|话题)$")


@dataclass(frozen=True, slots=True)
class RecallQueryPlan:
    raw_query: str
    query_core: str
    temporal_intent: str = "neutral"
    recall_mode: str = "contextual_recall"
    confidence: float = 0.0
    signals: tuple[str, ...] = ()

    @property
    def search_query(self) -> str:
        """Back-compatible alias for callers that expect search_query."""

        return self.query_core


def normalize_recall_query(query: str) -> str:
    text = unicodedata.normalize("NFKC", str(query or ""))
    text = _RECALL_BLOCK_RE.sub(" ", text)
    text = re.sub(r"[\s\u3000]+", " ", text).strip()
    text = re.sub(r"[?!？！，,。.;；:：]+", " ", text)
    return " ".join(text.split()).strip()


def _contains_cjk_temporal(text: str, terms: tuple[str, ...]) -> bool:
    for term in terms:
        if term == "最近":
            if re.search(r"最近(?!邻)", text):
                return True
            continue
        if term in text:
            return True
    return False


def _strip_cjk_terms(text: str, terms: tuple[str, ...]) -> str:
    out = text
    for term in terms:
        if term == "最近":
            out = re.sub(r"最近(?!邻)", " ", out)
            continue
        out = out.replace(term, " ")
    return out


def _has_topic_core(text: str) -> bool:
    return bool(_WORD_RE.search(text) or len(_CJK_RE.findall(text)) >= 2)


def _core_after_operator_removal(raw: str, *, remove_recap: bool, remove_temporal: bool, remove_verify: bool) -> str:
    core = raw
    if remove_temporal:
        core = _RECENT_EN_RE.sub(" ", core)
        core = _CURRENT_EN_RE.sub(" ", core)
        core = _HISTORICAL_EN_RE.sub(" ", core)
        core = _strip_cjk_terms(core, _RECENT_CJK_TERMS)
        core = _strip_cjk_terms(core, _CURRENT_CJK_TERMS)
        core = _strip_cjk_terms(core, _HISTORICAL_CJK_TERMS)
    if remove_recap:
        core = _RECAP_EN_RE.sub(" ", core)
        core = _RECAP_CJK_RE.sub(" ", core)
        core = _TRAILING_RECAP_CJK_RE.sub(" ", core)
    if remove_verify:
        core = _VERIFY_EN_RE.sub(" ", core)
        core = _strip_cjk_terms(core, _VERIFY_CJK_TERMS)
    return normalize_recall_query(core)


def plan_recall_query(query: str) -> RecallQueryPlan:
    raw = normalize_recall_query(query)
    if not raw:
        return RecallQueryPlan(raw_query="", query_core="", confidence=1.0, signals=("empty",))

    signals: list[str] = []
    has_recent = bool(_RECENT_EN_RE.search(raw)) or _contains_cjk_temporal(raw, _RECENT_CJK_TERMS)
    has_current = bool(_CURRENT_EN_RE.search(raw)) or _contains_cjk_temporal(raw, _CURRENT_CJK_TERMS)
    has_historical = bool(_HISTORICAL_EN_RE.search(raw)) or _contains_cjk_temporal(raw, _HISTORICAL_CJK_TERMS)
    has_recap = bool(_RECAP_EN_RE.search(raw) or _RECAP_CJK_RE.search(raw))
    has_verify = bool(_VERIFY_EN_RE.search(raw)) or any(term in raw for term in _VERIFY_CJK_TERMS)

    if has_current:
        temporal_intent = "current"
        signals.append("temporal.current")
    elif has_recent:
        temporal_intent = "recent"
        signals.append("temporal.recent")
    elif has_historical:
        temporal_intent = "historical"
        signals.append("temporal.historical")
    else:
        temporal_intent = "neutral"

    if has_recap:
        signals.append("mode.recap")
    if has_verify:
        signals.append("mode.verify")

    core = _core_after_operator_removal(
        raw,
        remove_recap=has_recap,
        remove_temporal=has_recent or has_current or has_historical,
        remove_verify=has_verify,
    )
    if not _has_topic_core(core):
        core = ""

    if has_recap:
        recall_mode = "recap" if core else "list_recent"
    elif has_verify or temporal_intent == "current":
        recall_mode = "verify"
    elif temporal_intent == "historical":
        recall_mode = "active_search"
    else:
        recall_mode = "contextual_recall"

    confidence = 0.35
    if temporal_intent != "neutral":
        confidence += 0.2
    if recall_mode != "contextual_recall":
        confidence += 0.2
    if core and core != raw:
        confidence += 0.15
    if not signals:
        signals.append("mode.contextual_recall.default")
    return RecallQueryPlan(
        raw_query=raw,
        query_core=core if core or recall_mode == "list_recent" else raw,
        temporal_intent=temporal_intent,
        recall_mode=recall_mode,
        confidence=min(1.0, confidence),
        signals=tuple(dict.fromkeys(signals)),
    )
