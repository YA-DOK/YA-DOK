from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from ..core.security import get_current_user
from ..schemas.hints import HintResponse
from ..services.hint_workflow import HintWorkflow
router = APIRouter(tags=["Hints"])



async def get_current_student_id(
    user: Annotated[dict, Depends(get_current_user)],
) -> str:
    """Get student ID from a verified Supabase token."""
    return user["id"]


# Will be connected to the real session database later
def get_hint_workflow() -> HintWorkflow:
    raise HTTPException(
        status_code=503,
        detail="Session store not configured"
    )


@router.post(
    "/simulations/{session_id}/hints",
    response_model=HintResponse
)
def request_hint(
    session_id: str,
    student_id: Annotated[str, Depends(get_current_student_id)],
    workflow: Annotated[HintWorkflow, Depends(get_hint_workflow)],
) -> HintResponse:

    try:
        result = workflow.request_hint(
            session_id=session_id,
            authenticated_user_id=student_id,
        )

    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        ) from exc

    except PermissionError as exc:
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid hint request"
        ) from exc

    return HintResponse(**result)
