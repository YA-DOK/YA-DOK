"""Allowlisted case projection: sends NO ground_truth, imaging, investigations, diagnosis, etc."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .errors import failure

MAX_FACTS = 120
MAX_TOTAL_FACT_CHARS = 16000
MAX_FACT_CHARS = 350


@dataclass(frozen=True)
class HistoryProjection:
    # English source facts only; never send private outcome/treatment/diagnosis.
    facts: tuple[dict[str, str], ...]
    patient_description: str
    caregiver: str
    language: str
    emotional_state: str
    hidden_leak_terms: tuple[str, ...]
    patient_name: str = ""
    speech_style: str = ""
    verbosity: str = "short"
    demographic_facts: tuple[dict[str, str], ...] = ()
    patient_sex: str = ""
    age_months: int | None = None

    @property
    def all_facts(self) -> tuple[dict[str, str], ...]:
        return (*self.facts, *self.demographic_facts)

    @property
    def ids(self) -> list[str]:
        return [f["id"] for f in self.all_facts]

    def as_prompt_data(self) -> str:
        return json.dumps({
            "patient_description": self.patient_description,
            "patient_display_name": self.patient_name,
            "caregiver": self.caregiver,
            "speech_style": self.speech_style,
            "verbosity": self.verbosity,
            "speech_language": self.language,
            "emotional_state": self.emotional_state,
            "history_facts": self.facts,
            "demographic_facts": self.demographic_facts,
            "patient_sex": self.patient_sex,
            "age_months": self.age_months,
        }, ensure_ascii=False, separators=(",", ":"))


def _bounded(value: Any, max_chars: int) -> str:
    return value.strip()[:max_chars] if isinstance(value, str) else ""


def project_history(blueprint: dict[str, Any]) -> HistoryProjection:
    if blueprint.get("schema_version") != "3.2":
        raise failure(409, "UNSUPPORTED_BLUEPRINT", "This case version uses an unsupported blueprint schema.")
    persona = blueprint.get("persona") or {}
    patient = blueprint.get("patient") or {}
    if not isinstance(persona, dict) or not isinstance(patient, dict):
        raise failure(409, "INVALID_BLUEPRINT", "Patient persona data is invalid.")
    facts: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    chars = 0
    for item in blueprint.get("history_items") or []:
        if not isinstance(item, dict) or item.get("known") is not True:
            continue
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id or len(item_id) > 80:
            raise failure(409, "INVALID_BLUEPRINT", "Invalid history item ID.")
        for i, source in enumerate(item.get("facts") or []):
            fact_id = f"{item_id}__{i}"
            if fact_id in seen_ids:
                raise failure(409, "INVALID_BLUEPRINT", "Duplicate clinical fact ID.")
            if not isinstance(source, str) or not source.strip() or len(source) > MAX_FACT_CHARS:
                raise failure(409, "INVALID_BLUEPRINT", "Invalid clinical fact value.")
            seen_ids.add(fact_id)
            chars += len(source)
            facts.append({"id": fact_id, "category": _bounded(item.get("category"), 50), "fact": source.strip()})
            if len(facts) > MAX_FACTS or chars > MAX_TOTAL_FACT_CHARS:
                raise failure(409, "BLUEPRINT_TOO_LARGE", "Clinical history is too large for the configured safe prompt.")
    if not facts:
        raise failure(409, "MISSING_CLINICAL_HISTORY", "There are no known history facts for this case.")

    # This is read *only* for response screening, never included in model messages.
    truth = blueprint.get("ground_truth") or {}
    diagnosis = truth.get("final_diagnosis") or {} if isinstance(truth, dict) else {}
    leak_terms = []
    if isinstance(diagnosis, dict):
        leak_terms.extend([diagnosis.get("label"), *(diagnosis.get("leak_terms") or [])])
    # Respect deidentification: use only synthetic display name; never unfiltered clinical records.
    age = patient.get("age_months")
    if not isinstance(age, int) or isinstance(age, bool) or age < 0:
        age = "unknown"
    sex = _bounded(patient.get("sex"), 16)
    description = f"{age} months old, sex: {sex}"
    # Public, approved patient demographics are evidence too. Do not make the
    # LLM answer age from prompt metadata while requiring impossible history IDs.
    # Keep these separate from history_items so existing F02 rubrics do not change.
    demographic_facts: list[dict[str, str]] = []
    age_months = age if isinstance(age, int) else None
    if age_months is not None:
        years, remaining = divmod(age_months, 12)
        forms = [f"Patient age is {age_months} months"]
        if years:
            forms.append(f"equivalent to {years} years and {remaining} months")
            if remaining == 0:
                forms.append(f"exactly {years} years")
            elif remaining == 6:
                forms.append(f"equivalent to {years + 0.5:g} years")
        demographic_facts.append({
            "id": "demographic_age__0", "category": "demographic",
            "fact": "; ".join(forms) + ".",
        })
    if sex.lower() in {"female", "male"}:
        demographic_facts.append({
            "id": "demographic_sex__0", "category": "demographic",
            "fact": f"The patient's biological sex in the case is {sex.lower()}.",
        })
    # An authored history item must not be able to collide with reserved facts.
    if any(f["id"] in seen_ids for f in demographic_facts):
        raise failure(409, "INVALID_BLUEPRINT", "Reserved demographic fact ID collision.")
    return HistoryProjection(
        facts=tuple(facts),
        patient_description=description,
        caregiver=_bounded(persona.get("respondent_role"), 30) or "mother",
        language=_bounded(persona.get("speech_language"), 12) or "ar-EG",
        emotional_state=_bounded(persona.get("emotional_state"), 70),
        hidden_leak_terms=tuple(str(t).strip() for t in leak_terms if isinstance(t, str) and len(t.strip()) >= 4),
        # Approved case blueprints contain only synthetic display names, never real identifiers.
        patient_name=_bounded(patient.get("display_name"), 80),
        speech_style=_bounded(persona.get("speech_style"), 110),
        verbosity=_bounded(persona.get("verbosity"), 24) or "short",
        demographic_facts=tuple(demographic_facts),
        patient_sex=sex.lower(),
        age_months=age_months,
    )
