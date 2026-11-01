"""No public image URLs; only requested, case-authored assets may be viewed."""
import pytest
from fastapi import HTTPException

from app.feature05 import session_api
from app.simulation.engine import create_session


def _session():
    return create_session({"imaging": [{"id":"cxr","label":"Chest X-ray", "image_asset":"case/xray.png", "report_text":"case-defined"}]})


@pytest.mark.asyncio
async def test_image_denied_before_order(monkeypatch):
    s=_session()
    monkeypatch.setattr(session_api,"_owned_session",lambda sid,user:s)
    with pytest.raises(HTTPException) as e:
        await session_api.private_case_image(s.session_id,"cxr",{"id":"tester"})
    assert e.value.status_code==404


@pytest.mark.asyncio
async def test_image_missing_storage_fails_closed(monkeypatch):
    s=_session()
    s.requested_investigations.append("cxr")
    monkeypatch.setattr(session_api,"_owned_session",lambda sid,user:s)
    monkeypatch.delenv("F05_SUPABASE_SERVICE_ROLE_KEY",raising=False)
    monkeypatch.delenv("F05_PRIVATE_BUCKET",raising=False)
    with pytest.raises(HTTPException) as e:
        await session_api.private_case_image(s.session_id,"cxr",{"id":"tester"})
    assert e.value.status_code==503


@pytest.mark.asyncio
async def test_external_image_path_rejected(monkeypatch):
    s=_session()
    s.requested_investigations.append("cxr")
    s.case_data["imaging"][0]["image_asset"]="https://bad.example/x.png"
    monkeypatch.setattr(session_api,"_owned_session",lambda sid,user:s)
    with pytest.raises(HTTPException) as e:
        await session_api.private_case_image(s.session_id,"cxr",{"id":"tester"})
    assert e.value.status_code==404
