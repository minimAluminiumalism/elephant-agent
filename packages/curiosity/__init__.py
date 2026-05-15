"""Personal Model question subsystem.

Lens/topic-bound question loop for the Understanding System.
Questions are created by the background learning agent; this package
provides the proactive ask policy and rendering helpers.
"""

from .open_question_generator import (
    generate_ambiguity_questions,
    generate_contextual_questions,
)
from .proactive_ask_policy import AskDecision, should_ask
from .question_renderer import render_idle_push, render_opener, render_session_hint

__all__ = [
    "AskDecision",
    "generate_ambiguity_questions",
    "generate_contextual_questions",
    "render_idle_push",
    "render_opener",
    "render_session_hint",
    "should_ask",
]
