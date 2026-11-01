"""F05 event-driven case-safe clinical orders for the stabilized F03 session."""
from __future__ import annotations

import json
from typing import Any

from app.feature05.clinical_integration import (
    exam_result,
    investigation_result,
    normalized_requested,
)


def _record(session, kind: str, name: str, result: Any, duplicate: bool, result_kind: str):
    # No educational relevance in client-visible F03 event details.
    # F07 evaluates using private Blueprint metadata and saved order names.
    from app.simulation.engine import SimulationMessage
    status = "already_requested" if duplicate else ("completed" if result is not None else "unavailable")
    payload = {
        "name": name,
        "available": result is not None,
        "status": status,
        "kind": result_kind,
        "result": None if duplicate else result,
        "message": (
            "Already requested. The saved original result is available in your history."
            if duplicate else
            "Case-defined result retrieved." if result is not None else
            "This case does not contain an approved result for that request."
        ),
    }
    if not duplicate:
        session.messages.append(SimulationMessage(role="user",content=f"{kind.title()} requested: {name}",action=f"request_{kind}"))
        session.messages.append(SimulationMessage(role="system",content=json.dumps(payload,ensure_ascii=False),action=f"{kind}_result"))
    session.record_event(
        f"{kind}_requested",
        {"name": name, "available": result is not None,"status": status,
         "result": None if duplicate else result, "repeated": duplicate, "kind": result_kind},
    )
    return payload


def perform_examination(session, examination_name: str, error_type):
    name = examination_name.strip()
    if not name:
        raise error_type("Examination name cannot be empty.")
    result, item = exam_result(session.case_data, name)
    # Only legacy F03 cases use legacy findings. v3.2 cases must never fall back to invented values.
    if item is None and "exam_items" not in session.case_data:
        from app.simulation.engine import _find_case_result, _normalize_examination_name
        findings = session.case_data.get("physical_examination") or session.case_data.get("examination") or {}
        if isinstance(findings, dict):
            result = _find_case_result(findings,name)
            if result is None:
                for key,value in findings.items():
                    if _normalize_examination_name(str(key)) == _normalize_examination_name(name):
                        result = value
                        break
    duplicate = normalized_requested(session,"examination",name)
    if not duplicate:
        session.requested_examinations.append(name)
    return _record(session,"examination",name,result,duplicate,"examination")


def perform_investigation(session, investigation_name: str, error_type):
    name = investigation_name.strip()
    if not name:
        raise error_type("Investigation name cannot be empty.")
    result, item, kind = investigation_result(session.case_data, name)
    if item is None and "case_investigation_items" not in session.case_data:
        from app.simulation.engine import _find_case_result
        raw = session.case_data.get("investigations",{})
        if isinstance(raw, dict):
            result = _find_case_result(raw,name)
    duplicate = normalized_requested(session,"investigation",name)
    if not duplicate:
        session.requested_investigations.append(name)
    return _record(session,"investigation",name,result,duplicate,kind)
