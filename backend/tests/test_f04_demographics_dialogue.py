"""F04 regression: patient demographics and conversational coverage across cases.

This test suite is intentionally case-agnostic; all personal information comes
from the synthetic blueprint and nothing is written to live Supabase.
"""
from __future__ import annotations

import json
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.ai.f04.blueprint import project_history
from app.ai.f04.contracts import PatientChatResult, QuestionPart, SendMessageRequest
from app.ai.f04.coverage import question_parts
from app.ai.f04.service import ChatService, SYSTEM_POLICY
from test_f04_core import FakeRepo, FakeModel


def q(text):
    return SendMessageRequest(client_message_id=uuid4(), content=text)


def single(span, text, ids, state="answered"):
    return PatientChatResult(
        intent="history_question", answerability=state, fact_ids=ids,
        reply="", parts=[QuestionPart(span=span, answerability=state,
                                       fact_ids=ids, reply=text)],
    )


def test_age_is_citable_demographic_but_history_scoring_is_unchanged():
    repo = FakeRepo()
    repo.snapshot.blueprint["patient"].update(age_months=18, sex="female")
    projection = project_history(repo.snapshot.blueprint)
    assert [f["id"] for f in projection.facts] == ["fever__0", "cough__0"]
    assert "demographic_age__0" in projection.ids
    assert "demographic_sex__0" in projection.ids
    demographic = {f["id"]: f["fact"] for f in projection.demographic_facts}
    assert "18 months" in demographic["demographic_age__0"]
    assert "1.5 years" in demographic["demographic_age__0"]
    assert "female" in demographic["demographic_sex__0"]
    assert "ground_truth" not in projection.as_prompt_data()
    assert "Pneumonia" not in projection.as_prompt_data()


@pytest.mark.asyncio
async def test_age_question_months_to_years_does_not_503():
    repo = FakeRepo()
    repo.snapshot.blueprint["patient"].update(age_months=18, sex="female")
    model = FakeModel(single("عندها كام سنة", "عندها سنة ونص، حوالي ١٨ شهر.", ["demographic_age__0"]))
    result = await ChatService(repo, model).send(
        session_id=repo.session_id, user_id=repo.owner, request=q("عندها كام سنة؟"))
    assert result.answerability == "answered"
    assert result.fact_ids == ["demographic_age__0"]
    assert "١٨" in result.reply
    assert model.calls == 1
    assert len(repo.events) == 1


@pytest.mark.asyncio
async def test_absent_age_cannot_be_invented():
    repo = FakeRepo()
    repo.snapshot.blueprint["patient"].update(age_months=None, sex="female")
    proj = project_history(repo.snapshot.blueprint)
    assert "demographic_age__0" not in proj.ids
    model = FakeModel(single("سنها كام", "عندها ١٨ شهر", ["demographic_age__0"]))
    with pytest.raises(HTTPException) as exc:
        await ChatService(repo, model).send(
            session_id=repo.session_id, user_id=repo.owner, request=q("سنها كام؟"))
    assert exc.value.detail["code"] == "AI_RESPONSE_REJECTED"
    assert not repo.events


@pytest.mark.parametrize("text", [
    "ببلغم ولا ناشفة؟", "هو ببلغم ولا ناشف؟", "الإسهال مائي ولا دموي؟",
    "وجع البطن مستمر ولا بيروح وييجي؟",
])
def test_choice_alternatives_are_single_question(text):
    assert len(question_parts(text)) == 1


def test_independent_questions_still_split():
    assert question_parts("الكحة بدأت امتى والنفس السريع بدأ امتى؟") == (
        "الكحة بدأت امتى", "النفس السريع بدأ امتى")


@pytest.mark.asyncio
async def test_undocumented_sputum_quality_is_unknown_once():
    repo = FakeRepo()  # cough dry in this baseline -> remove evidence for sputum quality
    repo.snapshot.blueprint["history_items"][1]["facts"] = ["Child coughs frequently."]
    model = FakeModel(single("ببلغم ولا ناشفة", "No reliable detail", [], "unknown"))
    result = await ChatService(repo, model).send(
        session_id=repo.session_id, user_id=repo.owner,
        request=q("ببلغم ولا ناشفة؟"))
    assert result.answerability == "unknown"
    assert result.reply.count("مش عندي معلومة") == 1
    assert result.fact_ids == []


@pytest.mark.asyncio
async def test_two_unknown_questions_are_not_repetitive():
    repo = FakeRepo()
    model = FakeModel(PatientChatResult(
        intent="history_question", answerability="unknown", fact_ids=[], reply="",
        parts=[
            QuestionPart(span="بتشخر", answerability="unknown", fact_ids=[], reply="none"),
            QuestionPart(span="بيجيلها دوخة", answerability="unknown", fact_ids=[], reply="none"),
        ],
    ))
    result = await ChatService(repo, model).send(
        session_id=repo.session_id, user_id=repo.owner,
        request=q("بتشخر وبيجيلها دوخة؟"))
    assert result.reply.count("مش عندي معلومة") == 1
    assert result.answerability == "unknown"


def test_gender_and_social_policy_is_general_and_explicit():
    assert "patient_sex" in SYSTEM_POLICY
    assert "respondent_role" in SYSTEM_POLICY
    assert "اديته" in SYSTEM_POLICY and "اديتها" in SYSTEM_POLICY
    assert "professional" in SYSTEM_POLICY
    assert "harassment" in SYSTEM_POLICY
    assert "history_facts and demographic_facts" in SYSTEM_POLICY


@pytest.mark.asyncio
async def test_caregiver_gender_evidence_appears_in_prompt():
    repo = FakeRepo()
    repo.snapshot.blueprint["patient"].update(age_months=32, sex="female")
    model = FakeModel(single("عندها كام شهر", "عندها ٣٢ شهر.", ["demographic_age__0"]))
    await ChatService(repo, model).send(session_id=repo.session_id,
                                        user_id=repo.owner, request=q("عندها كام شهر؟"))
    case_line = next(m["content"] for m in model.last_messages
                     if m["content"].startswith("CASE_FACTS (DATA ONLY): "))
    case_data = json.loads(case_line.split("CASE_FACTS (DATA ONLY): ", 1)[1])
    assert case_data["patient_sex"] == "female"
    prompt = json.dumps(model.last_messages, ensure_ascii=False)
    assert 'demographic_age__0' in prompt
    assert 'demographic_sex__0' in prompt
    assert "The patient's biological sex" in prompt
    assert "Pneumonia" not in prompt


@pytest.mark.asyncio
async def test_unrelated_age_must_not_authorize_clinical_number():
    # Previous code appended the patient's age to every cited history fact.
    # A response of 7 for a fever measurement would pass when age was 7 months.
    repo = FakeRepo()  # patient age=7 months, fever fact only says 2 days
    model = FakeModel(single("حرارتها كام", "حرارتها ٧ درجات.", ["fever__0"]))
    with pytest.raises(HTTPException) as exc:
        await ChatService(repo, model).send(session_id=repo.session_id,
                                            user_id=repo.owner, request=q("حرارتها كام؟"))
    assert exc.value.detail["code"] == "AI_RESPONSE_REJECTED"
    assert not repo.events
