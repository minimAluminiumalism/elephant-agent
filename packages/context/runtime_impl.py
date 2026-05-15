"""Layered context runtime implementation assembled from smaller modules."""


from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
from typing import Any, Mapping, Protocol, runtime_checkable

from packages.capabilities.runtime import CapabilityDescriptor, ContextCapability
from packages.contracts.layers import Episode
from packages.contracts.runtime import ContextBundle, StateFocusDecision, MemoryRecord, StructuredTurnSlot
from packages.evidence import parse_structured_turn_memory



from .runtime_types import (
    ContextAssemblyPlan,
    ContextAssemblyResult,
    ContextBudgetPlan,
    ContextBudgetRequest,
    ContextLayerBudget,
    ContextLayerSnapshot,
    ContextRetrievalRequest,
    ContextSourceTrace,
    ContextSummaryRequest,
    EpisodeReplay,
    EpisodeFrame,
    StateSnapshot,
    EpisodeFrozenContext,
    LoopContext,
    RequestAttachments,
)
from .runtime_layers import (
    BudgetManager,
    ContextPlanner,
    DeterministicBudgetManager,
    DeterministicRetrievalScheduler,
    DeterministicSummaryHook,
    MarkdownPromptRenderer,
    PromptRenderer,
    RetrievalScheduler,
    EpisodeFrameBuilder,
    SummaryHook,
    build_prompt_envelope,
)
from .runtime_support import (
    _budget_for,
    _work_item_line,
    _memory_line,
    _select_steady_memories,
    _steady_memory_refs,
    _work_item_trace_reason,
    _derived_source_refs,
    _loop_context_trace_reason,
    _session_snapshot_trace_reason,
    _request_attachment_trace_reason,
    _session_snapshot_lines,
    _build_retrieval_query,
    _build_retrieval_reason,
    _estimate_tokens,
    _state_focus_budget_multiplier,
    _truncate_lines,
    _summary_content_for_layer,
    _retrieval_lines,
    _ReplayRequestSpec,
    _split_retrieval_requests,
    _infer_replay_specs,
    _schedule_replay_requests,
    _select_replay_memory,
    _replay_rank,
    _project_replay_slot,
    _replay_lines,
    _replay_summary_lines,
    _replay_packet_trace_reason,
    _tokenize,
    _thematic_tokens,
    _continuity_marker_tokens,
    _context_memory_score,
    _retrieval_priority_bucket,
    _plan_rationale,
    _snapshot_work_items,
)

