"""Central model catalog: candidates, not instantiated models.

Environment variables ONLY override model identifiers. API keys are not read or
printed here. Provider transport, deployment and test gates come in later phases.
"""
import os
from dataclasses import asdict, dataclass
from typing import Literal


@dataclass(frozen=True)
class ModelSpec:
    task: str
    provider: str
    model_id: str
    runtime: str
    status: Literal["benchmark_required", "existing_keep"]
    fallback: str


def get_registry() -> dict[str, ModelSpec]:
    return {
        "patient": ModelSpec("patient", "openrouter", os.getenv("YADOK_PATIENT_MODEL", "qwen/qwen3.5-35b-a3b"), "hosted_api", "benchmark_required", "safe_unavailable_message"),
        "intent_disambiguation": ModelSpec("intent_disambiguation", "openrouter", os.getenv("YADOK_INTENT_MODEL", os.getenv("YADOK_PATIENT_MODEL", "qwen/qwen3.5-35b-a3b")), "hosted_api", "benchmark_required", "request_clarification"),
        "evaluation": ModelSpec("evaluation", "google", os.getenv("YADOK_EVALUATION_MODEL", "gemini-3.8-flash"), "hosted_api", "benchmark_required", "rubric_checks_and_review"),
        "student_coach": ModelSpec("student_coach", "existing", os.getenv("YADOK_COACH_MODEL", "preserve_current"), "current_project", "existing_keep", "deterministic_summary"),
        "stt": ModelSpec("stt", "huggingface", os.getenv("YADOK_STT_MODEL", "mohammedaly22/QwenCleo-ASR"), "separate_gpu_worker_candidate", "benchmark_required", "typed_input"),
        "tts": ModelSpec("tts", "huggingface", os.getenv("YADOK_TTS_MODEL", "mohammedaly22/VoiceTut-TTS"), "separate_gpu_worker_candidate", "benchmark_required", "display_text"),
        "embeddings_optional": ModelSpec("embeddings_optional", "huggingface", os.getenv("YADOK_EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-0.6B"), "disabled_until_needed", "benchmark_required", "exact_lookup"),
    }


def registry_as_dict() -> dict[str, dict[str, str]]:
    return {key: asdict(value) for key, value in get_registry().items()}
