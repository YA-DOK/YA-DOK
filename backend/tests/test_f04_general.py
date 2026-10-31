"""Golden contract tests against distinct synthetic cases, no real OpenRouter calls.

These test structural evidence/coverage, NOT clinical semantic correctness.
"""
from __future__ import annotations

from uuid import uuid4
from fastapi import HTTPException
import pytest

from app.ai.f04.contracts import PatientChatResult, QuestionPart, SendMessageRequest
from app.ai.f04.coverage import question_parts, spans_accounted_for
from app.ai.f04.service import ChatService
from test_f04_core import FakeRepo, FakeModel


def question(text: str) -> SendMessageRequest:
    return SendMessageRequest(client_message_id=uuid4(), content=text)


def result(parts):
    all_ids = list(dict.fromkeys(fid for p in parts for fid in p.fact_ids))
    return PatientChatResult(
        intent="history_question", answerability="answered",
        fact_ids=all_ids, reply="", parts=parts,
    )


def part(span, fact_ids, reply, state="answered"):
    return QuestionPart(span=span, fact_ids=fact_ids, reply=reply, answerability=state)


def case_items(items):
    return [{"id": category, "category": category, "known": True, "facts": facts}
            for category, facts in items]


def test_generic_question_splitter_is_not_a_symptom_dictionary():
    assert question_parts("الكحة بدأت امتى والنفس السريع بدأ امتى؟") == (
        "الكحة بدأت امتى", "النفس السريع بدأ امتى"
    )
    assert question_parts("الرضاعة والبول عاملين ايه؟") == ("الرضاعة", "البول عاملين ايه")
    assert question_parts("Any chest pain and shortness of breath?") == (
        "Any chest pain", "shortness of breath"
    )
    assert question_parts("الكحة زادت امتى؟") == ("الكحة زادت امتى",)
    assert not spans_accounted_for("الكحة بدأت امتى والنفس بدأ امتى؟", ["الكحة بدأت امتى"])


@pytest.mark.asyncio
async def test_pediatric_respiratory_multisymptom_must_answer_both():
    repo = FakeRepo()
    repo.snapshot.blueprint["history_items"] = case_items([
        ("onset_duration", ["Fever and cough started three days ago.",
                            "Fast breathing began twelve hours ago."]),
    ])
    q = "الكحة بدأت امتى والنفس السريع بدأ امتى؟"
    model = FakeModel(result([
        part("الكحة بدأت امتى", ["onset_duration__0"], "الكحة بقالها 3 أيام."),
        part("النفس السريع بدأ امتى", ["onset_duration__1"], "النفس سريع من 12 ساعة."),
    ]))
    response = await ChatService(repo, model).send(
        session_id=repo.session_id, user_id=repo.owner, request=question(q))
    assert response.fact_ids == ["onset_duration__0", "onset_duration__1"]
    assert "3" in response.reply and "12" in response.reply
    assert response.answerability == "answered"
    assert model.calls == 1


@pytest.mark.asyncio
async def test_gastro_case_partial_answer_requires_explicit_unknown():
    repo = FakeRepo()
    repo.snapshot.blueprint["history_items"] = case_items([
        ("vomiting", ["Vomiting occurs after feeds."]),
    ])
    q = "الترجيع بيحصل بعد الرضاعة والبول قل؟"
    model = FakeModel(result([
        part("الترجيع بيحصل بعد الرضاعة", ["vomiting__0"], "أيوه، بيرجع بعد الرضاعة."),
        part("البول قل", [], "Unknown", "unknown"),
    ]))
    r = await ChatService(repo, model).send(
        session_id=repo.session_id, user_id=repo.owner, request=question(q))
    assert r.answerability == "partial"
    assert r.fact_ids == ["vomiting__0"]
    assert "مش عندي معلومة" in r.reply
    assert "Unknown" not in r.reply


@pytest.mark.asyncio
async def test_adult_cardio_case_uses_same_service_no_cough_rule():
    repo = FakeRepo()
    repo.snapshot.blueprint["history_items"] = case_items([
        ("pain", ["Chest pain radiates to left arm."]),
        ("allergy", ["No known drug allergy."]),
    ])
    model = FakeModel(result([
        part("الألم بيوصل للدراع", ["pain__0"], "أيوه، بيوصل لدراعي الشمال."),
        part("عندك حساسية", ["allergy__0"], "معنديش حساسية معروفة من الأدوية."),
    ]))
    r = await ChatService(repo, model).send(
        session_id=repo.session_id, user_id=repo.owner,
        request=question("الألم بيوصل للدراع وعندك حساسية؟"))
    assert r.answerability == "answered"
    assert r.fact_ids == ["pain__0", "allergy__0"]


