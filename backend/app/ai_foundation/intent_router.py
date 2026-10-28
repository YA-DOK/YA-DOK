"""Rules-first router with no model call, side effects, or session writes.

The first phase intentionally prefers asking for clarification rather than
misclassifying a clinical action. Next phase can add a JSON-only LLM fallback.
"""
import re

from .contracts import Intent, RouteDecision, RouteSource

# Small high-precision set; add aliases only from verified benchmark failures.
_TEST_ALIASES: dict[str, tuple[str, ...]] = {
    "cbc": ("cbc", "صورة دم", "صوره دم", "complete blood count"),
    "chest_xray": ("chest x-ray", "chest xray", "cxr", "أشعة صدر", "اشعه صدر", "اشعة على الصدر"),
    "ecg": ("ecg", "ekg", "رسم قلب", "رسم القلب"),
    "crp": ("crp", "سي ار بي", "c-reactive protein"),
}
_EXAM_ALIASES: dict[str, tuple[str, ...]] = {
    "chest_auscultation": ("سماع الصدر", "اسمع الصدر", "chest auscultation", "auscultate chest"),
    "abdominal_exam": ("فحص البطن", "اكشف البطن", "abdominal exam", "abdominal examination"),
    "vitals": ("العلامات الحيوية", "قيس الحرارة", "قياس الضغط", "vital signs", "check vitals"),
}
_QUESTION_MARKERS = (
    "?", "؟", "امتى", "إمتى", "ليه", "ايه", "إيه", "ازاي", "إزاي", "فين", "هل", "قد ايه", "من امتى", "what", "when", "where", "how", "why", "do you", "have you", "is it", "are you", "tell me",
)
_ORDER_VERBS = ("اطلب", "عايز اعمل", "عايز أعمل", "اعمل تحليل", "اعمل أشعة", "اعمل اشعة", "اطلب تحليل", "order", "request", "run test")
_EXAM_VERBS = ("افحص", "اكشف", "اكشف على", "اسمع", "قيس", "قياس", "اعمل فحص", "examine", "check", "auscultate")
_HINT_PATTERNS = ("تلميح", "ممكن تلميح", "اديني تلميح", "عايز تلميح", "hint", "give me a hint", "ساعدني", "help me with a hint")
_FINISH_PATTERNS = ("خلصت الحالة", "انهي الحالة", "إنهاء الحالة", "finish session", "end case", "finish case")
_DIAGNOSIS_PREFIXES = ("التشخيص النهائي", "تشخيصي النهائي", "my final diagnosis", "submit diagnosis")


def _clean(value: str) -> str:
    value = value.casefold().strip()
    return re.sub(r"\s+", " ", value)


def _matched_alias(text: str, aliases: dict[str, tuple[str, ...]]) -> str | None:
    for canonical, names in aliases.items():
        if any(re.search(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", text) for alias in names):
            return canonical
    return None


def route_intent(text: str, *, ui_action: str | None = None, target: str | None = None) -> RouteDecision:
    """Classify text or explicit UI action, without executing any clinical task.

    The backend MUST authenticate and authorize separately (see guardrails).
    Unknown or ambiguous actions require confirmation.
    """
    cleaned = _clean(text)
    if not cleaned:
        return RouteDecision(Intent.UNKNOWN, RouteSource.CLARIFICATION, requires_confirmation=True, reason="empty_input")

    if ui_action is not None:
        try:
            selected = Intent(ui_action)
        except ValueError:
            return RouteDecision(Intent.UNKNOWN, RouteSource.CLARIFICATION, requires_confirmation=True, reason="invalid_ui_action")
        if selected == Intent.UNKNOWN:
            return RouteDecision(Intent.UNKNOWN, RouteSource.CLARIFICATION, requires_confirmation=True, reason="unknown_ui_action")
        if selected in (Intent.ORDER_TEST, Intent.PHYSICAL_EXAM) and not target:
            return RouteDecision(Intent.UNKNOWN, RouteSource.CLARIFICATION, requires_confirmation=True, reason="missing_target")
        if selected == Intent.SUBMIT_DIAGNOSIS and not cleaned:
            return RouteDecision(Intent.UNKNOWN, RouteSource.CLARIFICATION, requires_confirmation=True, reason="missing_diagnosis")
        return RouteDecision(selected, RouteSource.UI, target=target, content=text)

    for phrase in _FINISH_PATTERNS:
        if cleaned == phrase.casefold():
            return RouteDecision(Intent.FINISH_SESSION, RouteSource.RULE)

    for phrase in _HINT_PATTERNS:
        if cleaned == phrase.casefold() or cleaned.startswith(phrase.casefold() + " "):
            return RouteDecision(Intent.REQUEST_HINT, RouteSource.RULE)

    for phrase in _DIAGNOSIS_PREFIXES:
        if cleaned.startswith(phrase.casefold()):
            answer = cleaned[len(phrase):].strip(" :،-")
            return (RouteDecision(Intent.SUBMIT_DIAGNOSIS, RouteSource.RULE, content=answer)
                    if answer else RouteDecision(Intent.UNKNOWN, RouteSource.CLARIFICATION, requires_confirmation=True, reason="missing_diagnosis"))

    order_hit = any(v in cleaned for v in _ORDER_VERBS)
    exam_hit = any(v in cleaned for v in _EXAM_VERBS)
    test_target = _matched_alias(cleaned, _TEST_ALIASES)
    exam_target = _matched_alias(cleaned, _EXAM_ALIASES)

    if test_target and any(v in cleaned for v in ("نتيجة", "نتايج", "result", "results")) and not order_hit:
        return RouteDecision(Intent.UNKNOWN, RouteSource.CLARIFICATION, requires_confirmation=True, reason="results_require_explicit_action")

    if order_hit and test_target and not exam_hit:
        return RouteDecision(Intent.ORDER_TEST, RouteSource.RULE, target=test_target)
    if exam_hit and exam_target and not order_hit:
        return RouteDecision(Intent.PHYSICAL_EXAM, RouteSource.RULE, target=exam_target)
    if order_hit or exam_hit:
        return RouteDecision(Intent.UNKNOWN, RouteSource.CLARIFICATION, requires_confirmation=True, reason="ambiguous_action")

    if any(marker in cleaned for marker in _QUESTION_MARKERS):
        return RouteDecision(Intent.PATIENT_QUESTION, RouteSource.RULE, content=text)

    return RouteDecision(Intent.UNKNOWN, RouteSource.CLARIFICATION, requires_confirmation=True, reason="unclassified_turn")
