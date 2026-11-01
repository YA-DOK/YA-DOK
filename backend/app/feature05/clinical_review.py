"""Read-only F05 educational audit built from F03 persisted events.

This is NOT a clinical grade or an examination-result release scheduler.
No rubric information is persisted in student-visible F03 request events.
Only expose this review after the owning student's session is complete.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.simulation.engine import SimulationSession

SECTIONS = {
    "examination_requested": ("examination", "exam_items"),
    "investigation_requested": ("investigation", "case_investigation_items"),
}


def _norm(value: object) -> str:
    return " ".join(str(value or "").strip().casefold().replace("_", " ").split())


def _authored_items(case_data: dict) -> dict[str, dict[str, dict]]:
    """Only use metadata attached to this session's frozen case snapshot."""
    result: dict[str, dict[str, dict]] = {"examination": {}, "investigation": {}}
    for section, key in (("examination", "exam_items"), ("investigation", "case_investigation_items")):
        for item in case_data.get(key, []) or []:
            if not isinstance(item, dict) or not item.get("id"):
                continue
            for alias in (item.get("id"), item.get("label")):
                if alias:
                    result[section][_norm(alias)] = item
    for item in case_data.get("imaging", []) or []:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        for alias in (item.get("id"), item.get("label")):
            if alias:
                result["investigation"][_norm(alias)] = item
    return result


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def build_clinical_review(session: SimulationSession) -> dict[str, Any]:
    """Summarize orders for debrief; never return findings, results or diagnosis.

    Deliberately refuses a live session: this must not become an answer-key
    oracle while the learner is still diagnosing the patient.
    """
    if not session.is_completed:
        raise ValueError("Clinical review is only available after session completion.")

    catalogue = _authored_items(session.case_data)
    event_list = session.events
    created = next((e for e in event_list if e.event_type == "session_created"), None)
    start = _utc(created.timestamp) if created else None

    first_attempted: dict[str, set[str]] = {"examination": set(), "investigation": set()}
    counts = {"examination": 0, "investigation": 0}
    repeats = unavailable = not_indicated = unrated = 0
    elapsed: list[float] = []

    for event in event_list:
        if event.event_type not in SECTIONS:
            continue
        section, _ = SECTIONS[event.event_type]
        details = event.details or {}
        key = _norm(details.get("name"))
        if not key:
            continue
        counts[section] += 1
        if start is not None:
            elapsed.append(max(0.0, round((_utc(event.timestamp) - start).total_seconds(), 3)))

        if details.get("repeated") is True or details.get("status") == "already_requested":
            repeats += 1
            continue

        first_attempted[section].add(key)
        if details.get("status") == "unavailable":
            unavailable += 1

        item = catalogue[section].get(key)
        if item is None or item.get("relevance") is None:
            unrated += 1
        elif item.get("relevance") == "not_indicated":
            not_indicated += 1

    essentials = {"total": 0, "attempted": 0, "not_requested": 0}
    for section, key in (("examination", "exam_items"), ("investigation", "case_investigation_items"), ("investigation", "imaging")):
        for item in session.case_data.get(key, []) or []:
            if not isinstance(item, dict) or item.get("relevance") != "essential":
                continue
            essentials["total"] += 1
            if _norm(item.get("id")) in first_attempted[section] or _norm(item.get("label")) in first_attempted[section]:
                essentials["attempted"] += 1
            else:
                essentials["not_requested"] += 1

    return {
        "session_id": session.session_id,
        "status": "review_only_not_graded",
        "request_counts": {
            "examination": counts["examination"],
            "investigation_or_imaging": counts["investigation"],
            "repeated": repeats,
            "unavailable": unavailable,
            "not_indicated": not_indicated,
            "unrated": unrated,
        },
        "essential_actions": essentials,
        "request_timing": {
            "metric": "elapsed_seconds_from_session_creation_to_f05_request",
            "first_request_seconds": min(elapsed) if elapsed else None,
            "last_request_seconds": max(elapsed) if elapsed else None,
            "recorded_request_count": len(elapsed),
        },
        "result_release_delay": "not_configured_in_blueprint_v3_2",
        "penalty_points": None,
        "penalty_status": "requires_clinician_approved_rubric",
    }
