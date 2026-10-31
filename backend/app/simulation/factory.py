
from backend.app.ai.llm.openrouter import OpenRouterProvider
from backend.app.simulation.patient_agent import PatientAgent


def create_patient_agent() -> PatientAgent:
    """Create a patient agent backed by the configured OpenRouter model."""
    provider = OpenRouterProvider()
    return PatientAgent(llm_service=provider)
