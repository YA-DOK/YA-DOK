"""Case-agnostic safety floor for multi-part questions.

This splitter does NOT try to diagnose, translate symptoms, or choose facts.
It only recognizes explicit question boundaries and coordinators, so that
one model answer cannot silently replace two separate questions.
"""
from __future__ import annotations

import re
import unicodedata

# Punctuation and conjunctions mark possible independently answerable parts.
# The Arabic waw is joined to the next word. Split only after whitespace.
_BOUNDARY = re.compile(r"\s*(?:[؟?؛;،,]|\band\b)\s*|\s+و(?!لا(?:\s|$))(?=[\w\u0621-\u064a])", re.IGNORECASE)
_START_FILLER = re.compile(r"^\s*(?:و|and)\s+", re.IGNORECASE)
# Colloquial conversation openers are NOT independently answerable questions.
# Strip only at the very start, never in the middle (where clauses may matter).
# This is discourse handling, independent of any disease, symptom or case.
_DISCOURSE_PREFIX = re.compile(
    r"^\s*(?:(?:طب|طيب|معلش|بص)\s*(?:[،,]\s*|\s+))+",
    re.IGNORECASE,
)


def normalized(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    return " ".join(value.casefold().strip().replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ى", "ي").split())


def question_parts(question: str) -> tuple[str, ...]:
    """Minimum independently requested spans; does not infer medical intent.

    Some Arabic conjunctions connect noun phrases within a single question
    and will produce a conservative additional part. In those cases the LLM
    must account for both rather than return an incomplete 'answered' reply.
    """
    # Drop an explicit standalone leading conjunction, but NEVER strip the
    # first letter of lexical words such as "وجع", "وزنه", or "ولدك".
    question = _DISCOURSE_PREFIX.sub("", question)
    question = _START_FILLER.sub("", question)
    spans = []
    cursor = 0
    for match in _BOUNDARY.finditer(question):
        # "ولا" introduces alternatives to the SAME property. A subsequent
        # coordinated verb ("بيروح وييجي") is still inside that alternative,
        # not a separate patient-history question. Apply after the most recent
        # confirmed boundary, without any symptom-specific vocabulary.
        if re.search(r"\bولا\b", question[cursor:match.start()]):
            continue
        candidate = _START_FILLER.sub("", question[cursor:match.start()]).strip(" \t\n؟?؛;،")
        if candidate:
            spans.append(candidate)
        cursor = match.end()
    tail = _START_FILLER.sub("", question[cursor:]).strip(" \t\n؟?؛;،")
    if tail:
        spans.append(tail)
    # Fail closed on too many parts; do not let model report false completeness.
    return tuple(spans)


def spans_accounted_for(question: str, output_spans: list[str]) -> bool:
    """Model must copy every independent input span once, without omission.

    Exact normalization (not semantic similarity) prevents the model from
    inventing a different question. This is a structural guard, NOT proof of
    semantic clinical correctness.
    """
    expected = question_parts(question)
    return (
        len(expected) == len(output_spans)
        and len(expected) <= 8
        and all(normalized(a) == normalized(b) for a, b in zip(expected, output_spans))
    )
