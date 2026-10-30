from fastapi import APIRouter, Depends, HTTPException
from ..auth import require_admin
from ..db import get_supabase
from app.auth import require_admin
from ..schemas import CaseCreate, StatusUpdate
from fastapi import APIRouter, Depends
from ..auth import require_admin

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)]
)


@router.get("/cases")
def list_all_cases(_admin=Depends(require_admin), limit: int = 100, offset: int = 0):
    result = get_supabase().table("cases").select(
        "id, case_code, title, specialty, difficulty"
    ).order("title").range(offset, offset + min(limit, 100) - 1).execute()
    return {"items": result.data or []}

@router.get("/cases/{case_id}")
def get_case_admin(case_id: str, _admin=Depends(require_admin)):
    case = get_supabase().table("cases").select("*").eq("id", case_id).limit(1).execute()
    if not case.data:
        raise HTTPException(status_code=404, detail="Case not found")
    versions = get_supabase().table("case_versions").select("*").eq(
        "case_id", case_id
    ).order("created_at", desc=True).execute()
    return {"case": case.data[0], "versions": versions.data or []}

@router.post("/cases", status_code=201)
def create_case(payload: CaseCreate, _admin=Depends(require_admin)):
    db = get_supabase()
    existing = db.table("cases").select("id").eq(
        "case_code", payload.case_code
    ).limit(1).execute()
    if existing.data:
        raise HTTPException(status_code=409, detail="case_code already exists")
    inserted = db.table("cases").insert({
        "case_code": payload.case_code,
        "title": payload.title,
        "specialty": payload.specialty,
        "difficulty": payload.difficulty,
    }).execute()
    if not inserted.data:
        raise HTTPException(status_code=500, detail="Could not create case row")
    case_id = inserted.data[0]["id"]
    try:
        version = db.table("case_versions").insert({
            "case_id": case_id,
            "version_number": payload.version_number,
            "status": payload.status,
            "blueprint_data": payload.blueprint_data,
            "xray_path": payload.xray_path,
        }).execute()
        return {"case": inserted.data[0], "version": version.data[0] if version.data else None}
    except Exception as exc:
        # Only remove the parent row created by this request.
        db.table("cases").delete().eq("id", case_id).execute()
        raise HTTPException(status_code=400, detail=f"Version insert failed: {exc}")

@router.patch("/cases/{case_id}/versions/{version_id}/status")
def update_version_status(
    case_id: str, version_id: str, payload: StatusUpdate,
    _admin=Depends(require_admin)
):
    result = get_supabase().table("case_versions").update({
        "status": payload.status
    }).eq("id", version_id).eq("case_id", case_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Case version not found")
    return {"version": result.data[0]}
