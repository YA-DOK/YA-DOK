
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from .json_loader import get_case_by_id
from .ordering import ORDERS, SESSION_CASES, get_investigation_status
from .security import verify_signature


router = APIRouter(
    prefix="/simulations",
    tags=["Feature 05 - Medical Images"],
)

BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = (BASE_DIR / "Data" / "medical_images").resolve()

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

MEDIA_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


@router.get(
    "/{session_id}/investigations/{investigation_id}/image"
)
def get_investigation_image(
    session_id: str,
    investigation_id: str,
    exp: int | None = None,
    sig: str | None = None,
):
    # 0. Time-limited signed link (issued with the released result)
    if not verify_signature(session_id, investigation_id, exp, sig):
        raise HTTPException(
            status_code=403,
            detail="Invalid or expired image link",
        )

    # 1. Investigation must have been ordered
    order = ORDERS.get((session_id, investigation_id))

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Investigation has not been ordered",
        )

    # 2. Result must be released
    status = get_investigation_status(session_id, investigation_id)

    if status["status"] != "completed":
        raise HTTPException(
            status_code=409,
            detail="Investigation result is not ready yet",
        )

    # 3. Session and case must match
    case_id = order["case_id"]

    if SESSION_CASES.get(session_id) != case_id:
        raise HTTPException(
            status_code=403,
            detail="Session and case do not match",
        )

    # 4. Case-defined result
    case_data = get_case_by_id(case_id)

    if case_data is None:
        raise HTTPException(status_code=404, detail="Case not found")

    result = case_data.get("investigation_results", {}).get(
        investigation_id
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Investigation result not configured",
        )

    image_path = result.get("image_path")

    if not image_path:
        raise HTTPException(
            status_code=404,
            detail="No image configured for this investigation",
        )

    resolved_path = (BASE_DIR / image_path).resolve()

    # 5. Never serve files outside medical_images
    if not resolved_path.is_relative_to(IMAGES_DIR):
        raise HTTPException(status_code=400, detail="Invalid image path")

    if (
        resolved_path.suffix.lower() not in ALLOWED_EXTENSIONS
        or not resolved_path.is_file()
    ):
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(
        path=resolved_path,
        media_type=MEDIA_TYPES[resolved_path.suffix.lower()],
        filename=resolved_path.name,
        content_disposition_type="inline",
        headers={"Cache-Control": "private, no-store"},
    )
