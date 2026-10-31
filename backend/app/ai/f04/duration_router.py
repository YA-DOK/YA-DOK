"""Conservative, source-grounded rescue for clear symptom-duration questions.

Not a general NLU: return None unless a single supported symptom and an
explicit duration with a small, unambiguous time interval are both present.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class GroundedDuration:
    fact_id: str
    reply: str


_ALIASES = {
    "cough": ("كح", "سعال", "cough"),
    "fever": ("سخون", "حرار", "حمى", "fever", "temperature"),
    "vomiting": ("ترجيع", "بيرجع", "قيء", "استفراغ", "vomit"),
    "diarrhea": ("اسهال", "diarrhea", "diarrhoea"),
}
_DURATION_WORDS = ("امتى", "متى", "بقال", "قد ايه", "بدأ", "بدا", "منذ", "how long", "since when", "when did")
# The onset fast path is ONLY for "when did this symptom begin?".
# If the question asks about *worsening*, improvement, or cessation, the
# onset fact must never be substituted for a different clinical event.
_EVOLUTION_WORDS = (
    "زاد", "زادت", "بيزيد", "بتزيد", "تزيد", "بقت اوحش", "بقى اوحش",
    "اوحش", "اسوا", "اسوأ", "سوء", "اشتدت", "اشتد", "شدة", "شديده",
    "بتسوء", "تسوء", "خفت", "بيخف", "بتخف", "خفّت", "خفت", "تحسن",
    "اتحسن", "بتتحسن", "احسن", "قلت", "بتقل", "اختفت", "وقفت",
    "worse", "worsen", "got worse", "more severe", "increasing",
    "increased", "improved", "better", "less severe", "stopped", "resolved",
)
_CESSATION_WORDS = ("مبقاش", "مبقتش", "مفيش", "مش بي", "no longer", "without")
_NUMBERS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7}
_ARABIC = {1: {"day": "يوم", "week": "اسبوع", "month": "شهر", "hour": "ساعة"},
           2: {"day": "يومين", "week": "اسبوعين", "month": "شهرين", "hour": "ساعتين"}}
_MORE = {"day": "ايام", "week": "اسابيع", "month": "شهور", "hour": "ساعات"}
_SPOKEN = {3: "تلات", 4: "اربع", 5: "خمس", 6: "ست", 7: "سبع"}
_DURATION = re.compile(
    r"\b(?P<num>one|two|three|four|five|six|seven|[1-7])\s+"
    r"(?P<unit>days?|weeks?|months?|hours?)\b", re.IGNORECASE
)


def _normalize(value: str) -> str:
    text = "".join(c for c in unicodedata.normalize("NFKC", value) if not unicodedata.combining(c))
    return (text.casefold().replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
            .replace("ى", "ي").replace("ـ", ""))


def _phrase(source: str) -> str | None:
    # Do not reduce ranges, negation or vague/uncertain durations to a fixed answer.
    if re.search(r"\b(approximately|around|about|maybe|up to|at least|possibly|unknown|resolved|previously|last month|last year|months ago|years ago)\b", source, re.I):
        return None
    if re.search(r"\b(no|not|never|denies|without)\b", source, re.I):
        return None
    # A duration of *worsening* is not necessarily duration since onset.
    if re.search(r"\b(worsen(?:ed|ing|s)?|getting worse|more noticeable|intensif(?:ied|ying)|improv(?:ed|ing)|increas(?:ed|ing))\b", source, re.I):
        return None
    # Mentioning a time span alone is not proof it describes symptom onset.
    if not re.search(r"\b(for|since|started|began|onset|has been|have been|lasted|lasting)\b", source, re.I):
        return None
    matches = list(_DURATION.finditer(source))
    if len(matches) != 1:
        return None
    m = matches[0]
    count = _NUMBERS.get(m["num"].lower(), None)
    if count is None:
        count = int(m["num"])
    unit = m["unit"].lower().rstrip("s")
    if count <= 2:
        amount = _ARABIC[count][unit]
        return f"من {amount} يا دكتور."
    return f"من {_SPOKEN[count]} {_MORE[unit]} يا دكتور."


def grounded_duration_answer(question: str, facts: Iterable[dict[str, str]]) -> GroundedDuration | None:
    q = _normalize(question)
    if not any(_normalize(marker) in q for marker in _DURATION_WORDS):
        return None
    if any(_normalize(marker) in q for marker in (*_EVOLUTION_WORDS, *_CESSATION_WORDS)):
        # A change or end-date is a different fact from symptom onset.
        # Let the history agent reason over the relevant facts instead.
        return None
    matching_categories = [category for category, aliases in _ALIASES.items()
                           if any(alias in q for alias in aliases)]
    if len(matching_categories) != 1:
        return None
    # Clinical onset often lives under onset_duration / chief_complaint, not
    # under the symptom-specific category. Shared facts must explicitly name
    # the queried symptom; never use an unrelated symptom's duration.
    target = matching_categories[0]
    source_aliases = {
        "cough": ("cough", "coughing"),
        "fever": ("fever",),
        "vomiting": ("vomit", "vomiting", "throwing up"),
        "diarrhea": ("diarrhea", "diarrhoea"),
    }[target]
    candidates = []
    for fact in facts:
        category = fact.get("category")
        source = fact.get("fact", "")
        if not isinstance(source, str):
            continue
        if category == target:
            candidates.append(fact)
        elif category in ("onset_duration", "chief_complaint") and any(
            re.search(r"\b" + re.escape(word) + r"\b", source, re.I)
            for word in source_aliases
        ):
            candidates.append(fact)

    matched = [(f["id"], f.get("category"), _phrase(f["fact"])) for f in candidates]
    matched = [(fact_id, category, reply) for fact_id, category, reply in matched if reply is not None]
    # Repeated documentation of the same onset is not a conflict. Two
    # different onsets are a conflict, so fail closed instead of guessing.
    if not matched or len({reply for _, _, reply in matched}) != 1:
        return None
    # Prefer explicit onset over a summary when both cite the same duration.
    preference = {"onset_duration": 0, target: 1, "chief_complaint": 2}
    fact_id, _, reply = min(matched, key=lambda m: preference.get(m[1], 3))
    return GroundedDuration(fact_id=fact_id, reply=reply)
