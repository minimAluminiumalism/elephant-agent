# Curiosity Package

This package owns proactive OpenQuestion behavior for Elephant Agent.

## Own Here

- `OpenQuestion` generation from contextual and ambiguity seeds
- proactive ask policy over caller-provided activity timestamps
- question rendering and sensitivity-aware user-facing wording
- tool surface behavior for answering, updating, and deleting questions

## Do Not Own Here

- direct storage writes outside repository APIs
- background learning job execution
- Personal Model fact promotion
- CLI or dashboard layout

Questions are created by background learning or runtime ambiguity detection.
Keep rendering centralized in `question_renderer.py` and keep policy inputs
explicit; callers own user activity timestamps.
