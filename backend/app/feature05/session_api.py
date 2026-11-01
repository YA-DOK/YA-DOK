"""F05 add-on routes: session-owned safe catalog and private image proxy.

No independent SESSION_CASES or global in-memory ORDERS are used.
"""
from __future__ import annotations

import os
from typing import Annotated
from urllib.parse import quote
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Response

from app.core.config import settings
from app.core.security import get_current_user
from app.feature05.clinical_integration import clinical_options

router = APIRouter(prefix="/simulation/sessions", tags=["Clinical Tools F05"])
CurrentUser = Annotated[dict, Depends(get_current_user)]


def _owned_session(session_id: str, user: dict):
    from app.api.routes.simulation import _pg_service, get_owned_session
    from app.services.simulation_pg_service import SessionNotFound
    try:
        UUID(session_id)
        if (pg := _pg_service()) is not None:
            return pg.load(str(user["id"]), session_id)
        return get_owned_session(session_id, user)
    except (SessionNotFound, ValueError, TypeError, KeyError) as exc:
        raise HTTPException(404, "Simulation session not found.") from exc


@router.get("/{session_id}/clinical-options")
def available(session_id: str, user: CurrentUser, search: str = ""):
    if len(search) > 100:
        raise HTTPException(422, "Search is too long.")
    return clinical_options(_owned_session(session_id,user),search)


@router.get("/{session_id}/clinical-review")
def review_completed_session(session_id: str, user: CurrentUser):
    from app.feature05.clinical_review import build_clinical_review
    session = _owned_session(session_id, user)
    if not session.is_completed:
        raise HTTPException(409, "Clinical review is available only after completion.")
    return build_clinical_review(session)


@router.get("/{session_id}/imaging/{image_id}/asset")
async def private_case_image(session_id: str, image_id: str, user: CurrentUser):
    """Never expose raw storage path or server credentials to browser."""
    session = _owned_session(session_id,user)
    if not any(str(x).strip().casefold() == image_id.strip().casefold()
               for x in session.requested_investigations):
        raise HTTPException(404, "Image has not been requested.")
    item = next((x for x in session.case_data.get("imaging",[]) if isinstance(x,dict)
                 and str(x.get("id","")).casefold()==image_id.casefold()),None)
    if not item or not item.get("image_asset"):
        raise HTTPException(404, "No case image available.")
    path = str(item["image_asset"])
    # Only approved relative private Storage paths. External URLs and traversal are refused.
    if (not path or path.startswith("/") or "\\" in path or "?" in path or "#" in path
            or ":" in path or any(seg in ("", ".", "..") for seg in path.split("/"))):
        raise HTTPException(404, "Invalid private image asset.")
    key = os.environ.get("F05_SUPABASE_SERVICE_ROLE_KEY", "")
    bucket = os.environ.get("F05_PRIVATE_BUCKET", "")
    url = settings.supabase_url.rstrip("/")
    if not key or not bucket or not url.startswith("https://"):
        raise HTTPException(503, "Private imaging storage is not configured.")
    if not bucket.replace("-", "").replace("_", "").isalnum():
        raise HTTPException(503, "Private imaging bucket configuration invalid.")
    # Supabase Object API (server-side service role); no user-controlled host.
    resource = f"{url}/storage/v1/object/authenticated/{quote(bucket,safe='')}/{quote(path,safe='/')}"
    async with httpx.AsyncClient(timeout=httpx.Timeout(20.0,connect=4.0),follow_redirects=False) as client:
        try:
            result = await client.get(resource,headers={"Authorization":f"Bearer {key}","apikey":key})
        except httpx.HTTPError as exc:
            raise HTTPException(502, "Imaging service unavailable.") from exc
    if result.status_code != 200:
        raise HTTPException(404, "Case image could not be retrieved.")
    kind = result.headers.get("content-type","").split(";")[0].lower()
    if kind not in ("image/png","image/jpeg","image/webp") or len(result.content)>8*1024*1024:
        raise HTTPException(422, "Unsupported image asset.")
    return Response(result.content,media_type=kind,headers={"Cache-Control":"private, no-store","X-Content-Type-Options":"nosniff"})
