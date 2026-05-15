# Curiosity Package Rules

This package owns Elephant Agent's proactive-curiosity machinery. Runtime rules:

- No direct storage writes outside the repository API.
- OpenQuestion generation splits into three sources: coverage_gap
  (produced by `packages/learning/consolidate.py`), ambiguity (emitted when
  reconcile cannot resolve cross-source conflict), contextual (seeded by
  `packages/learning/extract.py` via `generate_contextual_questions`).
- Idle-clock semantics (ADR-0004): reset on the user's latest activity,
  not on Elephant Agent's latest ask. This module never touches user timestamps;
  callers pass `user_last_active_at`.
- All rendering funnels through `question_renderer.py` so prompt wording
  is centralized and sensitivity-aware.
