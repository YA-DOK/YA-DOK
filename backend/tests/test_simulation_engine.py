
import pytest
from backend.app.simulation.engine import (
    InvalidPhaseTransition,
    SimulationPhase,
    get_next_phase,
    transition_phase,
)


def test_get_next_phase_from_introduction():
    assert (
        get_next_phase(SimulationPhase.INTRODUCTION)
        == SimulationPhase.HISTORY_TAKING
    )


def test_completed_has_no_next_phase():
    assert get_next_phase(SimulationPhase.COMPLETED) is None


def test_valid_transition():
    result = transition_phase(
        SimulationPhase.INTRODUCTION,
        SimulationPhase.HISTORY_TAKING,
    )
    assert result == SimulationPhase.HISTORY_TAKING


def test_cannot_skip_a_phase():
    with pytest.raises(InvalidPhaseTransition):
        transition_phase(
            SimulationPhase.INTRODUCTION,
            SimulationPhase.EXAMINATION,
        )


def test_cannot_move_backwards():
    with pytest.raises(InvalidPhaseTransition):
        transition_phase(
            SimulationPhase.EXAMINATION,
            SimulationPhase.HISTORY_TAKING,
        )


def test_cannot_transition_after_completion():
    with pytest.raises(InvalidPhaseTransition):
        transition_phase(
            SimulationPhase.COMPLETED,
            SimulationPhase.INTRODUCTION,
        )

from backend.app.simulation.engine import (
    SimulationError,
    advance_phase,
    ask_patient,
    complete_session,
    create_session,
    request_examination,
    request_investigation,
    submit_diagnosis_and_plan,
)


def make_test_session():
    return create_session(
        {
            "symptoms": ["fever", "cough"],
            "examination": {
                "temperature": "38 C",
            },
            "investigations": {
                "CBC": {
                    "white_blood_cells": "12000",
                },
            },
        }
    )


def move_to_phase(session, target_phase):
    while session.current_phase != target_phase:
        next_phase = get_next_phase(session.current_phase)
        advance_phase(session, next_phase)


def test_create_session_starts_at_introduction():
    session = make_test_session()

    assert session.current_phase == SimulationPhase.INTRODUCTION
    assert session.is_completed is False
    assert session.session_id


def test_patient_question_available_without_phase_transition():
    session = make_test_session()

    reply = ask_patient(session, "Do you have a fever?")
    assert reply
    assert session.current_phase == SimulationPhase.INTRODUCTION
    assert session.events[-1].event_type == "patient_response"


def test_patient_question_uses_responder():
    session = make_test_session()
    move_to_phase(session, SimulationPhase.HISTORY_TAKING)

    response = ask_patient(
        session,
        "Do you have a fever?",
        responder=lambda **kwargs: "Yes, I have a fever.",
    )

    assert response == "Yes, I have a fever."
    assert session.messages[-1].role == "assistant"


def test_examination_returns_only_existing_results():
    session = make_test_session()
    move_to_phase(session, SimulationPhase.EXAMINATION)

    result = request_examination(session, "temperature")

    assert result["available"] is True
    assert result["result"] == "38 C"

    missing = request_examination(session, "heart sounds")

    assert missing["available"] is False
    assert missing["result"] is None


def test_investigation_returns_only_existing_results():
    session = make_test_session()
    move_to_phase(session, SimulationPhase.INVESTIGATIONS)

    result = request_investigation(session, "CBC")

    assert result["available"] is True
    assert result["result"]["white_blood_cells"] == "12000"

    missing = request_investigation(session, "MRI")

    assert missing["available"] is False
    assert missing["result"] is None


def test_session_requires_diagnosis_before_completion():
    session = make_test_session()
    move_to_phase(session, SimulationPhase.DIAGNOSIS_AND_PLAN)

    with pytest.raises(SimulationError):
        complete_session(session)


