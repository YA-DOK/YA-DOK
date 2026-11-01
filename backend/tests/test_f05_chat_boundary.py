"""Regression: F05 clinical results must never become F04 LLM context."""
from app.simulation.engine import SimulationMessage, patient_dialogue_history


def test_only_patient_dialogue_is_used_as_llm_history():
    messages = [
        SimulationMessage(role="system", content="system setup", action="initialization"),
        SimulationMessage(role="user", content="السلام عليكم", action="patient_question"),
        SimulationMessage(role="assistant", content="أهلا يا دكتور", action="patient_response"),
        SimulationMessage(role="user", content="Investigation requested: cbc", action="request_investigation"),
        SimulationMessage(role="system", content='{"result":"SECRET CBC"}', action="investigation_result"),
        SimulationMessage(role="user", content="Examination requested: chest", action="request_examination"),
        SimulationMessage(role="system", content='{"result":"SECRET EXAM"}', action="examination_result"),
    ]
    assert patient_dialogue_history(messages) == [
        {"role": "user", "content": "السلام عليكم"},
        {"role": "assistant", "content": "أهلا يا دكتور"},
    ]


def test_unrecognized_user_and_assistant_actions_are_not_patient_dialogue():
    messages = [
        SimulationMessage(role="user", content="Diagnosis: SECRET", action="submit_diagnosis"),
        SimulationMessage(role="assistant", content="automated event", action="other"),
    ]
    assert patient_dialogue_history(messages) == []