@pytest.mark.asyncio
async def test_drops_second_question_cannot_save_incomplete_reply():
    repo = FakeRepo()
    repo.snapshot.blueprint["history_items"] = case_items([
        ("onset_duration", ["Cough started three days ago.", "Fast breathing began twelve hours ago."]),
    ])
    q = question("الكحة بدأت امتى والنفس السريع بدأ امتى؟")
    model = FakeModel(PatientChatResult(
        intent="history_question", answerability="answered", fact_ids=["onset_duration__0"],
        reply="من 3 أيام.", parts=[part("الكحة بدأت امتى", ["onset_duration__0"], "من 3 أيام.")]
    ))
    with pytest.raises(HTTPException) as e:
        await ChatService(repo, model).send(session_id=repo.session_id, user_id=repo.owner, request=q)
    assert e.value.status_code == 503
    assert e.value.detail["code"] == "AI_RESPONSE_REJECTED"
    assert repo.events == []
    assert repo.reserved == {}


@pytest.mark.asyncio
async def test_model_cannot_replace_question_span():
    repo, model = FakeRepo(), FakeModel(result([
        part("هل عنده إسهال", ["fever__0"], "أيوه")
    ]))
    with pytest.raises(HTTPException):
        await ChatService(repo, model).send(
            session_id=repo.session_id, user_id=repo.owner,
            request=question("هل عنده سخونية؟"))
    assert repo.events == []


@pytest.mark.asyncio
async def test_unknown_part_with_fact_id_is_rejected():
    repo, model = FakeRepo(), FakeModel(result([
        part("هل عنده سخونية", ["fever__0"], "معرفش", "unknown")
    ]))
    with pytest.raises(HTTPException):
        await ChatService(repo, model).send(
            session_id=repo.session_id, user_id=repo.owner,
            request=question("هل عنده سخونية؟"))
    assert repo.events == []


@pytest.mark.asyncio
async def test_unsupported_second_part_numeric_rejected():
    repo, model = FakeRepo(), FakeModel(result([
        part("هو سخن", ["fever__0"], "سخن من يومين."),
        part("شرب قد ايه", ["cough__0"], "شرب 150 مل."),
    ]))
    with pytest.raises(HTTPException):
        await ChatService(repo, model).send(
            session_id=repo.session_id, user_id=repo.owner,
            request=question("هو سخن وشرب قد ايه؟"))
    assert repo.events == []


def test_number_words_normalize_without_case_specific_constants():
    from app.ai.f04.numeric_grounding import numbers_grounded
    assert numbers_grounded("من تلات أيام", "Fever started three days ago")
    assert numbers_grounded("من 12 ساعة", "Fast breathing began twelve hours ago")
    assert numbers_grounded("من ٣ أيام", "Cough started 3 days ago")
    assert not numbers_grounded("من 13 ساعة", "Fast breathing began twelve hours ago")


@pytest.mark.asyncio
async def test_hidden_diagnosis_in_one_part_blocks_entire_answer():
    repo, model = FakeRepo(), FakeModel(result([
        part("عنده سخونية", ["fever__0"], "عنده التهاب رئوي"),
        part("بيكح", ["cough__0"], "أيوه بيكح"),
    ]))
    with pytest.raises(HTTPException) as e:
        await ChatService(repo, model).send(session_id=repo.session_id, user_id=repo.owner,
                                            request=question("عنده سخونية وبيكح؟"))
    assert e.value.detail["code"] == "AI_RESPONSE_REJECTED"
    assert repo.events == []


@pytest.mark.asyncio
async def test_case_agnostic_no_fixed_symptom_optimization():
    repo = FakeRepo()
    repo.snapshot.blueprint["history_items"] = case_items([
        ("neurology", ["The seizure lasted 4 minutes."])
    ])
    model = FakeModel(result([
        part("التشنج استمر قد ايه", ["neurology__0"], "استمر 4 دقايق."),
    ]))
    response = await ChatService(repo, model).send(
        session_id=repo.session_id, user_id=repo.owner,
        request=question("التشنج استمر قد ايه؟"))
    assert response.fact_ids == ["neurology__0"]
    assert model.calls == 1
    assert response.model == "test-model"


@pytest.mark.parametrize("question", [
    "وجع الصدر بيروح فين؟",
    "وزنه كام؟",
    "والدته عندها سكر؟",
    "ولدك بيرجع بعد الرضاعة؟",
])
def test_arabic_words_starting_with_waw_are_not_corrupted(question):
    assert question_parts(question) == (question.rstrip("؟"),)


