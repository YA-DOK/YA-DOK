"""Authorizes actions against server-side case state; never generates results."""
from .contracts import Authorization, CaseFindings, CasePolicy, Intent, RouteDecision


def authorize_action(decision: RouteDecision, case: CasePolicy) -> Authorization:
    if not case.active:
        return Authorization(False, "session_is_not_active")
    if decision.requires_confirmation or decision.intent == Intent.UNKNOWN:
        return Authorization(False, "clarification_required")
    if decision.intent == Intent.PHYSICAL_EXAM:
        return Authorization(decision.target in case.permitted_exams, "exam_policy")
    if decision.intent == Intent.ORDER_TEST:
        return Authorization(decision.target in case.permitted_tests, "test_policy")
    if decision.intent == Intent.REQUEST_HINT:
        return Authorization(case.hints_enabled, "hint_policy")
    if decision.intent == Intent.SUBMIT_DIAGNOSIS:
        return Authorization(case.diagnosis_enabled and bool(decision.content), "diagnosis_policy")
    return Authorization(True, "action_allowed")


def read_case_finding(decision: RouteDecision, findings: CaseFindings, case: CasePolicy) -> str | None:
    """Returns only predefined findings; absence returns None. No default medical result."""
    if not authorize_action(decision, case).allowed:
        return None
    if decision.intent == Intent.ORDER_TEST:
        return findings.tests.get(decision.target or "")
    if decision.intent == Intent.PHYSICAL_EXAM:
        return findings.exams.get(decision.target or "")
    return None
