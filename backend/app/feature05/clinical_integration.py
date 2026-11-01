"""F05 session-bound tools built on F02 blueprint snapshots and F03 event logs.

Sara's catalog is reused for discovery. Her standalone ORDERS/SESSION_CASES
must not be used with the authenticated F03 runtime.
"""
from __future__ import annotations

from typing import Any

from app.feature05.catalog import get_all_investigations
from app.simulation.engine import SimulationSession


def _key(name: str) -> str:
    return " ".join(name.strip().casefold().replace("_", " ").split())


def _category(item: dict) -> str:
    return str(item.get("category") or "other")


def clinical_options(session: SimulationSession, search: str = "") -> dict[str, Any]:
    """Safe, result-free catalogue. Do not return exam findings or answer keys."""
    data = session.case_data
    term = _key(search)

    raw_exams = data.get("exam_items")
    exams: list[dict[str, str]] = []
    if isinstance(raw_exams, list):
        for item in raw_exams:
            if isinstance(item, dict) and item.get("id") and item.get("label"):
                exams.append({
                    "id": str(item["id"]),
                    "label": str(item["label"]),
                    "category": str(item.get("system") or "general"),
                })
    else:
        # Legacy F03 sessions created before the F02 published-case converter.
        source = data.get("physical_examination") or data.get("examination") or {}
        if isinstance(source, dict):
            exams = [{"id": str(k), "label": str(k), "category": "general"}
                     for k in source]

    tests = [
        {"id": item.id, "label": item.name, "category": item.category.value}
        for item in get_all_investigations()
        if item.category.value not in ("general", "system")
    ]
    # F02 can define tests not present in Sara's common catalogue.
    seen = {_key(item["id"]) for item in tests}
    source = data.get("case_investigation_items")
    if isinstance(source, list):
        for item in source:
            if not isinstance(item, dict) or not item.get("id"):
                continue
            ident = str(item["id"])
            if _key(ident) not in seen:
                tests.append({"id": ident, "label": str(item.get("label") or ident),
                              "category": "laboratory"})
                seen.add(_key(ident))
    elif isinstance(data.get("investigations"), dict):
        for ident in data["investigations"]:
            if _key(str(ident)) not in seen:
                tests.append({"id": str(ident), "label": str(ident),
                              "category": "laboratory"})
                seen.add(_key(str(ident)))

    imaging = []
    for item in data.get("imaging", []):
        if isinstance(item, dict) and item.get("id"):
            imaging.append({"id": str(item["id"]),
                            "label": str(item.get("label") or item["id"]),
                            "category": str(item.get("modality") or "imaging")})

    # Only catalogue metadata, never configured availability of investigations.
    def filtered(items):
        return [i for i in items if not term or term in _key(i["id"] + " " + i["label"])]

    return {"session_id": session.session_id,
            "current_phase": session.current_phase.value,
            "examinations": filtered(exams),
            "investigations": filtered(tests),
            "imaging": filtered(imaging)}


def exam_result(case_data: dict, name: str) -> tuple[Any | None, dict | None]:
    """Find only a specifically authored F02 exam result."""
    wanted = _key(name)
    for item in case_data.get("exam_items", []):
        if isinstance(item, dict) and wanted in (_key(str(item.get("id", ""))),
                                                 _key(str(item.get("label", "")))):
            if item.get("value") is None and not item.get("finding"):
                return None, item
            return {
                "value": item.get("value"), "unit": item.get("unit"),
                "finding": item.get("finding"), "system": item.get("system"),
                "label": item.get("label"),
            }, item
    return None, None


def investigation_result(case_data: dict, name: str) -> tuple[Any | None, dict | None, str]:
    """Case result for a lab or imaging order, never generated defaults."""
    wanted = _key(name)
    raw = case_data.get("case_investigation_items")
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            if wanted in (_key(str(item.get("id", ""))), _key(str(item.get("label", "")))):
                rows = [
                    {"label": r.get("label"), "value": r.get("value"),
                     "unit": r.get("unit"), "ref_range": r.get("ref_range"),
                     "flag": r.get("flag")}
                    for r in item.get("results", [])
                    if isinstance(r, dict) and r.get("value") is not None
                ]
                return (rows if rows else None), item, "investigation"
    for item in case_data.get("imaging", []):
        if not isinstance(item, dict):
            continue
        if wanted in (_key(str(item.get("id", ""))), _key(str(item.get("label", "")))):
            report = item.get("report_text")
            # A private image_asset MUST NOT be sent to the client as a raw storage path.
            result = ({"report": report, "image_available": bool(item.get("image_asset")),
                       "image_status": "private_asset_requires_signed_access"}
                      if report or item.get("image_asset") else None)
            return result, item, "imaging"
    return None, None, "investigation"


def catalog_category(name: str) -> str | None:
    key = _key(name)
    for item in get_all_investigations():
        if key in (_key(item.id), _key(item.name)):
            return item.category.value
    return None


def normalized_requested(session: SimulationSession, section: str, name: str) -> bool:
    values = session.requested_examinations if section == "examination" else session.requested_investigations
    return _key(name) in {_key(v) for v in values}