def test_standalone_waw_filler_is_safe_to_remove():
    assert question_parts("و وجع الصدر بيروح فين؟") == ("وجع الصدر بيروح فين",)


def test_compound_chest_pain_preserves_initial_word():
    assert question_parts("وجع الصدر بيمتد للدراع الشمال وعندك حساسية من أدوية؟") == (
        "وجع الصدر بيمتد للدراع الشمال", "عندك حساسية من أدوية",
    )


@pytest.mark.parametrize("respondent_role", ["mother", "father", "patient"])
@pytest.mark.parametrize("intent", ["diagnosis_attempt", "management_attempt"])
@pytest.mark.asyncio
async def test_generic_diagnosis_guard_speaks_without_gender_assumption(respondent_role, intent):
    repo = FakeRepo()
    repo.snapshot.blueprint["persona"]["respondent_role"] = respondent_role
    model = FakeModel(PatientChatResult(
        intent=intent, answerability="not_applicable", fact_ids=[],
        reply="Pneumonia", parts=[],
    ))
    r = await ChatService(repo, model).send(
        session_id=repo.session_id, user_id=repo.owner,
        request=question("ايه التشخيص النهائي؟"),
    )
    assert r.intent == intent
    assert r.answerability == "not_applicable"
    assert r.fact_ids == []
    assert r.reply == "التشخيص ده حضرتك اللي هتحدده بعد الكشف يا دكتور."
    assert "مش عارفة" not in r.reply
    assert "Pneumonia" not in r.reply
    assert len(repo.events) == 1


@pytest.mark.parametrize("text,expected", [
    ("صباح الخير", "صباح النور يا دكتور."),
    ("صباح الخير يا دكتور", "صباح النور يا دكتور."),
    ("السلام عليكم", "وعليكم السلام، أهلاً يا دكتور."),
    ("مساء الخير", "مساء النور يا دكتور."),
    ("شكراً", "العفو يا دكتور."),
    ("Hello", "أهلاً يا دكتور، اتفضل."),
])
@pytest.mark.asyncio
async def test_general_courtesy_is_persisted_without_an_llm_call(text, expected):
    repo, model = FakeRepo(), FakeModel()
    request = question(text)
    svc = ChatService(repo, model)
    result = await svc.send(session_id=repo.session_id, user_id=repo.owner, request=request)
    assert result.reply == expected
    assert result.intent == "other"
    assert result.answerability == "not_applicable"
    assert result.fact_ids == []
    assert result.model == "rules:salutation"
    assert model.calls == 0
    assert len(repo.events) == 1
    retry = await svc.send(session_id=repo.session_id, user_id=repo.owner, request=request)
    assert retry == result
    assert len(repo.events) == 1


def test_greeting_fast_path_does_not_steal_medical_questions():
    from app.ai.f04.service import safe_greeting_reply
    assert safe_greeting_reply("صباح الخير وعنده سخونية؟", arabic=True) is None
    assert safe_greeting_reply("عامل ايه ووجع الصدر بدأ امتى؟", arabic=True) is None


@pytest.mark.asyncio
async def test_natural_social_reply_is_kept_instead_of_history_fallback():
    repo = FakeRepo()
    model = FakeModel(PatientChatResult(
        intent="other", answerability="not_applicable", fact_ids=[],
        reply="الحمد لله، اتفضل يا دكتور.", parts=[],
    ))
    response = await ChatService(repo, model).send(
        session_id=repo.session_id, user_id=repo.owner,
        request=question("طمنيني، عاملة إيه النهاردة؟"),
    )
    assert response.intent == "other"
    assert response.reply == "الحمد لله، اتفضل يا دكتور."
    assert response.model == "test-model"
    assert response.fact_ids == []
    assert len(repo.events) == 1


@pytest.mark.asyncio
async def test_social_response_cannot_disclose_diagnosis_or_claim_unverified_number():
    for reply in ("عنده التهاب رئوي", "الحرارة 42 درجة"):
        repo = FakeRepo()
        model = FakeModel(PatientChatResult(
            intent="other", answerability="not_applicable", fact_ids=[],
            reply=reply, parts=[],
        ))
        with pytest.raises(HTTPException) as exc:
            await ChatService(repo, model).send(
                session_id=repo.session_id, user_id=repo.owner,
                request=question("احكيلي عن نفسك"),
            )
        assert exc.value.detail["code"] == "AI_RESPONSE_REJECTED"
        assert repo.events == []


