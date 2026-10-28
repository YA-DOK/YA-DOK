"""Offline tests; run: python -m unittest discover -s tests -p test_ai_foundation.py -v"""
import os
import unittest
from unittest.mock import patch

from app.ai_foundation.contracts import CaseFindings, CasePolicy, Intent, RouteSource
from app.ai_foundation.guardrails import authorize_action, read_case_finding
from app.ai_foundation.intent_router import route_intent
from app.ai_foundation.model_registry import get_registry


class RoutingTests(unittest.TestCase):
    def setUp(self):
        self.policy = CasePolicy(permitted_exams=frozenset({"chest_auscultation"}), permitted_tests=frozenset({"cbc"}), hints_enabled=True)
        self.findings = CaseFindings(tests={"cbc": "TEST FIXTURE"})

    def test_egyptian_patient_question(self):
        self.assertEqual(route_intent("الوجع بدأ إمتى؟").intent, Intent.PATIENT_QUESTION)

    def test_english_patient_question(self):
        self.assertEqual(route_intent("When did the fever start?").intent, Intent.PATIENT_QUESTION)

    def test_cbc_order(self):
        result = route_intent("اطلب تحليل CBC")
        self.assertEqual((result.intent, result.target), (Intent.ORDER_TEST, "cbc"))
        self.assertTrue(authorize_action(result, self.policy).allowed)

    def test_chest_exam(self):
        result = route_intent("اسمع الصدر")
        self.assertEqual((result.intent, result.target), (Intent.PHYSICAL_EXAM, "chest_auscultation"))

    def test_forbidden_test(self):
        result = route_intent("اطلب أشعة صدر")
        self.assertEqual(result.intent, Intent.ORDER_TEST)
        self.assertFalse(authorize_action(result, self.policy).allowed)

    def test_missing_result_is_never_invented(self):
        policy = CasePolicy(permitted_tests=frozenset({"chest_xray"}))
        result = route_intent("اطلب أشعة صدر")
        self.assertIsNone(read_case_finding(result, CaseFindings(), policy))

    def test_existing_result(self):
        result = route_intent("اطلب تحليل CBC")
        self.assertEqual(read_case_finding(result, self.findings, self.policy), "TEST FIXTURE")

    def test_hint(self):
        self.assertEqual(route_intent("ممكن تلميح").intent, Intent.REQUEST_HINT)

    def test_result_request_needs_explicit_action(self):
        result = route_intent("ايه نتيجة CBC؟")
        self.assertEqual(result.intent, Intent.UNKNOWN)
        self.assertTrue(result.requires_confirmation)

    def test_hint_disabled(self):
        result = route_intent("تلميح")
        self.assertFalse(authorize_action(result, CasePolicy(hints_enabled=False)).allowed)

    def test_finish(self):
        self.assertEqual(route_intent("خلصت الحالة").intent, Intent.FINISH_SESSION)

    def test_diagnosis(self):
        result = route_intent("التشخيص النهائي التهاب رئوي")
        self.assertEqual(result.intent, Intent.SUBMIT_DIAGNOSIS)
        self.assertEqual(result.content, "التهاب رئوي")

    def test_empty_diagnosis(self):
        result = route_intent("التشخيص النهائي")
        self.assertEqual(result.intent, Intent.UNKNOWN)
        self.assertTrue(result.requires_confirmation)

    def test_ambiguous_request(self):
        result = route_intent("اعمل تحليل معين")
        self.assertEqual(result.intent, Intent.UNKNOWN)
        self.assertTrue(result.requires_confirmation)

    def test_unknown_ui_action(self):
        result = route_intent("any", ui_action="DELETE_USER")
        self.assertTrue(result.requires_confirmation)

    def test_ui_action_requires_target(self):
        result = route_intent("أي كلام", ui_action="ORDER_TEST")
        self.assertEqual(result.intent, Intent.UNKNOWN)

    def test_explicit_ui_action(self):
        result = route_intent("cbc", ui_action="ORDER_TEST", target="cbc")
        self.assertEqual(result.source, RouteSource.UI)
        self.assertTrue(authorize_action(result, self.policy).allowed)

    def test_session_finished_rejects(self):
        result = route_intent("اطلب تحليل CBC")
        self.assertFalse(authorize_action(result, CasePolicy(active=False, permitted_tests=frozenset({"cbc"}))).allowed)

    def test_empty_input(self):
        self.assertTrue(route_intent(" ").requires_confirmation)

    def test_model_registry_is_not_running_models(self):
        registry = get_registry()
        self.assertIn("stt", registry)
        self.assertIn("tts", registry)
        self.assertEqual(registry["student_coach"].status, "existing_keep")

    def test_registry_override(self):
        with patch.dict(os.environ, {"YADOK_PATIENT_MODEL": "example/model"}):
            self.assertEqual(get_registry()["patient"].model_id, "example/model")


if __name__ == "__main__":
    unittest.main()
