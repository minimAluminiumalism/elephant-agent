from __future__ import annotations

from dataclasses import replace

from .memory_runtime_support import *  # noqa: F401,F403
from .personal_model_support import (
    PersonalModelWriteRequest,
    PersonalModelWriteResult,
    build_personal_model_component_record,
    build_personal_model_proposal,
    evaluate_personal_model_governance,
)


# Stubs for removed reflection modules (methods that reference these are dead code,
# kept temporarily for MemoryRuntime class shape compatibility).
class _ReflectionWindowResult:
    pass

ReflectionWindowResult = _ReflectionWindowResult


def _noop_reflection(*args, **kwargs):
    return _ReflectionWindowResult()

execute_reflection_window = _noop_reflection


class MemoryRuntime:
    def __init__(
        self,
        *,
        ledger: MemoryLedger | None = None,
        store: MemoryStore | None = None,
        extractor: MemoryExtractor | None = None,
        consolidator: MemoryConsolidator | None = None,
        retriever: MemoryRetriever | None = None,
        governance: MemoryGovernance | None = None,
        repository: RuntimeStorageRepository | None = None,
        semantic_summary_indexer: object | None = None,
    ) -> None:
        self.ledger = ledger or InMemoryMemoryLedger()
        self.store = store or InMemoryMemoryStore()
        self.extractor = extractor or DefaultMemoryExtractor()
        self.consolidator = consolidator or DefaultMemoryConsolidator()
        self.retriever = retriever or DefaultMemoryRetriever(self.store)
        self.governance = governance or DefaultMemoryGovernance()
        self.repository = repository
        # Optional producer-side indexer. When present, any committed
        # personal-model record gets its text pushed into the semantic index
        # right after `upsert_record`, so subsequent episodes can recall it.
        self.semantic_summary_indexer = semantic_summary_indexer

    def _governance_event_entry(
        self,
        episode_id: str,
        decision: MemoryGovernanceDecision,
        *,
        target_memory_id: str | None,
        related_memory_ids: tuple[str, ...] = (),
    ) -> MemoryLedgerEntry:
        created_at = _now()
        digest_source = "|".join(
            (
                episode_id,
                decision.action,
                target_memory_id or "",
                decision.actor,
                decision.reason,
                decision.replacement_memory_id or "",
                ",".join(related_memory_ids),
                created_at.isoformat(),
            )
        )
        entry_id = "memory.governance." + hashlib.sha256(digest_source.encode("utf-8")).hexdigest()[:16]
        state_tag = "allowed" if decision.allowed else "denied"
        content = f"{decision.action}:{state_tag}:{target_memory_id or 'episode'}:{decision.reason}"
        metadata = {
            "action": decision.action,
            "target_memory_id": target_memory_id or "",
            "allowed": "true" if decision.allowed else "false",
            "actor": decision.actor,
            "reason": decision.reason,
            "replacement_memory_id": decision.replacement_memory_id or "",
            "related_memory_ids": ",".join(related_memory_ids),
        }
        return MemoryLedgerEntry(
            entry_id=entry_id,
            episode_id=episode_id,
            event_id=entry_id,
            event_type="memory_governance",
            content=content,
            kind="governance",
            source_event_id=target_memory_id,
            work_item_refs=(),
            tags=("governance", decision.action, state_tag),
            created_at=created_at,
            metadata=metadata,
        )

    def _record_governance_event(
        self,
        session_id: str,
        decision: MemoryGovernanceDecision,
        *,
        target_memory_id: str | None,
        related_memory_ids: tuple[str, ...] = (),
    ) -> None:
        self.ledger.append(
            self._governance_event_entry(
                session_id,
                decision,
                target_memory_id=target_memory_id,
                related_memory_ids=related_memory_ids,
            )
        )

    @classmethod
    def from_repository(
        cls,
        repository: RuntimeStorageRepository,
        *,
        extractor: MemoryExtractor | None = None,
        consolidator: MemoryConsolidator | None = None,
        retriever: MemoryRetriever | None = None,
        governance: MemoryGovernance | None = None,
        semantic_bundle=None,
    ) -> "MemoryRuntime":
        store = SQLiteMemoryStore(repository)
        ledger = SQLiteMemoryLedger(repository)
        return cls(
            ledger=ledger,
            store=store,
            extractor=extractor,
            consolidator=consolidator,
            retriever=retriever or DefaultMemoryRetriever(
                store,
                repository=repository,
                semantic_bundle=semantic_bundle,
            ),
            governance=governance,
            repository=repository,
        )

    def _capture_repository(self) -> RuntimeStorageRepository:
        if self.repository is None:
            raise RuntimeError("memory capture requires a repository-backed runtime")
        return self.repository

    def _resolved_personal_model_write_request(self, request: PersonalModelWriteRequest) -> PersonalModelWriteRequest:
        repository = self._capture_repository()
        source_records: list[Record] = []
        for record_id in request.source_record_ids:
            source_record = repository.load_record(record_id)
            if source_record is None:
                raise KeyError(f"personal model write source record not found: {record_id}")
            source_records.append(source_record)
        resolved_personal_model_id = request.personal_model_id or next(
            (record.personal_model_id for record in source_records if record.personal_model_id),
            None,
        )
        if not resolved_personal_model_id:
            raise ValueError("personal model writes require personal_model_id or a personal-model-linked source record")
        if any(
            record.personal_model_id
            and record.personal_model_id != resolved_personal_model_id
            for record in source_records
        ):
            raise ValueError("personal model write source records must resolve to one personal_model_id")
        resolved_state_id = request.state_id or next((record.state_id for record in source_records if record.state_id), None)
        return replace(
            request,
            personal_model_id=resolved_personal_model_id,
            state_id=resolved_state_id,
            created_at=request.created_at or _now(),
        )

    def _resolved_capture_request(self, request: MemoryCaptureRequest) -> tuple[MemoryCaptureRequest, Record]:
        repository = self._capture_repository()
        source_record = repository.load_record(request.source_record_id)
        if source_record is None:
            raise KeyError(f"memory capture source record not found: {request.source_record_id}")
        resolved_state_id = request.state_id or source_record.state_id
        resolved_personal_model_id = request.personal_model_id or source_record.personal_model_id
        if request.scope == "state" and not resolved_state_id:
            raise ValueError("state-scoped memory capture requires state_id or a state-owned source record")
        if request.scope == "personal_model" and not resolved_personal_model_id:
            raise ValueError(
                "personal_model-scoped memory capture requires personal_model_id or a personal-model-owned source record"
            )
        return (
            replace(
                request,
                state_id=resolved_state_id,
                personal_model_id=resolved_personal_model_id,
                created_at=request.created_at or _now(),
            ),
            source_record,
        )

    def _capture_grounding(self, request: MemoryCaptureRequest) -> Grounding:
        captured_at = request.created_at or _now()
        grounding_hash = _capture_hash(
            request.scope,
            request.kind,
            request.source_record_id,
            request.content,
            captured_at.isoformat(),
        )
        metadata = {
            "capture_kind": request.kind,
            "capture_scope": request.scope,
            "user_directed": "true" if request.user_directed else "false",
            "sensitivity": request.sensitivity,
            "episode_id": request.episode_id or "",
            "loop_id": request.loop_id or "",
            "step_ids": ",".join(request.step_ids),
            "tool_refs": ",".join(request.tool_refs),
            "model_refs": ",".join(request.model_refs),
            **dict(request.metadata),
        }
        return Grounding(
            grounding_id=f"grounding:capture:{grounding_hash}",
            source_record_ids=(request.source_record_id,),
            summary=f"{request.scope} {request.kind} memory capture",
            confidence=1.0 if request.user_directed else 0.6,
            policy_decision="committed" if request.user_directed else "observed",
            repair_state="none",
            created_at=captured_at,
            metadata=metadata,
        )

    def _personal_model_grounding(self, request: PersonalModelWriteRequest) -> Grounding:
        created_at = request.created_at or _now()
        grounding_hash = _capture_hash(
            request.kind,
            request.maturity_state,
            ",".join(request.source_record_ids),
            request.content,
            created_at.isoformat(),
        )
        metadata = {
            "component_family": request.kind,
            "maturity_state": request.maturity_state,
            "support_count": str(request.support_count),
            "sensitivity": request.sensitivity,
            "user_confirmed": "true" if request.user_confirmed else "false",
            "user_directed": "true" if request.user_directed else "false",
            "user_edited": "true" if request.user_edited else "false",
            "state_refs": ",".join(request.state_refs),
            "episode_ids": ",".join(request.episode_ids),
            "related_skill_ids": ",".join(request.related_skill_ids),
            **dict(request.metadata),
        }
        return Grounding(
            grounding_id=f"grounding:personal-model:{grounding_hash}",
            source_record_ids=request.source_record_ids,
            summary=f"personal_model {request.kind} {request.maturity_state} write",
            confidence=request.confidence,
            policy_decision=request.maturity_state,
            repair_state=request.correction_state,
            created_at=created_at,
            metadata=metadata,
        )

    def _state_memory_entry(self, request: MemoryCaptureRequest, grounding: Grounding) -> MemoryEntry:
        assert request.state_id is not None
        assert request.personal_model_id is not None
        created_at = request.created_at or _now()
        capture_hash = _capture_hash(
            request.scope,
            request.kind,
            request.source_record_id,
            request.content,
            created_at.isoformat(),
        )
        return MemoryEntry(
            memory_entry_id=f"memory.curate:state:{capture_hash}",
            owner_scope="state",
            kind=request.kind,
            content=request.content.strip(),
            grounding_ids=(grounding.grounding_id,),
            personal_model_id=request.personal_model_id,
            state_id=request.state_id,
            sensitivity=request.sensitivity,
            status="committed" if request.user_directed else "observed",
            created_at=created_at,
            updated_at=created_at,
            metadata={
                "capture_kind": request.kind,
                "capture_scope": request.scope,
                "user_directed": "true" if request.user_directed else "false",
                **dict(request.metadata),
            },
        )

    def _personal_model_index_entry(
        self,
        request: PersonalModelWriteRequest,
        grounding: Grounding,
        record: Record,
        *,
        status: str,
        behavioral_state: str,
    ) -> MemoryEntry:
        assert request.personal_model_id is not None
        created_at = request.created_at or _now()
        capture_hash = _capture_hash(
            request.kind,
            request.maturity_state,
            ",".join(request.source_record_ids),
            request.content,
            created_at.isoformat(),
        )
        return MemoryEntry(
            memory_entry_id=f"memory.curate:personal_model:{capture_hash}",
            owner_scope="personal_model",
            kind=request.kind,
            content=request.content.strip(),
            grounding_ids=(grounding.grounding_id,),
            personal_model_id=request.personal_model_id,
            state_id=request.state_id,
            sensitivity=request.sensitivity,
            status=status,
            created_at=created_at,
            updated_at=created_at,
            metadata={
                "canonical_record_id": record.record_id,
                "behavioral_state": behavioral_state,
                "component_family": request.kind,
                "user_directed": "true" if request.user_directed else "false",
                **dict(request.metadata),
            },
        )

    def run_reflection_window(
        self,
        *,
        trigger: str,
        personal_model_id: str,
        state_id: str,
        episode_id: str,
        loop_id: str | None = None,
        checkpoint_step_id: str | None = None,
        source_record_id: str | None = None,
        summary: str = "",
        created_at: datetime | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> ReflectionWindowResult:
        return execute_reflection_window(
            self,
            trigger=trigger,
            personal_model_id=personal_model_id,
            state_id=state_id,
            episode_id=episode_id,
            loop_id=loop_id,
            checkpoint_step_id=checkpoint_step_id,
            source_record_id=source_record_id,
            summary=summary,
            created_at=created_at,
            metadata=metadata,
        )

    def write_personal_model_component(self, request: PersonalModelWriteRequest) -> PersonalModelWriteResult:
        resolved_request = self._resolved_personal_model_write_request(request)
        repository = self._capture_repository()
        decision = evaluate_personal_model_governance(resolved_request)
        grounding = self._personal_model_grounding(resolved_request)
        repository.upsert_grounding(
            grounding,
            owner_scope="personal_model",
            personal_model_id=resolved_request.personal_model_id,
            state_id=resolved_request.state_id,
        )
        canonical_record = build_personal_model_component_record(resolved_request, grounding, decision)
        repository.upsert_record(canonical_record)
        memory_entry = self._personal_model_index_entry(
            resolved_request,
            grounding,
            canonical_record,
            status=decision.stored_maturity_state,
            behavioral_state=decision.behavioral_state,
        )
        repository.upsert_memory_entry(memory_entry)
        proposal: ReflectionProposal | None = None
        if decision.proposal_type is not None:
            proposal = build_personal_model_proposal(
                resolved_request,
                grounding,
                decision,
                target_id=canonical_record.record_id,
            )
            repository.upsert_reflection_proposal(proposal)
        # Producer-side semantic indexing. Only committed records go in —
        # proposals are not recall targets. Best-effort: any exception is
        # swallowed so a semantic-index outage never blocks a governance write.
        if (
            self.semantic_summary_indexer is not None
            and decision.stored_maturity_state == "committed"
        ):
            index_personal_model_record = getattr(
                self.semantic_summary_indexer, "index_personal_model_record", None
            )
            if callable(index_personal_model_record):
                try:
                    index_personal_model_record(canonical_record)
                except Exception:
                    pass
        return PersonalModelWriteResult(
            status=decision.status,
            kind=resolved_request.kind,
            reason=decision.reason,
            grounding=grounding,
            canonical_record=canonical_record,
            memory_entry=memory_entry,
            proposal=proposal,
        )

    def capture_memory(self, request: MemoryCaptureRequest) -> MemoryCaptureResult:
        try:
            resolved_request, _ = self._resolved_capture_request(request)
        except (KeyError, ValueError) as exc:
            return MemoryCaptureResult(
                status="rejected",
                scope=request.scope,
                kind=request.kind,
                reason=str(exc),
            )
        repository = self._capture_repository()
        if resolved_request.scope == "state":
            grounding = self._capture_grounding(resolved_request)
            repository.upsert_grounding(
                grounding,
                owner_scope=resolved_request.scope,
                personal_model_id=resolved_request.personal_model_id,
                state_id=resolved_request.state_id,
            )
            memory_entry = self._state_memory_entry(resolved_request, grounding)
            repository.upsert_memory_entry(memory_entry)
            return MemoryCaptureResult(
                status="committed",
                scope=resolved_request.scope,
                kind=resolved_request.kind,
                reason="memory capture committed",
                grounding=grounding,
                memory_entry=memory_entry,
            )
        component_result = self.write_personal_model_component(
            PersonalModelWriteRequest(
                kind=resolved_request.kind,
                content=resolved_request.content,
                source_record_ids=(resolved_request.source_record_id,),
                personal_model_id=resolved_request.personal_model_id,
                state_id=resolved_request.state_id,
                maturity_state="committed",
                confidence=1.0 if resolved_request.user_directed else 0.6,
                sensitivity=resolved_request.sensitivity,
                support_count=1,
                user_directed=resolved_request.user_directed,
                component_kind=resolved_request.metadata.get("component_kind", ""),
                metadata=resolved_request.metadata,
                created_at=resolved_request.created_at,
            )
        )
        return MemoryCaptureResult(
            status=component_result.status,
            scope=resolved_request.scope,
            kind=resolved_request.kind,
            reason=component_result.reason,
            grounding=component_result.grounding,
            canonical_record=component_result.canonical_record,
            memory_entry=component_result.memory_entry,
        )

    def create_reflection_proposal(
        self,
        proposal: ReflectionProposal,
    ) -> ReflectionProposalLifecycleResult:
        validate_reflection_proposal(proposal)
        repository = self._capture_repository()
        missing = tuple(
            grounding_id
            for grounding_id in proposal.grounding_ids
            if repository.load_grounding(grounding_id) is None
        )
        if missing:
            raise KeyError(f"reflection proposal grounding ids not found: {', '.join(missing)}")
        repository.upsert_reflection_proposal(proposal)
        return ReflectionProposalLifecycleResult(
            proposal=proposal,
            action="create",
            reason="reflection proposal recorded",
        )

    def transition_reflection_proposal(
        self,
        reflection_proposal_id: str,
        *,
        status: str,
    ) -> ReflectionProposalLifecycleResult:
        repository = self._capture_repository()
        current = repository.load_reflection_proposal(reflection_proposal_id)
        if current is None:
            raise KeyError(f"reflection proposal not found: {reflection_proposal_id}")
        validate_reflection_transition(current.status, status)
        updated = replace(
            current,
            status=status,
            updated_at=_now(),
        )
        validate_reflection_proposal(updated)
        repository.upsert_reflection_proposal(updated)
        return ReflectionProposalLifecycleResult(
            proposal=updated,
            action="transition",
            reason=f"reflection proposal moved to {status}",
        )

    def append_event(self, event: EventEnvelope) -> MemoryAppendResult:
        result = self.extractor.extract(event)
        self.ledger.append(result.ledger_entry)
        for record in result.extracted_records:
            decision = self.governance.can_record(record)
            if decision.allowed:
                self.store.upsert(record)
        return result

    def record_memory(self, record: MemoryRecord) -> MemoryGovernanceDecision:
        if record.kind != "structured_turn":
            return MemoryGovernanceDecision(
                "record",
                record.memory_id,
                False,
                "direct memory writes must use capture_memory; record_memory is reserved for structured turn evidence",
            )
        decision = self.governance.can_record(record)
        if not decision.allowed:
            self._record_governance_event(
                record.episode_id,
                decision,
                target_memory_id=record.memory_id,
            )
            return decision
        self.store.upsert(record)
        return decision

    def consolidate_episode(self, episode_id: str, memory_ids: tuple[str, ...] = ()) -> MemoryConsolidationResult:
        if memory_ids:
            records = tuple(
                record
                for memory_id in memory_ids
                if (record := self.store.get(memory_id)) is not None
            )
        else:
            records = self.store.list(episode_id=episode_id)
        decision = self.governance.can_consolidate(records)
        if not decision.allowed:
            self._record_governance_event(
                episode_id,
                decision,
                target_memory_id=None,
                related_memory_ids=tuple(record.memory_id for record in records),
            )
            return MemoryConsolidationResult(
                episode_id=episode_id,
                input_memory_ids=tuple(record.memory_id for record in records),
                summary_record=None,
                rationale=decision.reason,
            )
        result = self.consolidator.consolidate(episode_id, records)
        if result.summary_record is not None:
            self.store.upsert(result.summary_record)
            self.store.mark_consolidated(tuple(result.input_memory_ids), result.summary_record.memory_id)
            self._record_governance_event(
                episode_id,
                MemoryGovernanceDecision(
                    "consolidate",
                    result.summary_record.memory_id,
                    True,
                    result.rationale or decision.reason,
                    actor=decision.actor,
                    replacement_memory_id=result.summary_record.memory_id,
                ),
                target_memory_id=result.summary_record.memory_id,
                related_memory_ids=tuple(result.input_memory_ids),
            )
        return result

    def retrieve(
        self,
        episode_id: str,
        query: str,
        *,
        work_item_ids: tuple[str, ...] = (),
        limit: int = 5,
        scope_episode_ids: tuple[str, ...] = (),
        scope_reason: str = "",
    ) -> MemoryRetrievalResult:
        return self.retriever.retrieve(
            episode_id,
            query,
            work_item_ids=work_item_ids,
            limit=limit,
            scope_episode_ids=scope_episode_ids,
            scope_reason=scope_reason,
        )

    def retrieve_evidence(self, request: EvidenceRetrievalRequest) -> EvidenceRetrievalResult:
        detailed = getattr(self.retriever, "retrieve_evidence", None)
        if callable(detailed):
            return detailed(request)
        focus_work_item_ids = request.work_item_ids
        if not focus_work_item_ids and request.state_focus is not None and request.state_focus.focus_work_item_ids:
            focus_work_item_ids = request.state_focus.focus_work_item_ids
        opened_scopes = request.scopes
        if (
            request.state_focus is not None
            and request.state_focus.focus_scope not in {"", "episode"}
            and request.state_focus.focus_scope not in opened_scopes
        ):
            opened_scopes = (*opened_scopes, request.state_focus.focus_scope)
        fallback = self.retrieve(
            request.episode_id,
            request.query,
            work_item_ids=focus_work_item_ids,
            limit=request.limit,
            scope_episode_ids=request.lineage_episode_ids,
            scope_reason=request.scope_reason,
        )
        candidates = tuple(
            EvidenceCandidate(
                evidence_id=candidate.record.memory_id,
                memory=candidate.record,
                score=candidate.score,
                matched_scopes=("episode",),
                reasons=tuple(
                    RecallReason("memory.fallback", detail, 0.0)
                    for detail in candidate.reasons
                ),
            )
            for candidate in fallback.candidates
        )
        return EvidenceRetrievalResult(
            request=request,
            scope_episode_ids=fallback.scope_episode_ids,
            scope_reason=fallback.scope_reason,
            candidates=candidates,
            recall_reasons=RecallReasons(
                opened_scopes=opened_scopes,
                evidence_ids=tuple(candidate.evidence_id for candidate in candidates),
                scope_reason=fallback.scope_reason,
                rerank_summary="fallback memory retrieval adapter reused existing ranking output",
                reasons=tuple(
                    RecallReason("memory.fallback", fallback.scope_reason, 0.0),
                ),
            ),
            index_policy=self.index_policy(),
        )

    def index_policy(self) -> EmbeddingIndexPolicy:
        return build_embedding_index_policy(self.store)

    def build_resume_packet(
        self,
        request: EvidenceRetrievalRequest,
        retrieval: EvidenceRetrievalResult,
        *,
        next_move: str = "",
        artifact_ids: tuple[str, ...] = (),
        constraint_ids: tuple[str, ...] = (),
    ) -> ResumePacket:
        return build_resume_packet(
            request,
            retrieval,
            next_move=next_move,
            artifact_ids=artifact_ids,
            constraint_ids=constraint_ids,
        )

    def maintain_episode(
        self,
        episode_id: str,
        *,
        now: datetime | None = None,
        maximum_ephemeral_age: timedelta = timedelta(hours=6),
    ) -> MemoryMaintenanceResult:
        current = now or _now()
        eligible = tuple(
            record
            for record in self.store.list(episode_id=episode_id)
            if self._eligible_for_maintenance(record, now=current, maximum_ephemeral_age=maximum_ephemeral_age)
        )
        if len(eligible) < 2:
            return MemoryMaintenanceResult(
                episode_id=episode_id,
                maintained_memory_ids=tuple(record.memory_id for record in eligible),
                summary_record=None,
                rationale="no aged episodic memories required maintenance",
            )

        result = self.consolidator.consolidate(episode_id, eligible)
        if result.summary_record is None:
            return MemoryMaintenanceResult(
                episode_id=episode_id,
                maintained_memory_ids=tuple(record.memory_id for record in eligible),
                summary_record=None,
                rationale=result.rationale or "maintenance consolidation produced no summary",
            )

        summary = replace(
            result.summary_record,
            tags=_unique(result.summary_record.tags + ("maintenance", "aged")),
        )
        self.store.upsert(summary)
        self.store.mark_consolidated(tuple(result.input_memory_ids), summary.memory_id)
        self._record_governance_event(
            episode_id,
            MemoryGovernanceDecision(
                "consolidate",
                summary.memory_id,
                True,
                "aged episodic memories consolidated into a maintained summary",
                actor="system",
                replacement_memory_id=summary.memory_id,
            ),
            target_memory_id=summary.memory_id,
            related_memory_ids=tuple(result.input_memory_ids),
        )
        return MemoryMaintenanceResult(
            episode_id=episode_id,
            maintained_memory_ids=tuple(result.input_memory_ids),
            summary_record=summary,
            rationale="aged episodic memories were consolidated into a maintained summary",
        )

    def list_governance_events(
        self,
        episode_id: str,
        *,
        target_memory_id: str | None = None,
    ) -> tuple[MemoryGovernanceEvent, ...]:
        events: list[MemoryGovernanceEvent] = []
        for entry in self.ledger.list(episode_id=episode_id):
            if entry.event_type != "memory_governance":
                continue
            action = str(entry.metadata.get("action", ""))
            if not action:
                continue
            event_target = str(entry.metadata.get("target_memory_id", "")) or entry.source_event_id
            if target_memory_id is not None and event_target != target_memory_id:
                related_ids = _split_csv(str(entry.metadata.get("related_memory_ids", "")))
                if target_memory_id not in related_ids:
                    continue
            events.append(
                MemoryGovernanceEvent(
                    entry_id=entry.entry_id,
                    episode_id=entry.episode_id,
                    action=action,
                    target_memory_id=event_target,
                    allowed=str(entry.metadata.get("allowed", "false")).lower() == "true",
                    actor=str(entry.metadata.get("actor", "user")),
                    reason=str(entry.metadata.get("reason", entry.content)),
                    replacement_memory_id=str(entry.metadata.get("replacement_memory_id", "")) or None,
                    related_memory_ids=_split_csv(str(entry.metadata.get("related_memory_ids", ""))),
                    created_at=entry.created_at,
                )
            )
        return tuple(events)

    def correct_memory(
        self,
        target_memory_id: str,
        corrected_content: str,
        *,
        actor: str = "user",
        reason: str = "",
    ) -> MemoryMutationResult:
        original = self.store.get(target_memory_id)
        if original is None:
            decision = MemoryGovernanceDecision("correct", target_memory_id, False, "target memory not found", actor=actor)
            return MemoryMutationResult(decision=decision)
        decision = self.governance.can_correct(original, corrected_content, actor=actor)
        if not decision.allowed:
            self._record_governance_event(
                original.episode_id,
                decision,
                target_memory_id=target_memory_id,
            )
            return MemoryMutationResult(decision=decision)
        protected_tags: tuple[str, ...] = ()
        policy = getattr(self.governance, "policy", None)
        if policy is not None:
            protected_tags = tuple(getattr(policy, "protected_tags", ()))
        preserved_tags = tuple(tag for tag in original.tags if tag not in protected_tags)
        reason_tag = (f"reason:{reason}",) if reason else ()
        corrected = MemoryRecord(
            memory_id=f"{target_memory_id}:corrected",
            episode_id=original.episode_id,
            kind=original.kind,
            content=corrected_content,
            source_event_id=original.source_event_id,
            work_item_refs=original.work_item_refs,
            tags=_unique(preserved_tags + ("corrected",) + reason_tag),
            created_at=_now(),
            metadata=dict(original.metadata),
        )
        self.store.upsert(corrected)
        self.store.mark_superseded(target_memory_id, corrected.memory_id)
        applied_decision = MemoryGovernanceDecision(
            "correct",
            target_memory_id,
            True,
            "memory corrected",
            actor=actor,
            replacement_memory_id=corrected.memory_id,
        )
        self._record_governance_event(
            original.episode_id,
            applied_decision,
            target_memory_id=target_memory_id,
            related_memory_ids=(corrected.memory_id,),
        )
        return MemoryMutationResult(
            decision=applied_decision,
            record=corrected,
        )

    def delete_memory(
        self,
        target_memory_id: str,
        *,
        actor: str = "user",
        reason: str,
    ) -> MemoryMutationResult:
        original = self.store.get(target_memory_id)
        if original is None:
            decision = MemoryGovernanceDecision("delete", target_memory_id, False, "target memory not found", actor=actor)
            return MemoryMutationResult(decision=decision)
        decision = self.governance.can_delete(original, actor=actor, reason=reason)
        if not decision.allowed:
            self._record_governance_event(
                original.episode_id,
                decision,
                target_memory_id=target_memory_id,
            )
            return MemoryMutationResult(decision=decision)
        self.store.mark_deleted(target_memory_id)
        self._record_governance_event(
            original.episode_id,
            decision,
            target_memory_id=target_memory_id,
        )
        return MemoryMutationResult(decision=decision)

    def pin_memory(
        self,
        target_memory_id: str,
        *,
        actor: str = "user",
        reason: str = "",
    ) -> MemoryMutationResult:
        original = self.store.get(target_memory_id)
        if original is None:
            decision = MemoryGovernanceDecision("pin", target_memory_id, False, "target memory not found", actor=actor)
            return MemoryMutationResult(decision=decision)
        if "pinned" in original.tags:
            decision = MemoryGovernanceDecision("pin", target_memory_id, True, "memory already pinned", actor=actor)
            return MemoryMutationResult(decision=decision, record=original)
        updated = replace(original, tags=_unique(original.tags + ("pinned",)))
        self.store.upsert(updated)
        decision = MemoryGovernanceDecision(
            "pin",
            target_memory_id,
            True,
            reason or "memory pinned",
            actor=actor,
        )
        self._record_governance_event(
            original.episode_id,
            decision,
            target_memory_id=target_memory_id,
            related_memory_ids=(updated.memory_id,),
        )
        return MemoryMutationResult(decision=decision, record=updated)

    def unpin_memory(
        self,
        target_memory_id: str,
        *,
        actor: str = "user",
        reason: str = "",
    ) -> MemoryMutationResult:
        original = self.store.get(target_memory_id)
        if original is None:
            decision = MemoryGovernanceDecision("unpin", target_memory_id, False, "target memory not found", actor=actor)
            return MemoryMutationResult(decision=decision)
        if "pinned" not in original.tags:
            decision = MemoryGovernanceDecision("unpin", target_memory_id, True, "memory was not pinned", actor=actor)
            return MemoryMutationResult(decision=decision, record=original)
        updated = replace(original, tags=tuple(tag for tag in original.tags if tag != "pinned"))
        self.store.upsert(updated)
        decision = MemoryGovernanceDecision(
            "unpin",
            target_memory_id,
            True,
            reason or "memory unpinned",
            actor=actor,
        )
        self._record_governance_event(
            original.episode_id,
            decision,
            target_memory_id=target_memory_id,
            related_memory_ids=(updated.memory_id,),
        )
        return MemoryMutationResult(decision=decision, record=updated)

    def _eligible_for_maintenance(
        self,
        record: MemoryRecord,
        *,
        now: datetime,
        maximum_ephemeral_age: timedelta,
    ) -> bool:
        if record.kind != "episodic":
            return False
        if record.created_at is None:
            return False
        age = now - record.created_at
        if age < maximum_ephemeral_age:
            return False
        if not record.work_item_refs:
            return False
        if any(tag in {"pinned", "locked", "system"} for tag in record.tags):
            return False
        return True
