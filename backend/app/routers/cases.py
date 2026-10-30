from fastapi import APIRouter, HTTPException, Query
from ..db import get_supabase
from ..config import BUCKET_NAME, SIGNED_URL_SECONDS

router = APIRouter(tags=["cases"])

def _get_version(case_id: str, published_only: bool = True):
    query = (
        get_supabase().table("case_versions")
        .select("id, case_id, version_number, status, blueprint_data, xray_path, created_at")
        .eq("case_id", case_id)
        .order("created_at", desc=True)
    )
    if published_only:
        query = query.eq("status", "published")
    result = query.limit(1).execute()
    return result.data[0] if result.data else None

@router.get("/cases")
def list_published_cases(
    specialty: str | None = None,
    difficulty: str | None = None,
    q: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    # The importer stores metadata in cases and the clinical JSON in case_versions.
    result = get_supabase().table("cases").select(
        "id, case_code, title, specialty, difficulty"
    ).order("title").range(offset, offset + limit - 1).execute()

    rows = []
    for case in result.data or []:
        if specialty and (case.get("specialty") or "").lower() != specialty.lower():
            continue
        if difficulty and case.get("difficulty") != difficulty:
            continue
        if q and q.lower() not in (
            str(case.get("title", "")) + " " + str(case.get("case_code", ""))
        ).lower():
            continue
        version = _get_version(str(case["id"]), published_only=True)
        if version:
            rows.append({
                **case,
                "version_id": version["id"],
                "version_number": version["version_number"],
                "status": version["status"],
            })
    return {"items": rows, "count": len(rows), "limit": limit, "offset": offset}

@router.get("/cases/{case_id}")
def get_published_case(case_id: str):
    case_result = get_supabase().table("cases").select(
        "id, case_code, title, specialty, difficulty"
    ).eq("id", case_id).limit(1).execute()
    if not case_result.data:
        raise HTTPException(status_code=404, detail="Case not found")
    version = _get_version(case_id, published_only=True)
    if not version:
        raise HTTPException(status_code=404, detail="No published version for this case")
    return {"case": case_result.data[0], "version": version}

@router.get("/cases/{case_id}/image")
def get_case_image(case_id: str):
    version = _get_version(case_id, published_only=True)
    if not version:
        raise HTTPException(status_code=404, detail="No published version for this case")
    path = version.get("xray_path")
    if not path:
        raise HTTPException(status_code=404, detail="This case has no linked X-ray image")
    try:
        signed = get_supabase().storage.from_(BUCKET_NAME).create_signed_url(
            path, SIGNED_URL_SECONDS
        )
        url = signed.get("signedURL") or signed.get("signedUrl")
        if not url:
            raise RuntimeError("Supabase did not return a signed URL")
        return {"image_url": url, "expires_in": SIGNED_URL_SECONDS}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not create image URL: {exc}")
