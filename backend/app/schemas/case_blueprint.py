"""YA-DOK Blueprint 3.2 contract (Phase A reference implementation).

Draft validation checks structure. Publishing requires additional approval checks.
This is an engineering validator, NOT a medical correctness validator.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Relevance = Literal["essential", "helpful", "optional", "not_indicated"] | None
Origin = Literal["record", "authored"]
IdPattern = r"^[a-z][a-z0-9_]*$"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CaseMeta(StrictModel):
    title: str | None = None
    subtitle: str | None = None
    short_brief: str | None = None
    specialty: str | None = None
    setting: str | None = None
    content_language: str = "en"
    difficulty: str | None = None
    estimated_duration_minutes: int | None = Field(default=None, ge=1)
    metrics: dict[str, Any] | None = None
    thumbnail: str | None = None
    anonymized: bool = False
    review_status: Literal["draft", "reviewed", "approved"] = "draft"
    reviewed_by: str | None = None
    source_pages: list[str] = Field(default_factory=list)
    source_notes: list[str] = Field(default_factory=list)
    review_flags: list[str] = Field(default_factory=list)


class Patient(StrictModel):
    display_name: str | None = None
    age_months: int | None = Field(default=None, ge=0)
    sex: str | None = None
    weight_kg: float | None = Field(default=None, gt=0)


class Persona(StrictModel):
    respondent_role: str
    speech_language: str
    emotional_state: str | None = None
    speech_style: str | None = None
    verbosity: Literal["short", "medium", "long"] | str = "short"
    opening_line: str | None = None
    unknown_replies: list[str] = Field(default_factory=list)


class Sourced(StrictModel):
    origin: Origin
    authored_by: str | None = None
    source_page: str | int | None = None


class HistoryItem(Sourced):
    id: str = Field(pattern=IdPattern)
    category: str = Field(min_length=1)
    known: bool
    facts: list[str] = Field(default_factory=list)
    volunteer_on_open_question: bool = False
    relevance: Relevance = None
    teaching_point: str | None = None

    @model_validator(mode="after")
    def unknown_has_no_facts(self):
        if not self.known and self.facts:
            raise ValueError("unknown history item cannot contain facts")
        return self


class ExamItem(Sourced):
    id: str = Field(pattern=IdPattern)
    system: str
    label: str
    type: str
    value: str | int | float | bool | None = None
    unit: str | None = None
    finding: str | None = None
    abnormal: bool = False
    relevance: Relevance = None
    teaching_point: str | None = None


class LabResult(Sourced):
    id: str = Field(pattern=IdPattern)
    label: str
    value: str | int | float | bool | None = None
    unit: str | None = None
    ref_range: str | None = None
    flag: Literal["low", "normal", "high", "positive", "negative", "abnormal"] | None = None


class Investigation(StrictModel):
    id: str = Field(pattern=IdPattern)
    label: str
    relevance: Relevance = None
    teaching_point: str | None = None
    results: list[LabResult] = Field(default_factory=list)


class Imaging(Sourced):
    id: str = Field(pattern=IdPattern)
    label: str
    modality: str
    body_part: str | None = None
    image_asset: str | None = None
    report_status: str = "not_available"
    report_text: str | None = None
    relevance: Relevance = None
    teaching_point: str | None = None


class FinalDiagnosis(StrictModel):
    id: str | None = None
    label: str | None = None
    leak_terms: list[str] = Field(default_factory=list)


class Distractor(StrictModel):
    id: str | None = None
    label: str | None = None
    why_not: str | None = None


class DifficultyFactors(StrictModel):
    presentation_typicality: Literal["typical", "atypical"] | None = None
    distractor_similarity: Literal["low", "medium", "high"] | None = None


class Debrief(StrictModel):
    summary: str | None = None
    learning_points: list[str] = Field(default_factory=list)


class GroundTruth(StrictModel):
    final_diagnosis: FinalDiagnosis
    distractors: list[Distractor] = Field(default_factory=list)
    distractors_approved_by: str | None = None
    difficulty_factors: DifficultyFactors
    secondary_findings: list[str] = Field(default_factory=list)
    severity: str | None = None
    expected_management: list[str] = Field(default_factory=list)
    management_in_record: list[str] = Field(default_factory=list)
    outcome_in_record: str | None = None
    debrief: Debrief


class CaseBlueprintV32(StrictModel):
    schema_version: Literal["3.2"]
    case_id: str = Field(min_length=3, pattern=r"^[A-Za-z0-9_-]+$")
    meta: CaseMeta
    patient: Patient
    persona: Persona
    history_items: list[HistoryItem]
    exam_items: list[ExamItem]
    investigations: list[Investigation]
    imaging: list[Imaging]
    ground_truth: GroundTruth

    @model_validator(mode="before")
    @classmethod
    def ignore_documentation_keys(cls, value: Any):
        # v3.2 template explicitly says underscore-prefixed metadata is documentation.
        if isinstance(value, dict):
            return {k: v for k, v in value.items() if not k.startswith("_")}
        return value

    @model_validator(mode="after")
    def unique_ids(self):
        for section in ("history_items", "exam_items", "investigations", "imaging"):
            ids = [item.id for item in getattr(self, section)]
            if len(ids) != len(set(ids)):
                raise ValueError(f"duplicate IDs in {section}")
        for investigation in self.investigations:
            ids = [r.id for r in investigation.results]
            if len(ids) != len(set(ids)):
                raise ValueError(f"duplicate results in {investigation.id}")
        return self


def publication_issues(case: CaseBlueprintV32) -> list[str]:
    """Engineering review gates. A clinician still must approve medical accuracy."""
    issues = []
    if case.case_id == "SPECIALTY_SETTING_TOPIC_001":
        issues.append("case_id is a template placeholder")
    if case.meta.review_status != "approved":
        issues.append("meta.review_status must be approved")
    if not case.meta.anonymized:
        issues.append("meta.anonymized must be true after privacy review")
    if not (case.meta.reviewed_by or "").strip():
        issues.append("meta.reviewed_by is missing")
    if case.meta.review_flags:
        issues.append("meta.review_flags must be resolved")
    for name in ("title", "short_brief", "specialty", "setting"):
        if not (getattr(case.meta, name) or "").strip():
            issues.append(f"meta.{name} is missing")
    if case.patient.age_months is None:
        issues.append("patient.age_months is missing")
    if not (case.persona.opening_line or "").strip():
        issues.append("persona.opening_line is missing")
    if not case.history_items:
        issues.append("history_items must not be empty")
    if not (case.ground_truth.final_diagnosis.id and case.ground_truth.final_diagnosis.label):
        issues.append("final diagnosis is incomplete")
    if not (3 <= len(case.ground_truth.distractors) <= 6):
        issues.append("distractors must contain 3 to 6 clinician-reviewed alternatives")
    if not (case.ground_truth.distractors_approved_by or "").strip():
        issues.append("distractors_approved_by is missing")
    for i, distractor in enumerate(case.ground_truth.distractors):
        if not (distractor.id and distractor.label and distractor.why_not):
            issues.append(f"distractors[{i}] missing ID/label/why_not")
    if case.ground_truth.difficulty_factors.presentation_typicality is None:
        issues.append("difficulty_factors.presentation_typicality needs clinician rating")
    if case.ground_truth.difficulty_factors.distractor_similarity is None:
        issues.append("difficulty_factors.distractor_similarity needs clinician rating")
    for section in ("history_items", "exam_items", "investigations", "imaging"):
        for item in getattr(case, section):
            if item.relevance is None:
                issues.append(f"{section}.{item.id} relevance not rated")
    sourced = [*case.history_items, *case.exam_items, *case.imaging]
    for inv in case.investigations:
        sourced.extend(inv.results)
    for obj in sourced:
        if obj.origin == "record" and obj.source_page is None:
            issues.append(f"{obj.__class__.__name__}.{obj.id} lacks source_page")
        elif obj.origin == "authored" and not (obj.authored_by or "").strip():
            issues.append(f"{obj.__class__.__name__}.{obj.id} lacks authored_by")
    return issues


def student_case_summary(case: CaseBlueprintV32) -> dict[str, Any]:
    """Explicit allowlist; never return the Blueprint or ground_truth to students."""
    return {
        "case_id": case.case_id,
        "title": case.meta.title,
        "short_brief": case.meta.short_brief,
        "specialty": case.meta.specialty,
        "setting": case.meta.setting,
        "difficulty": case.meta.difficulty,
        "estimated_duration_minutes": case.meta.estimated_duration_minutes,
        "thumbnail": case.meta.thumbnail,
    }
