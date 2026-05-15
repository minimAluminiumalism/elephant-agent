"""Procedure projection helpers for operator-facing read surfaces."""

from __future__ import annotations

import re

from packages.contracts import ProcedureRecord, ProcedureStep, Record


def procedure_record_from_personal_model_record(
    record: Record,
) -> ProcedureRecord:
    if record.layer_type != "procedural_memory":
        raise ValueError(f"record {record.record_id} is not procedural_memory")
    payload = record.payload
    raw_steps = tuple(str(item).strip() for item in payload.get("steps") or () if str(item).strip())
    related_skill_ids = tuple(
        str(item).strip()
        for item in payload.get("related_skill_ids") or ()
        if str(item).strip()
    )
    skill_id = related_skill_ids[0] if related_skill_ids else None
    payload_status = str(payload.get("status") or "").strip().lower()
    maturity_state = str(payload.get("maturity_state") or "").strip().lower()
    approval_state = str(payload.get("approval_state") or "").strip().lower()
    behavioral_state = str(payload.get("behavioral_state") or "").strip().lower()
    if payload_status == "retired":
        status = "retired"
    elif behavioral_state == "active" or (maturity_state == "committed" and approval_state == "approved"):
        status = "active"
    else:
        status = payload_status or "candidate"
    return ProcedureRecord(
        procedure_id=record.record_id,
        title=str(payload.get("title") or "").strip() or record.record_id,
        summary=str(payload.get("summary") or "").strip() or str(payload.get("title") or "").strip() or record.record_id,
        status=status,
        trigger_refs=tuple(
            str(item).strip()
            for item in payload.get("trigger_conditions") or ()
            if str(item).strip()
        ),
        evidence_refs=tuple(
            str(item).strip()
            for item in payload.get("grounding_ids") or ()
            if str(item).strip()
        ),
        skill_id=skill_id,
        steps=tuple(
            ProcedureStep(
                step_id=f"{record.record_id}:step-{index}",
                title=(re.sub(r"^\d+\.\s*", "", instruction).strip() or f"Step {index}")[:72],
                instruction=instruction,
            )
            for index, instruction in enumerate(raw_steps, start=1)
        ),
    )
