"""Offline demo: python -m app.ai_foundation.demo (from backend/)."""
import json

from .contracts import CaseFindings, CasePolicy
from .guardrails import authorize_action, read_case_finding
from .intent_router import route_intent
from .model_registry import registry_as_dict


def main() -> None:
    example_policy = CasePolicy(permitted_exams=frozenset({"chest_auscultation"}), permitted_tests=frozenset({"cbc"}))
    # These are synthetic test fixtures, NOT real clinical interpretations.
    example_findings = CaseFindings(tests={"cbc": "TEST FIXTURE: predefined CBC result"}, exams={"chest_auscultation": "TEST FIXTURE: predefined auscultation finding"})
    print("MODEL REGISTRY (candidates; no models loaded):")
    print(json.dumps(registry_as_dict(), ensure_ascii=False, indent=2))
    print("\nROUTING DEMO (no network or database calls):")
    for text in ["الوجع بدأ إمتى؟", "اطلب تحليل CBC", "اسمع الصدر", "اطلب أشعة صدر", "ممكن تلميح", "خلصت الحالة", "اعملي حاجة"]:
        decision = route_intent(text)
        authorization = authorize_action(decision, example_policy)
        finding = read_case_finding(decision, example_findings, example_policy)
        print(json.dumps({"text": text, "intent": decision.intent.value, "target": decision.target, "allowed": authorization.allowed, "needs_clarification": decision.requires_confirmation, "predefined_result": finding}, ensure_ascii=False))


if __name__ == "__main__":
    main()