class LayeredContextPlanner:
    """Plan the layered context structure from runtime state."""

    def __init__(
        self,
        budget_manager: BudgetManager | None = None,
        summary_hook: SummaryHook | None = None,
        retrieval_scheduler: RetrievalScheduler | None = None,
    ) -> None:
        self._budget_manager = budget_manager or DeterministicBudgetManager()
        self._summary_hook = summary_hook or DeterministicSummaryHook()
        self._retrieval_scheduler = retrieval_scheduler or DeterministicRetrievalScheduler()

    def plan(
        self,
        *,
        session: Episode,
        work_items: tuple[...],
        memories: tuple[MemoryRecord, ...],
        total_tokens: int,
        instruction_refs: tuple[str, ...],
        recent_loop_context: tuple[str, ...],
        state_focus: StateFocusDecision | None = None,
        profile_snapshot_refs: tuple[str, ...] = (),
        artifacts: tuple[str, ...] = (),
    ) -> ContextAssemblyPlan:
        requests = self._build_budget_requests(
            session,
            work_items,
            memories,
            instruction_refs,
            recent_loop_context,
            state_focus,
            profile_snapshot_refs,
            artifacts,
        )
        budgets = self._budget_manager.allocate(total_tokens, requests)
        retrieval_requests = self._retrieval_scheduler.schedule(
            session=session,
            work_items=work_items,
            memories=memories,
            recent_loop_context=recent_loop_context,
            token_budget=max(
                self._snapshot_retrieval_budget(budgets, state_focus=state_focus),
                self._suggest_retrieval_budget(memories, state_focus=state_focus),
                max(total_tokens - budgets.allocated_tokens, 0),
            ),
            budget_plan=budgets,
            state_focus=state_focus,
        )
        summary_requests = self._build_summary_requests(
            session,
            budgets,
            work_items,
            memories,
            recent_loop_context,
            state_focus,
            profile_snapshot_refs,
            retrieval_requests,
        )
        source_trace = self._build_source_trace(
            session=session,
            work_items=work_items,
            memories=memories,
            instruction_refs=instruction_refs,
            state_focus=state_focus,
            profile_snapshot_refs=profile_snapshot_refs,
            recent_loop_context=recent_loop_context,
            artifacts=artifacts,
            summary_requests=summary_requests,
            retrieval_requests=retrieval_requests,
        )
        rationale = _plan_rationale(session, work_items, memories, budgets, retrieval_requests, state_focus=state_focus)
        frame = EpisodeFrameBuilder().build(
            session=session,
            instruction_refs=instruction_refs,
            profile_snapshot_refs=profile_snapshot_refs,
            work_items=work_items,
            memories=memories,
            recent_loop_context=recent_loop_context,
            request_attachments=artifacts,
            budgets=budgets,
            summary_requests=summary_requests,
            retrieval_requests=retrieval_requests,
            rationale=rationale,
            source_trace=source_trace,
            state_focus=state_focus,
        )
        return ContextAssemblyPlan(
            session_id=session.episode_id,
            profile_id=session.personal_model_id,
            total_tokens=total_tokens,
            layers=frame.layers(),
            budgets=budgets,
            summary_requests=summary_requests,
            retrieval_requests=retrieval_requests,
            frame=frame,
            rationale=rationale,
            source_trace=source_trace,
        )

    def _build_budget_requests(
        self,
        session: Episode,
        work_items: tuple[...],
        memories: tuple[MemoryRecord, ...],
        instruction_refs: tuple[str, ...],
        recent_loop_context: tuple[str, ...],
        state_focus: StateFocusDecision | None,
        profile_snapshot_refs: tuple[str, ...],
        artifacts: tuple[str, ...],
    ) -> tuple[ContextBudgetRequest, ...]:
        stable_prefix_tokens = max(48, len(instruction_refs) * 8)
        snapshot_work_items = _snapshot_work_items(work_items, state_focus=state_focus)
        snapshot_tokens = max(
            96,
            int(
                max(144, len(profile_snapshot_refs) * 6 + len(snapshot_work_items) * 28 + min(len(memories), 6) * 24)
                * _state_focus_budget_multiplier(state_focus)
            ),
        )
        loop_context_tokens = max(64, len(recent_loop_context) * 18)
        attachment_tokens = sum(_estimate_tokens(line) for line in artifacts)
        replay_specs = _infer_replay_specs(recent_loop_context, state_focus=state_focus)
        requests: list[ContextBudgetRequest] = [
            ContextBudgetRequest(
                layer_name="stable_prefix",
                desired_tokens=stable_prefix_tokens,
                minimum_tokens=24,
                required=True,
                priority=100,
                source_refs=instruction_refs,
            ),
            ContextBudgetRequest(
                layer_name="session_snapshot",
                desired_tokens=snapshot_tokens,
                minimum_tokens=64,
                required=True,
                priority=90,
                source_refs=tuple(
                    dict.fromkeys(
                        (
                            *profile_snapshot_refs,
                            *(work_item.work_item_id for work_item in snapshot_work_items),
                            *(memory.memory_id for memory in memories),
                        )
                    )
                ),
            ),
        ]
        if recent_loop_context:
            requests.append(
                ContextBudgetRequest(
                    layer_name="loop_context",
                    desired_tokens=loop_context_tokens,
                    minimum_tokens=24,
                    required=False,
                    priority=80,
                    source_refs=tuple(f"loop:{index}" for index, _ in enumerate(recent_loop_context, start=1)),
                )
            )
        if replay_specs:
            requests.append(
                ContextBudgetRequest(
                    layer_name="replay_packet",
                    desired_tokens=sum(spec.desired_tokens for spec in replay_specs),
                    minimum_tokens=min(48, sum(spec.minimum_tokens for spec in replay_specs)),
                    required=False,
                    priority=70,
                    source_refs=tuple(work_item.work_item_id for work_item in snapshot_work_items)
                    or tuple(spec.slot_name for spec in replay_specs),
                )
            )
        if artifacts:
            requests.append(
                ContextBudgetRequest(
                    layer_name="request_attachments",
                    desired_tokens=attachment_tokens,
                    minimum_tokens=0,
                    required=False,
                    priority=20,
                    source_refs=_derived_source_refs("attachment", artifacts),
                )
            )
        return tuple(requests)

    def _build_summary_requests(
        self,
        session: Episode,
        budgets: ContextBudgetPlan,
        work_items: tuple[...],
        memories: tuple[MemoryRecord, ...],
        recent_loop_context: tuple[str, ...],
        state_focus: StateFocusDecision | None,
        profile_snapshot_refs: tuple[str, ...],
        retrieval_requests: tuple[ContextRetrievalRequest, ...],
    ) -> tuple[ContextSummaryRequest, ...]:
        requests: list[ContextSummaryRequest] = []
        snapshot_work_items = _snapshot_work_items(work_items, state_focus=state_focus)
        snapshot_retrieval_requests, replay_retrieval_requests = _split_retrieval_requests(retrieval_requests)
        snapshot_budget = budgets.allocation_for("session_snapshot")
        if snapshot_budget:
            requests.append(
                ContextSummaryRequest(
                    layer_name="session_snapshot",
                    source_refs=tuple(
                        dict.fromkeys(
                            (
                                *profile_snapshot_refs,
                                *(work_item.work_item_id for work_item in snapshot_work_items),
                                *(memory.memory_id for memory in memories),
                            )
                        )
                    ),
                    token_budget=snapshot_budget.allocated_tokens,
                    reason="compress the rebuildable session snapshot while keeping profile, work, and evidence slices inspectable",
                    required=True,
                )
            )
        replay_budget = budgets.allocation_for("replay_packet")
        if replay_budget and replay_retrieval_requests and (
            replay_budget.allocated_tokens < replay_budget.requested_tokens or len(replay_retrieval_requests) > 1
        ):
            requests.append(
                ContextSummaryRequest(
                    layer_name="replay_packet",
                    source_refs=tuple(
                        dict.fromkeys(
                            memory_id
                            for request in replay_retrieval_requests
                            for memory_id in request.memory_ids
                        )
                    ),
                    token_budget=replay_budget.allocated_tokens,
                    reason="summarize targeted replay slices while keeping slot and compression choices inspectable",
                    required=False,
                )
            )
        return tuple(requests)

    def _snapshot_retrieval_budget(
        self,
        budgets: ContextBudgetPlan,
        *,
        state_focus: StateFocusDecision | None,
    ) -> int:
        snapshot = budgets.allocation_for("session_snapshot")
        if snapshot is None:
            return 0
        if state_focus is not None and state_focus.context_budget == "narrow":
            return max(32, snapshot.allocated_tokens // 4)
        if state_focus is not None and state_focus.context_budget == "broad":
            return max(64, snapshot.allocated_tokens // 2)
        return max(48, snapshot.allocated_tokens // 3)

    def _suggest_retrieval_budget(
        self,
        memories: tuple[MemoryRecord, ...],
        *,
        state_focus: StateFocusDecision | None,
    ) -> int:
        if not memories:
            return 0
        base = min(128, max(24, len(memories) * 24))
        if state_focus is not None and state_focus.context_budget == "narrow":
            return max(24, base - 24)
        if state_focus is not None and state_focus.context_budget == "broad":
            return min(192, base + 48)
        return base

    def _build_source_trace(
        self,
        *,
        session: Episode,
        work_items: tuple[...],
        memories: tuple[MemoryRecord, ...],
        instruction_refs: tuple[str, ...],
        state_focus: StateFocusDecision | None,
        profile_snapshot_refs: tuple[str, ...],
        recent_loop_context: tuple[str, ...],
        artifacts: tuple[str, ...],
        summary_requests: tuple[ContextSummaryRequest, ...],
        retrieval_requests: tuple[ContextRetrievalRequest, ...],
    ) -> tuple[ContextSourceTrace, ...]:
        steady_memories = _select_steady_memories(memories, session=session, work_items=work_items, state_focus=state_focus)
        snapshot_work_items = _snapshot_work_items(work_items, state_focus=state_focus)
        steady_refs = tuple(memory.memory_id for memory in steady_memories)
        snapshot_retrieval_requests, replay_retrieval_requests = _split_retrieval_requests(retrieval_requests)
        retrieved_memory_ids = tuple(
            dict.fromkeys(memory_id for request in snapshot_retrieval_requests for memory_id in request.memory_ids)
        )
        replay_memory_ids = tuple(
            dict.fromkeys(memory_id for request in replay_retrieval_requests for memory_id in request.memory_ids)
        )
        omitted_snapshot_refs = tuple(
            memory.memory_id
            for memory in memories
            if memory.memory_id not in steady_refs and memory.memory_id not in retrieved_memory_ids and memory.memory_id not in replay_memory_ids
        )
        traces: list[ContextSourceTrace] = [
            ContextSourceTrace(
                layer_name="stable_prefix",
                selected_refs=instruction_refs,
                reason="stable policy and runtime guardrails stay in a dedicated prefix instead of mixing with volatile recall",
            ),
            ContextSourceTrace(
                layer_name="session_snapshot",
                selected_refs=tuple(
                    dict.fromkeys(
                        (
                            *profile_snapshot_refs,
                            *(work_item.work_item_id for work_item in snapshot_work_items),
                            *steady_refs,
                            *retrieved_memory_ids,
                        )
                    )
                ),
                reason=_session_snapshot_trace_reason(
                    session,
                    work_items,
                    memories,
                    state_focus=state_focus,
                    profile_snapshot_refs=profile_snapshot_refs,
                    steady_memories=steady_memories,
                    retrieval_requests=snapshot_retrieval_requests,
                    summary_requests=summary_requests,
                ),
                omitted_refs=omitted_snapshot_refs,
            ),
        ]
        if replay_retrieval_requests:
            structured_turn_refs = tuple(memory.memory_id for memory in memories if parse_structured_turn_memory(memory) is not None)
            traces.append(
                ContextSourceTrace(
                    layer_name="replay_packet",
                    selected_refs=replay_memory_ids,
                    reason=_replay_packet_trace_reason(replay_retrieval_requests),
                    omitted_refs=tuple(
                        memory_id for memory_id in structured_turn_refs if memory_id not in replay_memory_ids
                    ),
                )
            )
        if recent_loop_context:
            traces.append(
                ContextSourceTrace(
                    layer_name="loop_context",
                    selected_refs=tuple(f"loop:{index}" for index, _ in enumerate(recent_loop_context, start=1)),
                    reason=_loop_context_trace_reason(session, recent_loop_context),
                )
            )
        if artifacts:
            traces.append(
                ContextSourceTrace(
                    layer_name="request_attachments",
                    selected_refs=_derived_source_refs("attachment", artifacts),
                    reason=_request_attachment_trace_reason(artifacts),
                )
            )
        return tuple(traces)

class ContextRuntime(ContextCapability):
    """Capability adapter for layered context assembly."""

    def __init__(
        self,
        planner: ContextPlanner | None = None,
        renderer: PromptRenderer | None = None,
        instruction_refs: tuple[str, ...] = (),
        total_tokens: int = 2048,
    ) -> None:
        self.descriptor = CapabilityDescriptor(
            capability_id="context.runtime",
            kind="context_assembler",
            version="1.0.0",
            metadata={"description": "Layered context assembly adapter."},
        )
        self._planner = planner or LayeredContextPlanner()
        self._renderer = renderer or MarkdownPromptRenderer()
        self._instruction_refs = instruction_refs
        self._total_tokens = total_tokens

    @property
    def instruction_refs(self) -> tuple[str, ...]:
        return self._instruction_refs

    @property
    def total_tokens(self) -> int:
        return self._total_tokens

    def plan(
        self,
        session: Episode,
        work_items: tuple[...],
        memories: tuple[MemoryRecord, ...],
        *,
        recent_loop_context: tuple[str, ...] = (),
        state_focus: StateFocusDecision | None = None,
        profile_snapshot_refs: tuple[str, ...] = (),
        artifacts: tuple[str, ...] = (),
        total_tokens: int | None = None,
    ) -> ContextAssemblyPlan:
        return self._planner.plan(
            session=session,
            work_items=work_items,
            memories=memories,
            total_tokens=total_tokens if total_tokens is not None else self._total_tokens,
            instruction_refs=self._instruction_refs,
            recent_loop_context=recent_loop_context,
            state_focus=state_focus,
            profile_snapshot_refs=profile_snapshot_refs,
            artifacts=artifacts,
        )

    def assemble(
        self,
        session: Episode,
        work_items: tuple[...],
        memories: tuple[MemoryRecord, ...],
        *,
        state_focus: StateFocusDecision | None = None,
    ) -> ContextBundle:
        plan = self.plan(session, work_items, memories, state_focus=state_focus)
        rendered = self._renderer.render(plan)
        prompt_envelope = build_prompt_envelope(plan.frame)
        return ContextBundle(
            bundle_id=f"{session.episode_id}:context",
            episode_id=session.episode_id,
            instruction_refs=self._instruction_refs,
            work_item_ids=tuple(work_item.work_item_id for work_item in work_items),
            memory_ids=tuple(memory.memory_id for memory in memories),
            artifact_ids=(),
            token_budget=plan.total_tokens,
            prompt_envelope=prompt_envelope,
            rendered_prompt=rendered,
        )

    def assemble_detailed(
        self,
        session: Episode,
        work_items: tuple[...],
        memories: tuple[MemoryRecord, ...],
        *,
        recent_loop_context: tuple[str, ...] = (),
        state_focus: StateFocusDecision | None = None,
        profile_snapshot_refs: tuple[str, ...] = (),
        artifacts: tuple[str, ...] = (),
        total_tokens: int | None = None,
    ) -> ContextAssemblyResult:
        plan = self.plan(
            session,
            work_items,
            memories,
            recent_loop_context=recent_loop_context,
            state_focus=state_focus,
            profile_snapshot_refs=profile_snapshot_refs,
            artifacts=artifacts,
            total_tokens=total_tokens,
        )
        rendered = self._renderer.render(plan)
        prompt_envelope = build_prompt_envelope(plan.frame)
        summary_by_layer = {
            layer.layer_name: layer.summary
            for layer in plan.layers
            if layer.summary is not None
        }
        retrieved_memory_ids = tuple(
            memory_id
            for request in plan.retrieval_requests
            for memory_id in request.memory_ids
        )
        bundle = ContextBundle(
            bundle_id=f"{session.episode_id}:context",
            episode_id=session.episode_id,
            instruction_refs=self._instruction_refs,
            work_item_ids=tuple(work_item.work_item_id for work_item in work_items),
            memory_ids=tuple(memory.memory_id for memory in memories),
            artifact_ids=artifacts,
            token_budget=plan.total_tokens,
            prompt_envelope=prompt_envelope,
            rendered_prompt=rendered,
        )
        return ContextAssemblyResult(
            bundle=bundle,
            plan=plan,
            rendered_prompt=rendered,
            summary_by_layer=summary_by_layer,
            retrieved_memory_ids=retrieved_memory_ids,
            source_trace=plan.source_trace,
            frame=plan.frame,
        )

__all__ = [
    "BudgetManager",
    "ContextAssemblyPlan",
    "ContextAssemblyResult",
    "ContextBudgetPlan",
    "ContextBudgetRequest",
    "ContextLayerBudget",
    "ContextLayerSnapshot",
    "ContextPlanner",
    "ContextRetrievalRequest",
    "ContextRuntime",
    "ContextSummaryRequest",
    "ContextSourceTrace",
    "DeterministicBudgetManager",
    "DeterministicRetrievalScheduler",
    "DeterministicSummaryHook",
    "LayeredContextPlanner",
    "MarkdownPromptRenderer",
    "PromptRenderer",
    "EpisodeReplay",
    "RetrievalScheduler",
    "EpisodeFrame",
    "EpisodeFrameBuilder",
    "StateSnapshot",
    "EpisodeFrozenContext",
    "SummaryHook",
    "LoopContext",
    "RequestAttachments",
]