def test_session_can_be_completed():
    session = make_test_session()
    move_to_phase(session, SimulationPhase.DIAGNOSIS_AND_PLAN)

    submit_diagnosis_and_plan(
        session,
        diagnosis="Example diagnosis",
        treatment_plan="Example treatment plan",
    )

    result = complete_session(session)

    assert result["is_completed"] is True
    assert result["current_phase"] == "completed"


import asyncio

from backend.app.simulation.engine import ask_patient_async


def test_async_patient_agent_integration():
    class FakePatientAgent:
        async def respond(self, case_data, messages, question):
            assert case_data["symptoms"] == ["fever"]
            assert question == "Do you have a fever?"
            return "Yes, I have a fever."

    session = create_session({"symptoms": ["fever"]})
    move_to_phase(session, SimulationPhase.HISTORY_TAKING)

    response = asyncio.run(
        ask_patient_async(
            session=session,
            question="Do you have a fever?",
            patient_agent=FakePatientAgent(),
        )
    )

    assert response == "Yes, I have a fever."
    assert session.messages[-1].role == "assistant"
    assert session.messages[-1].action == "patient_response"
    assert session.messages[-1].content == response


def test_patient_agent_with_provider_integration():
    import asyncio

    from backend.app.simulation.factory import create_patient_agent

    class FakeLLM:
        async def generate(self, messages, **kwargs):
            assert messages[0]["role"] == "system"
            assert all(x in messages[0]["content"] for x in ('"symptoms"', '"duration"', "fever", "one day"))
            return "Yes, I have had a fever since yesterday."

    agent = create_patient_agent()
    agent.llm_service = FakeLLM()

    session = create_session({
        "symptoms": ["fever"],
        "duration": "one day",
    })

    move_to_phase(session, SimulationPhase.HISTORY_TAKING)

    response = asyncio.run(
        ask_patient_async(
            session=session,
            question="How long have you had a fever?",
            patient_agent=agent,
        )
    )

    assert response == "Yes, I have had a fever since yesterday."
    assert session.messages[-1].role == "assistant"
    assert session.messages[-1].content == response


def test_session_creation_records_event():
    session = make_test_session()

    assert session.events
    assert session.events[0].event_type == "session_created"
    assert session.events[0].phase == SimulationPhase.INTRODUCTION


def test_phase_transition_records_ordered_event():
    session = make_test_session()

    advance_phase(session, SimulationPhase.HISTORY_TAKING)

    event = session.events[-1]

    assert event.event_type == "phase_changed"
    assert event.details["from_phase"] == "introduction"
    assert event.details["to_phase"] == "history_taking"


def test_patient_question_and_response_are_logged():
    session = make_test_session()
    move_to_phase(session, SimulationPhase.HISTORY_TAKING)

    ask_patient(
        session,
        "Do you have a fever?",
        responder=lambda **kwargs: "Yes.",
    )

    event_types = [event.event_type for event in session.events]

    assert event_types[-2:] == [
        "patient_question",
        "patient_response",
    ]


def test_event_serialization_contains_timestamp_and_id():
    session = make_test_session()

    event = session.to_dict()["events"][0]

    assert event["event_id"]
    assert event["event_type"] == "session_created"
    assert event["timestamp"]
    assert event["phase"] == "introduction"
    assert isinstance(event["details"], dict)


def test_invalid_transition_does_not_record_transition_event():
    session = make_test_session()
    initial_event_count = len(session.events)

    with pytest.raises(InvalidPhaseTransition):
        advance_phase(session, SimulationPhase.EXAMINATION)

    assert len(session.events) == initial_event_count
    assert session.current_phase == SimulationPhase.INTRODUCTION

def test_cannot_bypass_diagnosis_with_direct_phase_transition():
    session = make_test_session()
    move_to_phase(session, SimulationPhase.DIAGNOSIS_AND_PLAN)
    initial_events = len(session.events)

    with pytest.raises(SimulationError):
        advance_phase(session, SimulationPhase.COMPLETED)

    assert session.current_phase == SimulationPhase.DIAGNOSIS_AND_PLAN
    assert session.is_completed is False
    assert len(session.events) == initial_events


