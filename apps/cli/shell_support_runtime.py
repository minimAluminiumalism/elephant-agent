"""Support classes and helper functions for the productized shell."""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from dataclasses import dataclass, field
from difflib import unified_diff
import os
from pathlib import Path
import re
import shlex
import time

from packages.contracts import ExperienceRecord
from packages.kernel.runtime import KernelOutcome
from packages.operator import (
    MemoryOperatorDetail,
    MemorySearchHit,
    build_memory_operator_surface,
    build_profile_operator_surface,
    render_memory_lines,
    render_profile_lines,
)
from packages.tools.handler_support import resolve_allowed_path
from .provider_flow import provider_setup_defaults, run_provider_selection_wizard
from .runtime import CliRuntime
from .wizard import WIZARD_BACK
from .shell_composer import (
    build_command_palette as _build_shell_command_palette,
    build_composer_body as _build_shell_composer_body,
    build_divider_window as _build_shell_divider_window,
    build_input_window as _build_shell_input_window,
    build_key_bindings as _build_shell_key_bindings,
    build_prompt_buffer as _build_shell_prompt_buffer,
    build_queue_preview_window as _build_shell_queue_preview_window,
    prompt_continuation as _shell_prompt_continuation,
    prompt_label as _shell_prompt_label,
    prompt_style as _shell_prompt_style,
    prompt_style_map as _shell_prompt_style_map,
    prompt_toolkit_composer_available as _shell_prompt_toolkit_composer_available,
    read_command as _read_shell_command,
    shell_history as _shell_history,
)
from .shell_boot import WAKE_DISPLAY_SECONDS, BootFrameContext, render_boot_frame
from .shell_opening import (
    ShellOpeningContext,
    compose_shell_opening_instruction,
    compose_shell_opener,
)
from .shell_progress import (
    animations_enabled as _shell_animations_enabled,
    render_queued_followup_fragments as _render_shell_queued_followup_fragments,
    render_tool_frame as _render_shell_tool_frame,
    tool_trace_line as _shell_tool_trace_line,
    render_turn_frame as _render_shell_turn_frame,
    render_turn_progress_fragments as _render_shell_turn_progress_fragments,
    run_tool_with_progress as _run_shell_tool_with_progress,
    run_turn_with_progress as _run_shell_turn_with_progress,
    run_turn_with_queued_input as _run_shell_turn_with_queued_input,
    summarize_progress_prompt as _summarize_shell_progress_prompt,
    tool_event_lines as _shell_tool_event_lines,
    tool_event_summary as _shell_tool_event_summary,
    tool_event_tracker as _shell_tool_event_tracker,
    tool_frame_phases as _shell_tool_frame_phases,
    turn_phase as _shell_turn_phase,
    _tool_trace_emoji as _shell_tool_trace_emoji,
)
from .shell_render import (
    center_brand_block as _center_shell_brand_block,
    displayable_experiences as _displayable_shell_experiences,
    format_experience_status as _format_shell_experience_status,
    growth_panel_lines as _shell_growth_panel_lines,
    growth_progress_bar as _shell_growth_progress_bar,
    growth_progress_counts as _shell_growth_progress_counts,
    recent_activity_lines as _shell_recent_activity_lines,
    recent_experience_lines as _shell_recent_experience_lines,
    render_brand_column as _render_shell_brand_column,
    render_chat_entry as _render_shell_chat_entry,
    render_entry as _render_shell_entry,
    render_elephant_brand_mark as _render_shell_elephant_mark,
    render_growth_mark_for_stage as _render_shell_growth_mark,
    render_pending_entries as _render_shell_pending_entries,
    render_shell_frame as _render_shell_frame_view,
    render_status_column as _render_shell_status_column,
    should_display_experience as _should_display_shell_experience,
    styled_growth_progress_bar as _styled_shell_growth_progress_bar,
)
from .shell_stack import (
    Align,
    Completion,
    Completer,
    Console,
    Document,
    FormattedText,
    Group,
    Live,
    PROMPT_TOOLKIT_AVAILABLE,
    Panel,
    RICH_AVAILABLE,
    Table,
    Text,
)
from .shell_ui import (
    BRAND_ACCENT,
    BRAND_ACCENT_STRONG,
    BRAND_DARK,
    BRAND_LIGHT,
    BRAND_MUTED,
    COMMAND_PALETTE_VISIBLE_ROWS,
    ELEPHANT_STAGE_ROWS,
    GROWTH_HIGHLIGHT_FG,
    GROWTH_PROGRESS_EMPTY,
    GROWTH_PROGRESS_FILLED,
    GROWTH_PROGRESS_WIDTH,
    HATCHLING_HEAD_ROWS,
    HATCHLING_STAGE_ROWS,
    HATCHLING_STAGE_ROWS,
    QUEUE_PREVIEW_INSET,
    SCOUT_STAGE_ROWS,
    SEED_STAGE_ROWS,
    SHELL_WELCOME_HEADLINE,
    USER_HISTORY_BG,
    USER_HISTORY_FG,
    WEB_URL_PATTERN,
    compact_line as _compact_line,
    centered_elephant_rows as _centered_elephant_rows,
    display_path as _display_path,
    display_width as _display_width,
    render_elephant_mark,
    resolve_elephant_version as _resolve_elephant_version,
)

@dataclass(frozen=True, slots=True)
class TranscriptEntry:
    kind: str
    title: str
    body: str
    meta: str = ""

@dataclass(frozen=True, slots=True)
class _PendingFileReview:
    path: Path
    before_text: str | None

@dataclass(frozen=True, slots=True)
class PendingShellCommand:
    command: str
    display_command: str = ""
    event_payload: Mapping[str, str] = field(default_factory=dict)


