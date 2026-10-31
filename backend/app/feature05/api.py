
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from .json_loader import get_case_by_id

from .catalog import (
    get_all_investigations,
    search_investigations,
)

from .schemas import InvestigationCategory

from .service import (
    perform_examination,
    PERFORMED_EXAMINATIONS,
)

from .ordering import (
    order_investigation,
    get_investigation_status,
    get_investigation_result,
    SESSION_CASES,
)

from .events import get_session_events

from .views import (
    public_case,
    public_evaluation,
    public_event,
    public_result,
    clean_result,
)


router = APIRouter(
    prefix="/simulations",
    tags=["Feature 05 - Clinical Examinations"],
)


# ---------- request models ----------

class InvestigationOrderBody(BaseModel):
    case_id: str = Field(min_length=1)
    investigation_id: str = Field(min_length=1)


class ExaminationBody(BaseModel):
    case_id: str = Field(min_length=1)
    examination_id: str = Field(min_length=1)


# ---------- helpers ----------

def validate_session_case(session_id: str, case_id: str):

    existing_case = SESSION_CASES.get(session_id)

    if existing_case is not None and existing_case != case_id:
        raise HTTPException(
            status_code=409,
            detail="Session belongs to another case",
        )


def clean_action_response(response: dict) -> dict:
    """Remove internal data from order / examination responses."""

    response = dict(response)

    if "evaluation" in response:
        response["evaluation"] = public_evaluation(
            response["evaluation"]
        )

    if isinstance(response.get("result"), dict):
        response["result"] = clean_result(response["result"])

    return response


# ---------- 1. universal catalog ----------

@router.get("/investigations/catalog")
def investigation_catalog(
    search: str = Query(default="", max_length=100),
    category: InvestigationCategory | None = Query(default=None),
):

    items = search_investigations(query=search, category=category)
    all_items = get_all_investigations()

    categories = []

    for category_item in InvestigationCategory:

        if any(item.category == category_item for item in all_items):
            categories.append({
                "id": category_item.value,
                "name": category_item.value.replace("_", " ").title(),
            })

    return {
        "investigations": [
            item.model_dump(mode="json") for item in items
        ],
        "total": len(items),
        "categories": categories,
    }


# ---------- 2. available investigations ----------

@router.get("/{session_id}/available-investigations")
def available_investigations(
    session_id: str,
    case_id: str = Query(...),
    search: str = Query(default=""),
):

    validate_session_case(session_id, case_id)

    case_data = get_case_by_id(case_id)

    if case_data is None:
        raise HTTPException(status_code=404, detail="Case not found")

    available_ids = case_data.get("available_investigations", [])

    items = []

    for item in get_all_investigations():

        if item.id not in available_ids:
            continue

        searchable = (
            item.id + " " + item.name + " " + (item.description or "")
        ).lower()

        if search.strip() and search.lower().strip() not in searchable:
            continue

        if item.category in (
            InvestigationCategory.GENERAL,
            InvestigationCategory.SYSTEM,
        ):
            performed = (session_id, item.id) in PERFORMED_EXAMINATIONS
            status = "completed" if performed else "available"

        else:
            order_status = get_investigation_status(
                session_id, item.id
            )["status"]

            status = (
                "available"
                if order_status == "not_ordered"
                else order_status
            )

        items.append({**item.model_dump(mode="json"), "status": status})

    return {
        "session_id": session_id,
        "case_id": case_id,
        "investigations": items,
        "total": len(items),
    }


# ---------- 3. case summary (student-safe) ----------

@router.get("/{session_id}/case")
def get_simulation_case(
    session_id: str,
    case_id: str = Query(...),
):

    validate_session_case(session_id, case_id)

    case_data = get_case_by_id(case_id)

    if case_data is None:
        raise HTTPException(status_code=404, detail="Case not found")

    SESSION_CASES[session_id] = case_id

    # Diagnosis, treatment, outcome, timeline, hospital and
    # source notes are NOT returned to the student.
    return public_case(case_data)


# ---------- 4. clinical examination ----------

@router.post("/{session_id}/examinations")
def clinical_examination(
    session_id: str,
    body: ExaminationBody,
):

    validate_session_case(session_id, body.case_id)

    if get_case_by_id(body.case_id) is None:
        raise HTTPException(status_code=404, detail="Case not found")

    result = perform_examination(
        case_id=body.case_id,
        examination_id=body.examination_id,
        session_id=session_id,
    )

    if result.get("status") == "error":
        raise HTTPException(
            status_code=400,
            detail=result.get("message"),
        )

    return clean_action_response(result)


# ---------- 5. order investigation ----------

@router.post("/{session_id}/investigations")
def create_investigation_order(
    session_id: str,
    body: InvestigationOrderBody,
):

    validate_session_case(session_id, body.case_id)

    if get_case_by_id(body.case_id) is None:
        raise HTTPException(status_code=404, detail="Case not found")

    response = order_investigation(
        session_id,
        body.case_id,
        body.investigation_id,
    )

    if response.get("status") == "error":
        message = response.get("message", "Request failed")
        code = 404 if "not found" in message.lower() else 400
        raise HTTPException(status_code=code, detail=message)

    return clean_action_response(response)


# ---------- 6. status ----------

@router.get("/{session_id}/investigations/{investigation_id}/status")
def investigation_status(
    session_id: str,
    investigation_id: str,
):
    return get_investigation_status(session_id, investigation_id)


# ---------- 7. result (student-safe, signed image link) ----------

@router.get("/{session_id}/investigations/{investigation_id}/result")
def investigation_result(
    session_id: str,
    investigation_id: str,
):

    response = get_investigation_result(session_id, investigation_id)

    if response.get("status") != "completed":
        return response

    return {
        "status": "completed",
        "investigation_id": investigation_id,
        "result": public_result(
            session_id,
            investigation_id,
            response["result"],
        ),
        "evaluation": public_evaluation(response["evaluation"]),
    }


# ---------- 8. session events ----------

@router.get("/{session_id}/investigation-events")
def investigation_events(session_id: str):

    return {
        "session_id": session_id,
        "events": [
            public_event(event)
            for event in get_session_events(session_id)
        ],
    }
