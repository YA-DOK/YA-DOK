
import asyncio

import pytest

from backend.app.ai.llm.base import LLMService
from backend.app.simulation.patient_agent import PatientAgent


class FakeLLM(LLMService):
    """Fake LLM for testing without an API key."""

    def __init__(self, response="Yes, I have had a fever."):
        self.response = response
        self.received_messages = None

    async def generate(self, messages: list[dict], **kwargs) -> str:
        self.received_messages = messages
        return self.response


def test_patient_agent_returns_llm_response():
    llm = FakeLLM("Yes, I have had a fever.")
    agent = PatientAgent(llm)

    response = asyncio.run(
        agent.respond(
            case_data={"symptoms": ["fever"]},
            messages=[],
            question="Do you have a fever?",
        )
    )

    assert response == "Yes, I have had a fever."
    assert llm.received_messages is not None


def test_patient_agent_includes_case_in_system_prompt():
    llm = FakeLLM()
    agent = PatientAgent(llm)

    asyncio.run(
        agent.respond(
            case_data={"symptoms": ["fever"], "age": 25},
            messages=[],
            question="How are you feeling?",
        )
    )

    system_prompt = llm.received_messages[0]["content"]

    assert "fever" in system_prompt
    assert "25" in system_prompt
    assert "\u0645\u0645\u0646\u0648\u0639 \u0627\u062e\u062a\u0631\u0627\u0639 \u0623\u0639\u0631\u0627\u0636" in system_prompt


def test_patient_agent_includes_conversation_history():
    llm = FakeLLM()
    agent = PatientAgent(llm)

    history = [
        {"role": "user", "content": "Do you have a fever?"},
        {"role": "assistant", "content": "Yes, I have a fever."},
    ]

    asyncio.run(
        agent.respond(
            case_data={"symptoms": ["fever"]},
            messages=history,
            question="When did it start?",
        )
    )

    sent_messages = llm.received_messages

    assert sent_messages[1] == history[0]
    assert sent_messages[2] == history[1]
    assert sent_messages[3]["content"] == "When did it start?"


def test_patient_agent_rejects_empty_question():
    agent = PatientAgent(FakeLLM())

    with pytest.raises(ValueError, match="question cannot be empty"):
        asyncio.run(
            agent.respond(
                case_data={"symptoms": ["fever"]},
                messages=[],
                question="   ",
            )
        )


def test_patient_agent_rejects_empty_llm_response():
    agent = PatientAgent(FakeLLM("   "))

    with pytest.raises(ValueError, match="empty patient response"):
        asyncio.run(
            agent.respond(
                case_data={"symptoms": ["fever"]},
                messages=[],
                question="Do you have a fever?",
            )
        )