def coerce_pending_shell_command(value: object) -> PendingShellCommand:
    if isinstance(value, PendingShellCommand):
        return value
    command = str(getattr(value, "command", value) or "")
    display_command = str(getattr(value, "display_command", "") or "")
    payload = getattr(value, "event_payload", None)
    if isinstance(payload, Mapping):
        event_payload = {str(key): str(item) for key, item in payload.items()}
    else:
        event_payload = {}
    return PendingShellCommand(
        command=command,
        display_command=display_command,
        event_payload=event_payload,
    )

@dataclass(frozen=True, slots=True)
class ShellCommandSpec:
    name: str
    description: str

@dataclass(frozen=True, slots=True)
class SkillSlashSpec:
    command: str
    skill_id: str
    display_name: str
    summary: str
    aliases: tuple[str, ...] = ()
    trigger_phrases: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()

def _skill_metadata_values(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (list, tuple, set)):
        raw_items = tuple(value)
    else:
        text = str(value).strip()
        if not text:
            return ()
        raw_items = tuple(segment.strip() for segment in text.split(","))
    normalized: list[str] = []
    seen: set[str] = set()
    for item in raw_items:
        token = str(item).strip().strip("\"'")
        if not token:
            continue
        dedupe_key = token.lower()
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        normalized.append(token)
    return tuple(normalized)

def _normalize_skill_match_text(value: str) -> str:
    normalized = value.strip().lower().replace("/", " ").replace("_", " ").replace("-", " ")
    normalized = re.sub(r"[^\w\s\u4e00-\u9fff]+", " ", normalized)
    return " ".join(normalized.split())

def _skill_phrase_in_message(message: str, phrase: str) -> bool:
    normalized_message = _normalize_skill_match_text(message)
    normalized_phrase = _normalize_skill_match_text(phrase)
    if not normalized_phrase:
        return False
    if re.search(r"[\u4e00-\u9fff]", normalized_phrase):
        return normalized_phrase in normalized_message
    return f" {normalized_phrase} " in f" {normalized_message} "

def _completion(text: str, *, start_position: int, display: str, meta: str = "") -> Completion:
    try:
        return Completion(text, start_position=start_position, display=display, display_meta=meta)
    except TypeError:  # pragma: no cover - fallback signature
        return Completion(text, start_position=start_position, display=display)

class ShellCompleter(Completer):
    def __init__(self, shell: "ProductizedShell") -> None:
        self.shell = shell

    def get_completions(self, document: Document, complete_event):
        text = document.text_before_cursor
        stripped = text.lstrip()
        if not stripped.startswith("/"):
            return
        words = stripped.split()
        current_word = document.get_word_before_cursor(WORD=True)
        if not words:
            return
        command = words[0]
        if len(words) <= 1 and not text.endswith(" "):
            for spec in self.shell.command_specs:
                if spec.name.startswith(command):
                    yield _completion(
                        spec.name,
                        start_position=-len(current_word),
                        display=spec.name,
                        meta=spec.description,
                    )
            return

        if command == "/tools":
            candidates = (
                ("inspect", "Show metadata for one tool"),
                ("enable", "Enable a tool for this elephant"),
                ("disable", "Disable a tool for this elephant"),
                ("install", "Load a tool manifest into this elephant"),
                ("run", "Run a tool with explicit key=value arguments"),
            )
        elif command == "/skills":
            candidates = (
                ("list", "List discoverable skill packages from local shelves"),
                ("active", "Show currently active installed skills"),
                ("search", "Search installable skill packages from local shelves"),
                ("view", "Load one skill package and show its instructions"),
                ("inspect", "Alias for view"),
                ("enable", "Enable a skill for this elephant"),
                ("disable", "Disable a skill for this elephant"),
                ("install", "Install a skill package or manifest into this elephant"),
            )
        elif command == "/learn":
            candidates = (
                ("queue", "Queue learning for this episode"),
                ("run", "Queue learning and run the worker once now"),
                ("start", "Start the detached learning worker"),
                ("status", "Show recent learning jobs for this episode"),
                ("history", "Show recent learning jobs across herd"),
            )
        elif command == "/gateway":
            candidates = (
                ("status", "Show gateway setup guidance"),
                ("setup", "Open the CLI gateway setup command guidance"),
                ("doctor", "Show gateway doctor command guidance"),
            )
        elif command == "/providers":
            candidates = (
                ("configure", "Choose a provider, endpoint, key, model, and context window"),
                ("status", "Show the active provider configuration"),
                ("list", "List supported provider catalogs"),
            )
        elif command == "/models":
            candidates = (
                ("configure", "Choose the active model and context window"),
                ("status", "Show the active model configuration"),
                ("list", "List models exposed by the active provider endpoint"),
            )
        elif command == "/cron":
            candidates = (
                ("create", "Create a scheduled prompt task"),
                ("inspect", "Show one cron job"),
                ("pause", "Pause a cron job"),
                ("resume", "Resume a paused cron job"),
                ("remove", "Remove a cron job"),
            )
        else:
            return

        for value, description in candidates:
            if value.startswith(current_word):
                yield _completion(
                    value,
                    start_position=-len(current_word),
                    display=value,
                    meta=description,
                )

__all__ = [
    "TranscriptEntry",
    "_PendingFileReview",
    "PendingShellCommand",
    "coerce_pending_shell_command",
    "ShellCommandSpec",
    "SkillSlashSpec",
    "_skill_metadata_values",
    "_normalize_skill_match_text",
    "_skill_phrase_in_message",
    "_completion",
    "ShellCompleter",
]
