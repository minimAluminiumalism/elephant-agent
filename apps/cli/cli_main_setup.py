"""Interactive setup helpers for the CLI entrypoint."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
import random
import re
import select
import sys
import time
from collections.abc import Iterable
from pathlib import Path

from packages.state import DEFAULT_ELEPHANT_IDENTITY_TEXT, render_default_elephant_identity

from .runtime import CliRuntime
from .provider_flow import (
    ProviderSelectionState,
    provider_choices as _shared_provider_choices,
    provider_setup_defaults,
    run_provider_selection_wizard,
)
from .shell import (
    Align,
    BRAND_ACCENT,
    BRAND_ACCENT_STRONG,
    BRAND_DARK,
    BRAND_LIGHT,
    BRAND_MUTED,
    Console,
    Group,
    Panel,
    ProductizedShell,
    RICH_AVAILABLE,
    Table,
    Text,
    _resolve_elephant_version,
    render_stage_zero_elephant_mark,
)
from .wizard import (
    WIZARD_BACK,
    WIZARD_CANCEL,
    WizardChoice,
    _WizardBackSignal,
    _interactive_shell_supported,
    _wizard_choice_prompt,
    _wizard_dialogs_supported,
    _wizard_text_prompt,
)
from .shell_stack import Live

DEFAULT_PROVIDER_ID = "openai-compatible"
DEFAULT_ELEPHANT_NAME_SUGGESTIONS = (
    "Ada",
    "Asher",
    "Avery",
    "Caleb",
    "Chloe",
    "Eden",
    "Eli",
    "Eliza",
    "Felix",
    "Hazel",
    "Iris",
    "Jasper",
    "Julian",
    "Leah",
    "Lena",
    "Leo",
    "Maya",
    "Miles",
    "Milo",
    "Nina",
    "Nora",
    "Owen",
    "Ruby",
    "Rowan",
    "Simon",
    "Silas",
    "Theo",
    "Vera",
    "Zoe",
)
CLI_THEME_TITLE_GLYPH = "🐘"
CLI_THEME_BULLET = "•"
CLI_THEME_WELCOME_GLYPH = "🐘"
CLI_THEME_SUBTITLE = "Who you are, what matters, and what should stay close."

INIT_REFLECTION_LINES = (
    "Start with personal anchors first: name, context, style, rhythms, and care notes.",
    "After those are in place, name the Elephant Agent and choose the model/recall path.",
    "Then wire IM if you want Elephant Agent reachable beyond the local CLI.",
)
INIT_SETUP_STEPS = (
    ("01  You", "Personal context, language, hobbies, and optional care notes."),
    ("02  Almost", "A short pause after the Personal Model anchors are gathered."),
    ("03  Elephant + Model", "The first Elephant Agent name, dialogue model, and recall path."),
    ("04  Wake + IM", "Open the first elephant and optionally wire messenger access."),
)
INIT_ANIMATION_STAGES = (
    (
        "Stage 0",
        "Elephant Agent starts as a blank elephant.",
        "Nothing personal is assumed yet.",
    ),
    (
        "Personal anchors first",
        "A few true things give the elephant a first outline.",
        "Your context, style, hobbies, and care notes stay editable.",
    ),
    (
        "Only a few steps left",
        "After the personal pass, setup turns to the elephant and its model.",
        "Name it, choose the route, then wake the first thread.",
    ),
)



from .cli_main_support import *  # noqa: F401,F403

def _default_personality_preset(runtime: CliRuntime, *, mode: str, current: str | None = None) -> str | None:
    if mode != "companion":
        return None
    if current:
        return current
    for preset in runtime.personality_presets():
        if preset.preset_id == "companion":
            return preset.preset_id
    return runtime.personality_presets()[0].preset_id

def _print_birth_wizard_intro() -> None:
    if not RICH_AVAILABLE or Table is None or Panel is None or Group is None:
        _print_heading("Elephant Agent Init", "Bring a personal AI online around your work, preferences, and context.")
        for line in INIT_REFLECTION_LINES:
            _print_bullet(line)
        _print_bullet("Then name the Elephant Agent, choose the model and recall path, and optionally wire IM.")
        return
    console = Console(highlight=False, soft_wrap=True)
    questions = Text()
    questions.append("Stage 0: begin with a blank elephant\n", style=f"bold {BRAND_LIGHT}")
    questions.append(
        "Init is not a personality quiz or a database dump. It only gives Elephant Agent enough signal to start the first reply with the right person in view.\n\n",
        style=BRAND_MUTED,
    )
    for line in INIT_REFLECTION_LINES:
        questions.append(f"• {line}\n", style=BRAND_LIGHT)

    flow = Text()
    flow.append("What will happen\n", style=f"bold {BRAND_ACCENT}")
    for label, detail in INIT_SETUP_STEPS:
        flow.append(f"{label}\n", style=f"bold {BRAND_LIGHT}")
        flow.append(f"    {detail}\n", style=BRAND_MUTED)

    brand = Text(justify="center", no_wrap=True)
    brand.append("STAGE 0\n", style=f"bold {BRAND_ACCENT}")
    brand.append("the elephant before recall\n\n", style=BRAND_MUTED)

    layout = Table.grid(expand=True)
    console_width = getattr(console.size, "width", 0)
    if console_width and console_width < 132:
        layout.add_column(ratio=1, min_width=48)
        layout.add_row(_center_brand_block(render_stage_zero_elephant_mark()))
        layout.add_row(_center_brand_block(Text("STAGE 0 · Elephant Agent Init", style=f"bold {BRAND_ACCENT}")))
        layout.add_row(Text(" "))
        layout.add_row(questions)
        layout.add_row(Text(" "))
        layout.add_row(flow)
    else:
        layout.add_column(ratio=5, min_width=24)
        layout.add_column(ratio=14, min_width=54)
        layout.add_column(ratio=10, min_width=42)
        logo_block = Table.grid(expand=True)
        logo_block.add_column()
        logo_block.add_row(_center_brand_block(brand))
        logo_block.add_row(_center_brand_block(render_stage_zero_elephant_mark()))
        layout.add_row(_center_brand_block(logo_block), questions, flow)
    console.print(
        _center_intro_window(Panel(
            layout,
            title=f"[bold {BRAND_ACCENT}]Elephant Agent Init · Stage 0 → first wake · v{_resolve_elephant_version()}[/bold {BRAND_ACCENT}]",
            border_style=BRAND_ACCENT,
            expand=False,
            padding=(1, 2),
        ))
    )


_INIT_WELCOME_VARIANTS = (
    {
        "title": "Elephant Agent",
        "language": "English",
        "glyph": "🫂",
        "slogan": "🕯️  Intelligence carries us farther; understanding gives us a place to return.",
        "lines": (
            "☁️  Everyone carries weather not yet named.",
            "Elephant Agent begins by seeing it.",
            "Your words belong to you first.",
            "Then they become clues for care.",
            "🌱  They grow in conversation, lighting the next step.",
        ),
        "enter": "Press Enter to step into Elephant Agent's world.",
    },
    {
        "title": "开始之前",
        "language": "中文",
        "glyph": "🕯️",
        "slogan": "🕯️  智能让我们抵达远方，理解让我们有处可归。",
        "lines": (
            "☁️  每个人心里都有未命名的天气。",
            "Elephant Agent 先从看见它开始。",
            "这些话先属于你。",
            "然后才成为 Elephant Agent 理解你的线索。",
            "🌱  它们会在对话里生长，照见你，也照见下一步。",
        ),
        "enter": "按 Enter 进入 Elephant Agent 的世界。",
    },
    {
        "title": "Avant de commencer",
        "language": "Français",
        "glyph": "🏠",
        "slogan": "🕯️  L'intelligence avance; la mémoire nous ramène.",
        "lines": (
            "☁️  Chacun porte une meteo sans nom.",
            "Elephant Agent commence par la voir.",
            "Ces mots t'appartiennent d'abord.",
            "Puis ils deviennent des indices pour Elephant Agent.",
            "🌱  Ils grandissent et eclairent le prochain pas.",
        ),
        "enter": "Appuie sur Enter pour entrer dans le monde d'Elephant Agent.",
    },
    {
        "title": "시작하기 전에",
        "language": "한국어",
        "glyph": "🫂",
        "slogan": "🕯️  지능은 멀리 데려가고, 기억은 돌아올 곳을 줍니다.",
        "lines": (
            "☁️  누구에게나 아직 이름 없는 마음의 날씨가 있습니다.",
            "Elephant Agent 은 그것을 보는 데서 시작합니다.",
            "이 말들은 먼저 당신의 것입니다.",
            "그다음에야 Elephant Agent 이 당신을 이해하는 단서가 됩니다.",
            "🌱  대화 속에서 자라며 다음 걸음을 비춰 줍니다.",
        ),
        "enter": "Enter 를 눌러 Elephant Agent 의 세계로 들어가세요.",
    },
    {
        "title": "Antes de empezar",
        "language": "Español",
        "glyph": "🕯️",
        "slogan": "🕯️  La inteligencia avanza; la memoria nos devuelve a casa.",
        "lines": (
            "☁️  Cada persona lleva un clima sin nombre.",
            "Elephant Agent empieza por verlo.",
            "Tus palabras te pertenecen primero.",
            "Luego se vuelven pistas para Elephant Agent.",
            "🌱  Crecen e iluminan el proximo paso.",
        ),
        "enter": "Pulsa Enter para entrar en el mundo de Elephant Agent.",
    },
)


def _init_welcome_variant(variant_index: int) -> tuple[str, str, str, str, tuple[str, ...], str]:
    variant = _INIT_WELCOME_VARIANTS[variant_index % len(_INIT_WELCOME_VARIANTS)]
    return (
        str(variant["title"]),
        str(variant["language"]),
        str(variant["glyph"]),
        str(variant["slogan"]),
        tuple(str(line) for line in variant["lines"]),
        str(variant["enter"]),
    )


def _init_welcome_plain_text(variant_index: int) -> str:
    _title, language, glyph, slogan, lines, enter = _init_welcome_variant(variant_index)
    return "\n".join((f"Elephant Agent · {language}", glyph, "", slogan, "", *lines, "", enter))


def _init_welcome_frame(variant_index: int):
    _title, language, glyph, slogan, lines, enter = _init_welcome_variant(variant_index)
    if Table is None or Panel is None or Text is None:
        return _init_welcome_plain_text(variant_index)
    body = Table.grid(expand=True)
    body.add_column()
    body.add_row(_center_brand_block(render_stage_zero_elephant_mark()))
    body.add_row(Text(" "))
    copy = Text(justify="center", no_wrap=True)
    copy.append("Elephant Agent · ", style=BRAND_MUTED)
    copy.append(language + "\n", style=f"bold {BRAND_LIGHT}")
    copy.append(glyph + "\n\n", style=f"bold {BRAND_ACCENT_STRONG}")
    copy.append(slogan + "\n\n", style=f"bold {BRAND_LIGHT}")
    for index, line in enumerate(lines):
        style = f"bold {BRAND_ACCENT_STRONG}" if index == 0 else BRAND_LIGHT
        if "Elephant Agent" not in line:
            copy.append(line + "\n", style=style)
            continue
        prefix, suffix = line.split("Elephant Agent", 1)
        copy.append(prefix, style=style)
        copy.append("Elephant Agent", style=f"bold {BRAND_LIGHT}")
        copy.append(suffix + "\n", style=style)
    indicator = " ".join("●" if index == variant_index % len(_INIT_WELCOME_VARIANTS) else "·" for index in range(len(_INIT_WELCOME_VARIANTS)))
    copy.append("\n" + indicator + "\n", style=BRAND_MUTED)
    copy.append(enter + "\n", style=f"bold {BRAND_LIGHT}")
    body.add_row(_center_brand_block(copy))
    return _center_intro_window(Panel(
        body,
        subtitle=f"[bold {BRAND_ACCENT}]Enter to begin[/bold {BRAND_ACCENT}]",
        subtitle_align="center",
        border_style=BRAND_DARK,
        expand=True,
        padding=(1, 3),
        width=92,
        height=28,
    ))


def _prompt_init_welcome_gate() -> bool:
    if not _interactive_shell_supported():
        return True
    if (
        not RICH_AVAILABLE
        or Live is None
        or Console is None
        or Table is None
        or Panel is None
        or Text is None
        or os.environ.get("ELEPHANT_NO_ANIMATION") == "1"
    ):
        _print_heading("Elephant Agent", _init_welcome_plain_text(0))
        try:
            input()
        except (KeyboardInterrupt, EOFError):
            return False
        return True
    console = Console(highlight=False, soft_wrap=True)
    frame_index = 0
    next_switch = time.monotonic() + 4.2
    with Live(
        _init_welcome_frame(frame_index),
        console=console,
        refresh_per_second=8,
        screen=True,
        transient=False,
    ) as live:
        while True:
            try:
                ready, _, _ = select.select([sys.stdin], [], [], 0.1)
            except (OSError, ValueError):
                ready = []
            if ready:
                try:
                    sys.stdin.readline()
                except (KeyboardInterrupt, EOFError):
                    return False
                return True
            if time.monotonic() >= next_switch:
                frame_index = (frame_index + 1) % len(_INIT_WELCOME_VARIANTS)
                live.update(_init_welcome_frame(frame_index))
                next_switch = time.monotonic() + 4.2


def _birth_intro_frame(tick: int, total_ticks: int):
    if Table is None or Panel is None or Text is None:
        return "Elephant Agent Stage 0: begin with a blank elephant."
    progress = min(1.0, (tick + 1) / max(total_ticks, 1))
    stage_index = min(len(INIT_ANIMATION_STAGES) - 1, int(progress * len(INIT_ANIMATION_STAGES)))
    stage_title, stage_line, stage_detail = INIT_ANIMATION_STAGES[stage_index]
    step_index = min(len(INIT_SETUP_STEPS) - 1, max(0, int(progress * len(INIT_SETUP_STEPS))))

    logo = Table.grid(expand=True)
    logo.add_column()
    logo.add_row(_center_brand_block(render_stage_zero_elephant_mark()))
    logo_caption = Text(justify="center", no_wrap=True)
    logo_caption.append("STAGE 0\n", style=f"bold {BRAND_ACCENT}")
    logo_caption.append("blank elephant · no assumptions", style=BRAND_MUTED)
    logo.add_row(_center_brand_block(logo_caption))

    prompt = Text()
    prompt.append(f"{stage_title}\n", style=f"bold {BRAND_ACCENT_STRONG}")
    prompt.append(f"{stage_line}\n", style=f"bold {BRAND_LIGHT}")
    prompt.append(stage_detail, style=BRAND_MUTED)

    progress_bar = Text(justify="center", no_wrap=True)
    for index, (label, _) in enumerate(INIT_SETUP_STEPS):
        short_label = label.split("  ", 1)[-1]
        is_active = index == step_index
        is_done = index < step_index
        style = f"bold {BRAND_LIGHT}" if is_active else (BRAND_ACCENT if is_done else BRAND_MUTED)
        marker = "●" if is_active else ("•" if is_done else "·")
        progress_bar.append(f"{marker} {short_label}", style=style)
        if index < len(INIT_SETUP_STEPS) - 1:
            progress_bar.append("  ─  ", style=BRAND_DARK)

    active_detail = Text(justify="center")
    active_detail.append("Now setting up: ", style=BRAND_MUTED)
    active_detail.append(INIT_SETUP_STEPS[step_index][0].split("  ", 1)[-1], style=f"bold {BRAND_LIGHT}")
    active_detail.append(f" — {INIT_SETUP_STEPS[step_index][1]}", style=BRAND_MUTED)

    body = Table.grid(expand=True)
    body.add_column()
    body.add_row(_center_brand_block(logo))
    body.add_row(Text(" "))
    body.add_row(_center_brand_block(prompt))
    body.add_row(Text(" "))
    body.add_row(_center_brand_block(progress_bar))
    body.add_row(_center_brand_block(active_detail))

    viewport_width, _ = _intro_console_size()
    panel_width = None
    if viewport_width >= 80:
        panel_width = min(88, max(66, viewport_width - 16))
    return _center_intro_window(Panel(
        body,
        title=f"[bold {BRAND_ACCENT}]Elephant Agent Init · Stage 0 → first wake[/bold {BRAND_ACCENT}]",
        border_style=BRAND_ACCENT,
        expand=False,
        padding=(1, 2),
        width=panel_width,
    ))


def _intro_console_size() -> tuple[int, int]:
    if Console is None:
        return (0, 0)
    try:
        size = Console(highlight=False, soft_wrap=True).size
    except Exception:
        return (0, 0)
    return (getattr(size, "width", 0), getattr(size, "height", 0))


def _center_intro_window(renderable):
    if Align is None:
        return renderable
    _, height = _intro_console_size()
    try:
        if height > 0:
            return Align(renderable, align="center", vertical="middle", height=max(22, height - 1))
        return Align.center(renderable, vertical="middle")
    except TypeError:
        return Align.center(renderable)


def _play_birth_intro_animation() -> None:
    if (
        not RICH_AVAILABLE
        or Live is None
        or Console is None
        or os.environ.get("ELEPHANT_NO_ANIMATION") == "1"
        or not _interactive_shell_supported()
    ):
        return
    try:
        seconds = float(os.environ.get("ELEPHANT_INIT_INTRO_SECONDS", "2.0"))
    except ValueError:
        seconds = 2.0
    seconds = min(4.0, max(1.0, seconds))
    total_ticks = max(8, int(seconds * 4))
    try:
        settle_seconds = float(os.environ.get("ELEPHANT_INIT_INTRO_SETTLE", "0.2"))
    except ValueError:
        settle_seconds = 0.2
    settle_seconds = max(0.0, min(0.8, settle_seconds))
    console = Console(highlight=False, soft_wrap=True)
    with Live(
        _birth_intro_frame(0, total_ticks),
        console=console,
        refresh_per_second=8,
        screen=True,
        transient=True,
    ) as live:
        for tick in range(total_ticks):
            live.update(_birth_intro_frame(tick, total_ticks))
            time.sleep(seconds / total_ticks)
        # Hold the final frame briefly so the create has time to land
        # before the wizard questions begin.
        if settle_seconds > 0:
            live.update(_birth_intro_frame(total_ticks - 1, total_ticks))
            time.sleep(settle_seconds)


def _transition_text(language: str, english: str, chinese: str) -> str:
    return chinese if str(language or "").strip().lower().startswith("zh") else english


def _after_personal_transition_frame(language: str, tick: int, total_ticks: int):
    if Table is None or Panel is None or Text is None:
        return _transition_text(language, "Only a few steps left.", "只差几步了。")
    progress = min(1.0, (tick + 1) / max(total_ticks, 1))
    filled = max(1, int(progress * 18))
    bar = "●" * filled + "·" * (18 - filled)
    body = Table.grid(expand=True)
    body.add_column()
    headline = Text(justify="center")
    headline.append(_transition_text(language, "Only a few steps left\n", "只差几步了\n"), style=f"bold {BRAND_ACCENT_STRONG}")
    headline.append(
        _transition_text(
            language,
            "Your personal anchors are in place. Next: name the Elephant Agent, choose the model, then wire IM.",
            "你的个人锚点已经放好。接下来：给 Elephant Agent 起名、选择模型，然后按需配置 IM。",
        ),
        style=BRAND_LIGHT,
    )
    progress_line = Text(justify="center", no_wrap=True)
    progress_line.append(bar, style=BRAND_ACCENT)
    caption = Text(justify="center")
    caption.append(_transition_text(language, "Personal pass complete → Elephant + model setup", "个人信息完成 → Elephant 与模型配置"), style=BRAND_MUTED)
    body.add_row(_center_brand_block(render_stage_zero_elephant_mark()))
    body.add_row(Text(" "))
    body.add_row(_center_brand_block(headline))
    body.add_row(Text(" "))
    body.add_row(_center_brand_block(progress_line))
    body.add_row(_center_brand_block(caption))
    return _center_intro_window(Panel(
        body,
        title=f"[bold {BRAND_ACCENT}]path nearly ready[/bold {BRAND_ACCENT}]",
        border_style=BRAND_DARK,
        expand=False,
        padding=(1, 3),
        width=92,
        height=28,
    ))


def _play_after_personal_transition(language: str = "en") -> None:
    if (
        not RICH_AVAILABLE
        or Live is None
        or Console is None
        or os.environ.get("ELEPHANT_NO_ANIMATION") == "1"
        or not _interactive_shell_supported()
    ):
        _print_heading(
            _transition_text(language, "Only a few steps left", "只差几步了"),
            _transition_text(
                language,
                "Personal anchors are in place. Next: name the Elephant Agent, choose the model, then wire IM.",
                "个人锚点已经放好。接下来给 Elephant Agent 起名、选择模型，然后按需配置 IM。",
            ),
        )
        return
    try:
        seconds = float(os.environ.get("ELEPHANT_INIT_TRANSITION_SECONDS", "1.4"))
    except ValueError:
        seconds = 1.4
    seconds = min(3.0, max(0.8, seconds))
    total_ticks = max(6, int(seconds * 5))
    console = Console(highlight=False, soft_wrap=True)
    with Live(
        _after_personal_transition_frame(language, 0, total_ticks),
        console=console,
        refresh_per_second=10,
        screen=True,
        transient=True,
    ) as live:
        for tick in range(total_ticks):
            live.update(_after_personal_transition_frame(language, tick, total_ticks))
            time.sleep(seconds / total_ticks)


def _prompt_first_elephant_name(default_name: str, *, allow_back: bool = False) -> str | _WizardBackSignal:
    return _wizard_text_prompt(
        "Name Your First Elephant Agent",
        "This first Elephant Agent is yours. What name feels right?",
        default=default_name,
        allow_back=allow_back,
    )

def _run_interactive_elephant_wizard(
    runtime: CliRuntime,
    *,
    elephant_name: str | None,
) -> str | None:
    current_elephant_name = elephant_name or _suggest_elephant_name(runtime)
    answer = _wizard_text_prompt(
        "Name Another Elephant Agent",
        "What should this new Elephant Agent be called?",
        default=current_elephant_name,
        allow_back=True,
    )
    if answer is WIZARD_BACK:
        return None
    return str(answer).strip() or current_elephant_name

def _run_interactive_birth_wizard(
    runtime: CliRuntime,
    *,
    display_name: str,
    provider_state: ProviderSelectionState,
) -> BirthWizardState | None:
    state = BirthWizardState(
        display_name=display_name,
        provider_id=provider_state.provider_id,
        base_url=provider_state.base_url,
        model_id=provider_state.model_id,
        api_key=provider_state.api_key,
        embedding_provider="local",
        embedding_source="huggingface",
        embedding_base_url="",
        embedding_model="",
        embedding_dimensions=None,
        embedding_api_key=None,
        reasoning_effort=provider_state.reasoning_effort,
        context_window_mode=provider_state.context_window_mode,
        context_window_tokens=provider_state.context_window_tokens,
    )
    steps = ("display_name", "provider_setup")
    step_index = 0
    while step_index < len(steps):
        step = steps[step_index]
        if step == "display_name":
            answer = _prompt_first_elephant_name(state.display_name, allow_back=True)
            if answer is WIZARD_BACK:
                return None
            state.display_name = str(answer).strip() or state.display_name
            step_index += 1
            continue
        if step == "provider_setup":
            answer = run_provider_selection_wizard(
                runtime,
                initial_state=ProviderSelectionState(
                    provider_id=state.provider_id,
                    base_url=state.base_url,
                    api_key=state.api_key,
                    model_id=state.model_id,
                    reasoning_effort=state.reasoning_effort,
                    context_window_mode=state.context_window_mode,
                    context_window_tokens=state.context_window_tokens,
                ),
                allow_back=True,
            )
            if answer is WIZARD_BACK or answer is WIZARD_CANCEL:
                return None
            state.provider_id = answer.provider_id
            state.base_url = answer.base_url
            state.api_key = answer.api_key
            state.model_id = answer.model_id
            state.reasoning_effort = answer.reasoning_effort
            state.context_window_mode = answer.context_window_mode
            state.context_window_tokens = answer.context_window_tokens
            step_index += 1
            continue
    return state

def _print_birth_paused() -> None:
    _print_cli_card(
        "Elephant Agent birth paused",
        "No new identity or provider changes were written.",
        next_commands=("elephant init", "elephant status"),
    )

def _gateway_birth_lines(elephant_name: str) -> tuple[str, ...]:
    return (
        "wire IM · elephant gateway setup",
        "inspect readiness · elephant gateway doctor",
        "inspect skill packages · elephant skills",
        "launch operator dashboard · elephant dashboard --dry-run",
    )

def _prompt_im_onboarding(runtime: CliRuntime, *, elephant_name: str) -> None:
    from apps.gateway.__main__ import run_im_setup

    run_im_setup(
        default_state_dir=runtime.paths.state_dir,
        default_control_state_dir=runtime.paths.state_dir,
        prompt_title="💬 IM Setup",
        prompt_text="💬 Which IM should Elephant Agent wire before wake opens?",
        allow_skip=True,
    )

def _print_overview(runtime: CliRuntime) -> None:
    provider = dict(runtime.provider_summary())
    doctor = runtime.provider_doctor()
    herd = runtime.list_herd(limit=5)
    if RICH_AVAILABLE and Table is not None and Panel is not None and Group is not None:
        console = Console(highlight=False, soft_wrap=True)
        brand = Table.grid(expand=True)
        brand.add_column(no_wrap=True)
        headline = Text(no_wrap=True)
        headline.append("Your Elephant Agent is awake\n", style=f"bold {BRAND_LIGHT}")
        headline.append("Still steady — and now, still yours.", style=BRAND_MUTED)
        capability = Text("You · Threads · Herd · Skills · Providers", style=BRAND_MUTED)
        action_lines = Text()
        action_lines.append("Start\n", style=f"bold {BRAND_ACCENT}")
        action_lines.append(f"{_format_command_line('elephant wake', 'continue the active thread')}\n", style=BRAND_LIGHT)
        action_lines.append(f"{_format_command_line('elephant init', 'set name, provider, model, and recall path')}\n", style=BRAND_LIGHT)
        action_lines.append(f"{_format_command_line('elephant herd new <name>', 'create another named continuity thread')}\n", style=BRAND_LIGHT)
        action_lines.append(f"{_format_command_line('elephant herd', 'inspect named continuity threads')}\n", style=BRAND_LIGHT)
        action_lines.append(f"{_format_command_line('elephant dashboard', 'open the continuity console')}\n", style=BRAND_LIGHT)
        action_lines.append("\nSystem controls\n", style=f"bold {BRAND_ACCENT}")
        action_lines.append(f"{_format_command_line('elephant provider', 'manage models, keys, context, and embeddings')}\n", style=BRAND_LIGHT)
        action_lines.append(f"{_format_command_line('elephant skills', 'inspect, install, search, and toggle skills')}\n", style=BRAND_LIGHT)
        action_lines.append(f"{_format_command_line('elephant gateway', 'bind messenger surfaces')}\n", style=BRAND_LIGHT)
        action_lines.append(f"{_format_command_line('elephant status', 'check provider and recall readiness')}\n", style=BRAND_LIGHT)
        action_lines.append("\nCurrent install\n", style=f"bold {BRAND_ACCENT}")
        action_lines.append(f"readiness · {doctor['status']}\n", style=BRAND_MUTED if doctor["status"] != "ready" else BRAND_LIGHT)
        action_lines.append(f"provider · {provider['provider_id']}\n", style=BRAND_MUTED)
        if provider.get("model_id") or provider.get("default_model"):
            action_lines.append(f"model · {provider.get('model_id') or provider.get('default_model')}\n", style=BRAND_MUTED)
        if herd:
            action_lines.append("states · " + ", ".join(elephant.elephant_id for elephant in herd), style=BRAND_MUTED)
        else:
            action_lines.append("states · none yet", style=BRAND_MUTED)
        brand.add_row(_center_brand_block(headline))
        brand.add_row(Text(" "))
        brand.add_row(_center_brand_block(_render_cli_banner_mark()))
        brand.add_row(Text(" "))
        brand.add_row(_center_brand_block(capability))
        layout = Table.grid(expand=True)
        console_width = getattr(console.size, "width", 0)
        if console_width and console_width < 132:
            layout.add_column(ratio=1, min_width=48)
            compact_brand = Table.grid(expand=True)
            compact_brand.add_column(no_wrap=True)
            compact_brand.add_row(_center_brand_block(headline))
            compact_brand.add_row(Text(" "))
            compact_brand.add_row(_center_brand_block(capability))
            layout.add_row(compact_brand)
            layout.add_row(Text(" "))
            layout.add_row(action_lines)
        else:
            layout.add_column(ratio=11, min_width=46)
            layout.add_column(ratio=11, min_width=44)
            layout.add_row(brand, action_lines)
        console.print(
            Panel(
                layout,
                title=f"[bold {BRAND_ACCENT}]Elephant Agent v{_resolve_elephant_version()}[/bold {BRAND_ACCENT}]",
                subtitle=f"[bold {BRAND_LIGHT}]You stay at the center. Everything else grows around that.[/bold {BRAND_LIGHT}]",
                border_style=BRAND_ACCENT,
                padding=(1, 2),
            )
        )
        return

    _print_heading("Your Elephant Agent is awake", "Still steady — and now, still yours.")
    _print_bullet("You · Threads · Herd · Skills · Providers")
    _print_command_line("elephant wake", "continue the active thread")
    _print_command_line("elephant init", "set name, provider, model, and recall path")
    _print_command_line("elephant herd new <name>", "create another named continuity thread")
    _print_command_line("elephant herd", "inspect named continuity threads")
    _print_command_line("elephant dashboard", "open the continuity console")
    _print_command_line("elephant provider", "manage models, keys, context, and embeddings")
    _print_command_line("elephant skills", "inspect, install, search, and toggle skills")
    _print_command_line("elephant gateway", "bind messenger surfaces")
    _print_command_line("elephant status", "check provider and recall readiness")
    _print_field("readiness", doctor["status"])
    _print_field("provider", provider["provider_id"])
    if provider.get("model_id") or provider.get("default_model"):
        _print_field("model", provider.get("model_id") or provider.get("default_model"))
    _print_field("states", ", ".join(elephant.elephant_id for elephant in herd) if herd else "none yet")

def _center_brand_block(renderable):
    if Align is None:
        return renderable
    return Align.center(renderable)

def _print_setup_intro(runtime: CliRuntime, *, provider_id: str) -> None:
    guide = runtime.provider_setup_guide(provider_id)
    loaded = runtime.current_profile()
    _print_cli_card(
        "Elephant Agent init",
        "Open the first thread of an Elephant Agent that will stay with you.",
        sections=(
            CliCardSection(
                "Current setup",
                (
                    f"name · {loaded.state.display_name}",
                    f"provider · {guide.display_name}",
                    f"transport · {guide.transport_display_name}",
                ),
            ),
            CliCardSection(
                "Init will set",
                (
                    "who this Elephant Agent is learning with",
                    "which dialogue model answers the first Episode",
                    "whether semantic recall uses elephant-embed or an embedding provider",
                    "which elephant wake should open first",
                ),
            ),
        ),
    )

def _default_born_args() -> argparse.Namespace:
    return argparse.Namespace(
        provider_id=DEFAULT_PROVIDER_ID,
        display_name=None,
        elephant_identity_text=None,
        elephant_name=None,
        base_url=None,
        model_id=None,
        api_key=None,
        context_window_mode=None,
        context_window=None,
        preferred_name=None,
        age=None,
        birth_date=None,
        gender=None,
        occupation=None,
        city=None,
        mbti=None,
        hobbies=None,
        safety_boundaries=None,
        non_interactive=False,
    )

def _default_grow_args() -> argparse.Namespace:
    return argparse.Namespace(
        elephant_id=None,
        debug=False,
        message=None,
    )

def _ensure_elephant_ready(
    runtime: CliRuntime,
    *,
    elephant_name: str,
    display_name: str,
    profile_id: str,
) -> tuple[object, str]:
    existing = runtime.latest_session_for_elephant(elephant_name)
    if existing is not None:
        return existing, "existing"
    session = runtime.create_elephant(
        elephant_id=elephant_name,
        profile_id=profile_id,
        display_name=display_name,
        mode="companion",
    )
    return session, "created"

__all__ = [
    "DEFAULT_PROVIDER_ID",
    "DEFAULT_ELEPHANT_NAME_SUGGESTIONS",
    "CLI_THEME_TITLE_GLYPH",
    "CLI_THEME_BULLET",
    "CLI_THEME_WELCOME_GLYPH",
    "CLI_THEME_SUBTITLE",
    "_default_personality_preset",
    "_play_birth_intro_animation",
    "_print_birth_wizard_intro",
    "_prompt_init_welcome_gate",
    "_play_after_personal_transition",
    "_prompt_first_elephant_name",
    "_run_interactive_elephant_wizard",
    "_run_interactive_birth_wizard",
    "_print_birth_paused",
    "_gateway_birth_lines",
    "_prompt_im_onboarding",
    "_print_overview",
    "_center_brand_block",
    "_print_setup_intro",
    "_default_born_args",
    "_default_grow_args",
    "_ensure_elephant_ready",
]
