"""Question management feature — create, settle, dismiss proactive questions."""

from __future__ import annotations

from .types import Feature

FEATURE = Feature(
    feature_id="questions",
    tools=("tool.personal_model.questions",),
    sop_fragment="""\
- tool.personal_model.questions action=list → review open questions.
- Settle questions whose answers are now known from the evidence.
- Create new questions for gaps or uncertain inferences (2-3 max).
- Dismiss stale questions that are no longer relevant.""",
    constraints="""\
- Use questions for uncertain inferences rather than guessing facts.
- Keep question bank small and actionable.""",
)
