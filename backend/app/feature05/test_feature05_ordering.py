
from app.feature05.ordering import (
    order_investigation,
    get_investigation_status,
    get_investigation_result,
)
from app.feature05.events import get_session_events


def check(name, condition):
    assert condition, f"FAILED: {name}"
    print(f"PASS: {name}")


session = "test_step13_session"


# 1. Before ordering
status = get_investigation_status(session, "cbc")

check(
    "Not ordered",
    status["status"] == "not_ordered",
)


# 2. First order
first = order_investigation(
    session,
    "case_001",
    "cbc",
)

check(
    "First order",
    first["status"] == "pending",
)


# 3. Educational evaluation
check(
    "Educational evaluation",
    first["evaluation"]["relevance"] == "relevant"
    and first["evaluation"]["penalty"] == 0,
)


# 4. Pending with release time
status = get_investigation_status(session, "cbc")

check(
    "Pending with release time",
    status["status"] == "pending"
    and "ready_at" in status,
)


# 5. Result not ready
result = get_investigation_result(session, "cbc")

check(
    "Pending result",
    result["status"] == "pending",
)


# 6. Duplicate order
second = order_investigation(
    session,
    "case_001",
    "cbc",
)

check(
    "Duplicate rejected",
    second["status"] == "already_ordered",
)


# 7. Non-relevant investigation
unrelated = order_investigation(
    session,
    "case_001",
    "urinalysis",
)

check(
    "Non-relevant investigation returns completed",
    unrelated["status"] == "completed",
)


# 8. Synthetic normal result
normal_result = get_investigation_result(
    session,
    "urinalysis",
)

check(
    "Simulated normal result without measurements",
    normal_result["status"] == "completed"
    and normal_result["result"]["simulated_normal"] is True
    and normal_result["result"]["result_type"]
    == "synthetic_qualitative_normal"
    and normal_result["result"]["measurements"] == []
    and "normal" in normal_result["result"]["findings"].lower(),
)


# 9. Session case protection
wrong_case = order_investigation(
    session,
    "case_002",
    "cbc",
)

check(
    "Session case protection",
    wrong_case["status"] == "error",
)


# 10. Event logging
events = get_session_events(session)

statuses = [
    event["status"]
    for event in events
]

check(
    "All attempts recorded",
    statuses == [
        "pending",
        "already_ordered",
        "completed",
    ],
)


# 11. No duplicate penalty
check(
    "No duplicate penalty",
    events[1]["penalty"] == 0,
)


print("\nALL UPDATED FEATURE 05 ORDERING TESTS PASSED!")