@pytest.mark.asyncio
async def test_social_reply_with_fact_citations_is_rejected():
    repo = FakeRepo()
    model = FakeModel(PatientChatResult(
        intent="other", answerability="not_applicable", fact_ids=["fever__0"],
        reply="أهلاً يا دكتور", parts=[],
    ))
    with pytest.raises(HTTPException):
        await ChatService(repo, model).send(
            session_id=repo.session_id, user_id=repo.owner,
            request=question("عايز أتكلم شوية"),
        )
    assert repo.events == []


@pytest.mark.asyncio
async def test_greeting_v08_persists_and_keeps_history_facts_private():
    repo, model = FakeRepo(), FakeModel()
    r = await ChatService(repo, model).send(
        session_id=repo.session_id, user_id=repo.owner, request=question("صباح الخير"))
    assert r.reply == "صباح النور يا دكتور."
    assert r.model == "rules:salutation"
    assert model.calls == 0
    assert repo.messages[-1].content == r.reply


@pytest.mark.asyncio
async def test_patient_name_from_blueprint_without_hardcoding():
    repo, model = FakeRepo(), FakeModel()
    repo.snapshot.blueprint["patient"] = {"display_name": "مريم", "age_months": 24, "sex": "female"}
    repo.snapshot.blueprint["persona"]["respondent_role"] = "mother"
    r = await ChatService(repo, model).send(
        session_id=repo.session_id, user_id=repo.owner, request=question("بنتك اسمها ايه؟"))
    assert "مريم" in r.reply
    assert r.model == "rules:identity"
    assert model.calls == 0
    assert repo.messages[-1].content == r.reply


@pytest.mark.asyncio
async def test_caregiver_not_claiming_patient_name_as_own():
    repo, model = FakeRepo(), FakeModel()
    repo.snapshot.blueprint["patient"]["display_name"] = "مريم"
    repo.snapshot.blueprint["persona"]["respondent_role"] = "mother"
    r = await ChatService(repo, model).send(
        session_id=repo.session_id, user_id=repo.owner, request=question("اسمك ايه؟"))
    assert "والدة مريم" in r.reply
    assert "اسمي مريم" not in r.reply


@pytest.mark.asyncio
async def test_name_is_not_fabricated_when_missing():
    repo, model = FakeRepo(), FakeModel(PatientChatResult(
        intent="other", answerability="not_applicable", fact_ids=[],
        reply="معلش يا دكتور، خلينا نتكلم عن اللي تعبها.", parts=[],
    ))
    repo.snapshot.blueprint["patient"].pop("display_name", None)
    r = await ChatService(repo, model).send(
        session_id=repo.session_id, user_id=repo.owner, request=question("اسمها ايه؟"))
    assert r.model == "test-model"
    assert "مريم" not in r.reply
    assert model.calls == 1


def test_name_questions_do_not_steal_compound_history():
    from app.ai.f04.service import safe_name_reply
    assert safe_name_reply("بنتك اسمها ايه والكحة امتى؟", patient_name="مريم", caregiver="mother", arabic=True, sex="female") is None


def test_model_prompt_has_patient_identity_without_ground_truth():
    from app.ai.f04.blueprint import project_history
    repo = FakeRepo()
    repo.snapshot.blueprint["patient"]["display_name"] = "مريم"
    projection = project_history(repo.snapshot.blueprint)
    prompt = projection.as_prompt_data()
    assert '"patient_display_name": "مريم"' in prompt or '"patient_display_name":"مريم"' in prompt
    assert "Pneumonia" not in prompt
    assert "ground_truth" not in prompt


@pytest.mark.parametrize("question,expected", [
    ("طب والنفس السريع ده بدأ امتى بالظبط؟", ("والنفس السريع ده بدأ امتى بالظبط",)),
    ("طيب، والبول قل امتى؟", ("والبول قل امتى",)),
    ("معلش، والتشنج استمر كام دقيقة؟", ("والتشنج استمر كام دقيقة",)),
    ("طب والكحة بدأت امتى والنفس السريع بدأ امتى؟", (
        "والكحة بدأت امتى", "النفس السريع بدأ امتى")),
    ("طب وجع الصدر بيروح فين؟", ("وجع الصدر بيروح فين",)),
    ("وزنه كام؟", ("وزنه كام",)),
    ("وجع البطن بدأ امتى؟", ("وجع البطن بدأ امتى",)),
])
def test_disourse_openers_are_not_fake_questions(question, expected):
    assert question_parts(question) == expected


