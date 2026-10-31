
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from .standalone import app
from .ordering import ORDERS


client = TestClient(app)


def _new_session():
    return f"sec_test_{uuid4().hex}"


def _release(session, investigation_id):
    key = (session, investigation_id)
    order = ORDERS[key].copy()
    order["ready_at"] = datetime.now(timezone.utc) - timedelta(seconds=1)
    ORDERS[key] = order


def _order_xray(session):
    response = client.post(
        f"/simulations/{session}/investigations",
        json={"case_id": "case_001", "investigation_id": "chest_xray"},
    )
    assert response.status_code == 200
    return response.json()


def test_image_blocked_without_signed_link():
    session = _new_session()
    url = f"/simulations/{session}/investigations/chest_xray/image"

    assert client.get(url).status_code == 403


def test_signed_link_flow():
    session = _new_session()
    _order_xray(session)
    _release(session, "chest_xray")

    body = client.get(
        f"/simulations/{session}/investigations/chest_xray/result"
    ).json()

    result = body["result"]

    assert "image_url" in result
    assert "image_path" not in result
    assert "source_notes" not in result
    assert "source_page" not in result

    ok = client.get(result["image_url"])
    assert ok.status_code == 200
    assert ok.headers["content-type"].startswith("image/")

    tampered = client.get(result["image_url"] + "0")
    assert tampered.status_code == 403


def test_signed_link_for_other_session_is_rejected():
    session_a = _new_session()
    session_b = _new_session()

    _order_xray(session_a)
    _release(session_a, "chest_xray")

    link = client.get(
        f"/simulations/{session_a}/investigations/chest_xray/result"
    ).json()["result"]["image_url"]

    stolen = link.replace(session_a, session_b)
    assert client.get(stolen).status_code == 403


def test_pending_result_has_no_image():
    session = _new_session()
    _order_xray(session)

    body = client.get(
        f"/simulations/{session}/investigations/chest_xray/result"
    ).json()

    assert body["status"] == "pending"
    assert "result" not in body


def test_case_view_hides_internal_data():
    session = _new_session()

    body = client.get(
        f"/simulations/{session}/case", params={"case_id": "case_002"}
    ).json()

    for hidden in (
        "working_diagnosis",
        "treatment",
        "outcome_summary",
        "clinical_timeline",
        "encounter",
        "vitals_trend",
    ):
        assert hidden not in body


def test_unrelated_test_returns_simulated_normal_with_penalty():
    session = _new_session()

    client.get(
        f"/simulations/{session}/case", params={"case_id": "case_002"}
    )

    response = client.post(
        f"/simulations/{session}/investigations",
        json={"case_id": "case_002", "investigation_id": "urinalysis"},
    )

    assert response.status_code == 200
    assert response.json()["evaluation"]["relevance"] == "unnecessary"
    assert response.json()["evaluation"]["penalty"] > 0