@pytest.mark.parametrize(
    "starting_phase",
    [
        SimulationPhase.INTRODUCTION,
        SimulationPhase.HISTORY_TAKING,
        SimulationPhase.EXAMINATION,
        SimulationPhase.INVESTIGATIONS,
        SimulationPhase.DIAGNOSIS_AND_PLAN,
    ],
)
def test_early_finish_from_any_phase(starting_phase):
    session = make_test_session()
    move_to_phase(session, starting_phase)
    submit_diagnosis_and_plan(session, "Provisional diagnosis", "")

    result = complete_session(session)

    assert result["is_completed"] is True
    assert result["current_phase"] == "completed"
    assert result["diagnosis"] == "Provisional diagnosis"
    assert result["treatment_plan"] == ""
    assert [event.event_type for event in session.events][-2:] == [
        "phase_changed", "session_completed",
    ]
    assert session.events[-2].details["from_phase"] == starting_phase.value
    with pytest.raises(SimulationError):
        complete_session(session)


def test_early_completion_still_requires_diagnosis():
    session = make_test_session()
    with pytest.raises(SimulationError):
        complete_session(session)
    assert session.current_phase == SimulationPhase.INTRODUCTION
    assert session.is_completed is False


from datetime import timedelta

from backend.app.simulation.engine import expire_test_session_if_due


def test_test_mode_timeout_records_completion_once():
    session = make_test_session()
    session.mode = "test"
    session.duration_minutes = 20
    created = session.events[0].timestamp
    assert not expire_test_session_if_due(session, now=created + timedelta(minutes=19))
    assert not session.is_completed
    assert expire_test_session_if_due(session, now=created + timedelta(minutes=20))
    assert session.is_completed
    assert session.current_phase == SimulationPhase.COMPLETED
    assert session.diagnosis is None
    assert session.events[-2].event_type == "session_timed_out"
    assert session.events[-1].details["reason"] == "time_limit"
    count = len(session.events)
    assert not expire_test_session_if_due(session, now=created + timedelta(minutes=30))
    assert len(session.events) == count


def test_training_never_expires_when_duration_is_display_only():
    session = make_test_session()
    session.mode = "training"
    session.duration_minutes = 1
    assert not expire_test_session_if_due(
        session, now=session.events[0].timestamp + timedelta(days=7)
    )
    assert not session.is_completed


def test_untimed_test_sessions_do_not_expire():
    session = make_test_session()
    session.mode = "test"
    session.duration_minutes = None
    assert not expire_test_session_if_due(
        session, now=session.events[0].timestamp + timedelta(days=7)
    )


@pytest.mark.parametrize(
    "phase",
    [
        SimulationPhase.INTRODUCTION,
        SimulationPhase.HISTORY_TAKING,
        SimulationPhase.EXAMINATION,
        SimulationPhase.INVESTIGATIONS,
        SimulationPhase.DIAGNOSIS_AND_PLAN,
    ],
)
def test_clinical_actions_work_in_any_live_phase(phase):
    session = make_test_session()
    move_to_phase(session, phase)

    assert ask_patient(session, "Hello")
    assert request_examination(session, "temperature")["available"] is True
    assert request_investigation(session, "CBC")["available"] is True
    assert session.current_phase == phase


def test_clinical_actions_rejected_after_completion():
    session = make_test_session()
    submit_diagnosis_and_plan(session, "Example diagnosis", "")
    complete_session(session)
    with pytest.raises(SimulationError):
        ask_patient(session, "Hello")
    with pytest.raises(SimulationError):
        request_examination(session, "temperature")
    with pytest.raises(SimulationError):
        request_investigation(session, "CBC")