@pytest.mark.asyncio
async def test_colloquial_followup_must_not_prepend_unknown_to_known_onset():
    repo = FakeRepo()
    repo.snapshot.blueprint["history_items"] = case_items([
        ("onset_duration", ["Fast breathing began approximately twelve hours ago."])
    ])
    q = "طب والنفس السريع ده بدأ امتى بالظبط؟"
    model = FakeModel(result([
        part("والنفس السريع ده بدأ امتى بالظبط", ["onset_duration__0"],
             "بدأ من حوالي 12 ساعة يا دكتور.")
    ]))
    response = await ChatService(repo, model).send(
        session_id=repo.session_id, user_id=repo.owner, request=question(q))
    assert response.answerability == "answered"
    assert response.fact_ids == ["onset_duration__0"]
    assert response.reply == "بدأ من حوالي 12 ساعة يا دكتور."
    assert "مش عندي معلومة" not in response.reply


@pytest.mark.parametrize("fact,question_text,span,cited,raw_reply,expected_reply", [
    ("Fast breathing started twelve hours ago.",
     "طب والنفس السريع ده بدأ امتى بالظبط؟",
     "والنفس السريع ده بدأ امتى بالظبط", "onset_duration__0",
     "مش عندي معلومة مؤكدة عن الموضوع ده يا دكتور. بدأ من حوالي ١٢ ساعة، من امبارح بالليل.",
     "بدأ من حوالي ١٢ ساعة، من امبارح بالليل."),
    ("Vomiting occurs after feeding.",
     "الترجيع بيحصل بعد الرضاعة؟",
     "الترجيع بيحصل بعد الرضاعة", "onset_duration__0",
     "مش عندي معلومة مؤكدة عن الموضوع ده يا دكتور. أيوه، بعد الرضاعة.",
     "أيوه، بعد الرضاعة."),
])
@pytest.mark.asyncio
async def test_no_unknown_boilerplate_in_supported_answer_across_cases(
    fact, question_text, span, cited, raw_reply, expected_reply,
):
    repo = FakeRepo()
    repo.snapshot.blueprint["history_items"] = case_items([
        ("onset_duration", [fact])
    ])
    model = FakeModel(result([part(span, [cited], raw_reply)]))
    r = await ChatService(repo, model).send(
        session_id=repo.session_id, user_id=repo.owner,
        request=question(question_text))
    assert r.answerability == "answered"
    assert r.reply == expected_reply
    assert r.fact_ids == [cited]
    assert len(repo.events) == 1


@pytest.mark.asyncio
async def test_inconsistent_unknown_wording_rejected_not_saved():
    repo = FakeRepo()
    repo.snapshot.blueprint["history_items"] = case_items([
        ("onset_duration", ["Fast breathing began twelve hours ago."])
    ])
    model = FakeModel(result([part(
        "النفس السريع بدأ امتى", ["onset_duration__0"],
        "مفيش معلومة عن الموضوع بس بدأ من حوالي ١٢ ساعة.",
    )]))
    with pytest.raises(HTTPException) as e:
        await ChatService(repo, model).send(
            session_id=repo.session_id, user_id=repo.owner,
            request=question("النفس السريع بدأ امتى؟"))
    assert e.value.detail["code"] == "AI_RESPONSE_REJECTED"
    assert repo.events == []
    assert repo.reserved == {}


@pytest.mark.asyncio
async def test_previous_bad_patient_answer_is_not_injected_into_new_context():
    from app.ai.f04.contracts import StoredMessage
    repo = FakeRepo()
    repo.snapshot.blueprint["history_items"] = case_items([
        ("onset_duration", ["Fast breathing started twelve hours ago."])
    ])
    bad = "مش عندي معلومة مؤكدة عن الموضوع ده يا دكتور. من حوالي 12 ساعة."
    repo.messages = [
        StoredMessage(role="student", content="النفس سريع من امتى"),
        StoredMessage(role="patient", content=bad),
    ]
    model = FakeModel(result([part(
        "النفس السريع بدأ امتى", ["onset_duration__0"],
        "من حوالي ١٢ ساعة."
    )]))
    r = await ChatService(repo, model).send(
        session_id=repo.session_id, user_id=repo.owner,
        request=question("النفس السريع بدأ امتى؟"))
    assert r.answerability == "answered"
    assert bad not in str(model.last_messages)


@pytest.mark.asyncio
async def test_truly_unknown_part_stays_unknown():
    repo = FakeRepo()
    q = "عنده حساسية من البنسلين؟"
    model = FakeModel(result([part(
        "عنده حساسية من البنسلين", [], "ممكن معرفش", "unknown",
    )]))
    r = await ChatService(repo, model).send(
        session_id=repo.session_id, user_id=repo.owner, request=question(q))
    assert r.answerability == "unknown"
    assert r.reply == "مش عندي معلومة مؤكدة عن الموضوع ده يا دكتور."
    assert r.fact_ids == []
