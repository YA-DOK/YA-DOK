
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from .standalone import app
from .ordering import ORDERS


client = TestClient(app)


def test_xray_image_flow():
    session = f"image_test_{uuid4().hex}"
    plain_url = f"/simulations/{session}/investigations/chest_xray/image"

    # No signed link: blocked
    assert client.get(plain_url).status_code == 403

    # Order X-ray: pending
    response = client.post(
        f"/simulations/{session}/investigations",
        json={"case_id": "case_001", "investigation_id": "chest_xray"},
    )
    assert response.json()["status"] == "pending"

    # Result not released yet: no image link
    result = client.get(
        f"/simulations/{session}/investigations/chest_xray/result"
    ).json()
    assert result["status"] == "pending"

    # Simulate release
    key = (session, "chest_xray")
    order = ORDERS[key].copy()
    order["ready_at"] = datetime.now(timezone.utc) - timedelta(seconds=1)
    ORDERS[key] = order

    # Released: signed link is issued and works
    result = client.get(
        f"/simulations/{session}/investigations/chest_xray/result"
    ).json()
    image_url = result["result"]["image_url"]

    response = client.get(image_url)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/")
    assert len(response.content) > 0
