"""Small typed contracts for the future F03 simulation engine."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping


class Intent(str, Enum):
    PATIENT_QUESTION = "PATIENT_QUESTION"
    PHYSICAL_EXAM = "PHYSICAL_EXAM"
    ORDER_TEST = "ORDER_TEST"
    SUBMIT_DIAGNOSIS = "SUBMIT_DIAGNOSIS"
    REQUEST_HINT = "REQUEST_HINT"
    FINISH_SESSION = "FINISH_SESSION"
    UNKNOWN = "UNKNOWN"


class RouteSource(str, Enum):
    UI = "ui_action"
    RULE = "rule"
    CLARIFICATION = "clarification"


@dataclass(frozen=True)
class RouteDecision:
    intent: Intent
    source: RouteSource
    target: str | None = None
    content: str | None = None
    requires_confirmation: bool = False
    reason: str = ""


@dataclass(frozen=True)
class CasePolicy:
    """Student-visible action permissions, not the hidden medical blueprint.

    The authoritative backend constructs this AFTER authenticating the student,
    verifying session ownership, loading the case version, and checking state.
    """

    permitted_exams: frozenset[str] = field(default_factory=frozenset)
    permitted_tests: frozenset[str] = field(default_factory=frozenset)
    hints_enabled: bool = True
    diagnosis_enabled: bool = True
    active: bool = True


@dataclass(frozen=True)
class Authorization:
    allowed: bool
    reason: str


@dataclass(frozen=True)
class CaseFindings:
    """Pre-authored public findings. Missing keys must NEVER be invented."""
    exams: Mapping[str, str] = field(default_factory=dict)
    tests: Mapping[str, str] = field(default_factory=dict)
