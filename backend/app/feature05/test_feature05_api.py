
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from .standalone import app
from .ordering import ORDERS


client = TestClient(app)

SESSION_ID = f"test_{uuid4().hex}"
CASE_ID = "case_001"


def check(name, condition):
    if not condition:
        raise AssertionError(f"FAILED: {name}")

    print(f"PASS: {name}")


def run_tests():

    # 1. Health Check
    response = client.get("/health")

    check(
        "Health Check",
        response.status_code == 200
        and response.json()["status"] == "ok",
    )

    # 2. Investigation Catalog
    response = client.get(
        "/simulations/investigations/catalog"
    )

    check(
        "Investigation Catalog",
        response.status_code == 200
        and len(response.json()["investigations"]) >= 60,
    )

    # 3. Catalog Search
    response = client.get(
        "/simulations/investigations/catalog",
        params={"search": "blood"},
    )

    check(
        "Catalog Search",
        response.status_code == 200
        and any(
            item["id"] == "cbc"
            for item in response.json()["investigations"]
        ),
    )

    # 4. Available Investigations
    response = client.get(
        f"/simulations/{SESSION_ID}/available-investigations",
        params={"case_id": CASE_ID},
    )

    check(
        "Available Investigations",
        response.status_code == 200
        and len(response.json()["investigations"]) == 4,
    )

    # 5. Clinical Examination
    response = client.post(
        f"/simulations/{SESSION_ID}/examinations",
        json={
            "case_id": CASE_ID,
            "examination_id": "respiratory_exam",
        },
    )

    check(
        "Clinical Examination",
        response.status_code == 200
        and response.json()["status"] == "completed",
    )

    # 6. Duplicate Examination
    response = client.post(
        f"/simulations/{SESSION_ID}/examinations",
        json={
            "case_id": CASE_ID,
            "examination_id": "respiratory_exam",
        },
    )

    check(
        "Duplicate Examination",
        response.status_code == 200
        and response.json()["status"] == "already_performed",
    )

    # 7. Investigation Ordering
    response = client.post(
        f"/simulations/{SESSION_ID}/investigations",
        json={
            "case_id": CASE_ID,
            "investigation_id": "cbc",
        },
    )

    check(
        "Investigation Ordering",
        response.status_code == 200
        and response.json()["status"] == "pending",
    )

    # 8. Educational Evaluation
    check(
        "Educational Evaluation",
        response.json()["evaluation"]["relevance"] == "relevant",
    )

    # 9. Pending Status
    response = client.get(
        f"/simulations/{SESSION_ID}/investigations/cbc/status"
    )

    check(
        "Pending Status",
        response.status_code == 200
        and response.json()["status"] == "pending",
    )

    # 10. Pending Result
    response = client.get(
        f"/simulations/{SESSION_ID}/investigations/cbc/result"
    )

    check(
        "Pending Result",
        response.status_code == 200
        and response.json()["status"] == "pending",
    )

    # 11. Duplicate Investigation
    response = client.post(
        f"/simulations/{SESSION_ID}/investigations",
        json={
            "case_id": CASE_ID,
            "investigation_id": "cbc",
        },
    )

    check(
        "Duplicate Investigation",
        response.status_code == 200
        and response.json()["status"] == "already_ordered",
    )

    # 12. Non-relevant Investigation
    response = client.post(
        f"/simulations/{SESSION_ID}/investigations",
        json={
            "case_id": CASE_ID,
            "investigation_id": "urinalysis",
        },
    )

    check(
        "Non-relevant Investigation",
        response.status_code == 200
        and response.json()["status"] == "completed",
    )

    # 13. Normal Result Without Numbers
    response = client.get(
        f"/simulations/{SESSION_ID}"
        "/investigations/urinalysis/result"
    )

    check(
        "Simulated Normal Result Without Numbers",
        response.status_code == 200
        and response.json()["status"] == "completed"
        and response.json()["result"]["simulated_normal"] is True
        and response.json()["result"]["result_type"]
        == "synthetic_qualitative_normal"
        and response.json()["result"]["measurements"] == []
        and "normal" in response.json()["result"]["findings"].lower(),
    )

    # 14. Session Case Protection
    response = client.post(
        f"/simulations/{SESSION_ID}/investigations",
        json={
            "case_id": "different_case",
            "investigation_id": "cbc",
        },
    )

    check(
        "Session Case Protection",
        response.status_code == 409,
    )

    # 15. Simulate CBC Result Release
    ORDERS[(SESSION_ID, "cbc")]["ready_at"] = (
        datetime.now(timezone.utc)
        - timedelta(seconds=1)
    )

    response = client.get(
        f"/simulations/{SESSION_ID}/investigations/cbc/result"
    )

    check(
        "Completed Investigation Result",
        response.status_code == 200
        and response.json()["status"] == "completed"
        and "result" in response.json(),
    )

    # 16. Session Event Logging
    response = client.get(
        f"/simulations/{SESSION_ID}/investigation-events"
    )

    events = response.json()["events"]

    check(
        "Session Event Logging",
        response.status_code == 200
        and len(events) == 5,
    )

    # 17. No Duplicate Penalty
    check(
        "No Duplicate Penalty",
        all(
            event["penalty"] == 0
            for event in events
            if event["status"] in (
                "already_ordered",
                "already_performed",
            )
        ),
    )

    # 18. Request Validation
    response = client.post(
        f"/simulations/{SESSION_ID}/investigations",
        json={
            "case_id": CASE_ID,
            "investigation_id": "",
        },
    )

    check(
        "Request Validation",
        response.status_code == 422,
    )

    print("\nALL FEATURE 05 API TESTS PASSED!")


if __name__ == "__main__":
    run_tests()
