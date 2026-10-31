from __future__ import annotations

import json
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.ai.f04.blueprint import project_history
from app.ai.f04.contracts import (
    PatientChatResult,
    Reservation,
    SendMessageRequest,
    SessionSnapshot,
    StoredMessage,
)
from app.ai.f04.provider import ProviderUnavailable
from app.ai.f04.service import ChatService, contains_hidden_answer, numbers_grounded


def blueprint():
    return {
        "schema_version": "3.2",
        "patient": {"age_months": 7, "sex": "male", "display_name": "Fictional"},
        "persona": {"respondent_role": "mother", "speech_language": "ar-EG",
                    "opening_line": "ابني تعبان يا دكتور", "emotional_state": "worried"},
        "history_items": [
            {"id": "fever", "category": "fever", "known": True,
             "facts": ["Fever started two days ago."]},
            {"id": "cough", "category": "cough", "known": True,
             "facts": ["The child has a dry cough."]},
            {"id": "unknown_allergy", "category": "allergy", "known": False, "facts": []},
        ],
        "ground_truth": {
            "final_diagnosis": {"label": "Pneumonia", "leak_terms": ["التهاب رئوي"]},
            "management_in_record": ["Antibiotics were started"],
            "outcome_in_record": "Recovered and discharged",
        },
        "investigations": [{"id": "cbc", "results": [{"id": "wbc", "value": 15000}]}],
        "imaging": [{"id": "cxr", "report_text": "Right basal shadow"}],
    }


class FakeRepo:
    def __init__(self, *, owner=None):
        self.owner = owner or uuid4()
        self.session_id = uuid4()
        self.snapshot = SessionSnapshot(
            session_id=self.session_id, owner_user_id=self.owner,
            phase="history_taking", is_completed=False, is_paused=False,
            blueprint=blueprint(), case_version_id="version-2", is_approved_version=True,
        )
        self.reserved = {}
        self.messages = []
        self.events = []

    async def get_session(self, session_id):
        return self.snapshot if session_id == self.session_id else None

    async def find_completed_reply(self, *, session_id, client_message_id, content):
        previous = self.reserved.get((session_id, client_message_id))
        if previous and previous[0] != content:
            raise HTTPException(409, detail={"code": "IDEMPOTENCY_CONFLICT"})
        return previous[1] if previous else None

    async def recent_messages(self, session_id, *, limit):
        return self.messages[-limit:]

    async def reserve_message(self, *, session_id, client_message_id, content):
        key = (session_id, client_message_id)
        previous = self.reserved.get(key)
        if previous is None:
            self.reserved[key] = (content, None)
            return Reservation(state="reserved", lease_token="mock-lease")
        if previous[0] != content:
            raise HTTPException(409, detail={"code": "IDEMPOTENCY_CONFLICT"})
        return (Reservation(state="existing", existing=previous[1])
                if previous[1] else Reservation(state="in_progress"))

    async def finish_message(self, *, session_id, client_message_id, reply, lease_token):
        key = (session_id, client_message_id)
        content = self.reserved[key][0]
        self.reserved[key] = (content, reply)
        self.messages.extend([StoredMessage(role="student", content=content),
                              StoredMessage(role="patient", content=reply.reply)])
        self.events.append(("chat_exchange", client_message_id, reply.intent, reply.fact_ids))

    async def release_reservation(self, *, session_id, client_message_id, lease_token):
        key = (session_id, client_message_id)
        if key in self.reserved and self.reserved[key][1] is None:
            del self.reserved[key]

    async def list_messages(self, *, session_id, limit):
        return self.messages[-limit:]


class FakeModel:
    def __init__(self, answer=None):
        self.calls = 0
        self.last_messages = []
        self.answer = answer or PatientChatResult(
            intent="history_question", answerability="answered",
            fact_ids=["fever__0"], reply="الحرارة بدأت من يومين يا دكتور.",
        )

    async def generate(self, *, messages, allowed_fact_ids, session_key):
        self.calls += 1
        self.last_messages = messages
        if isinstance(self.answer, Exception):
            raise self.answer
        return self.answer, "test-model"


def call(repo):
    return SendMessageRequest(client_message_id=uuid4(), content="هل عنده سخونية؟")


@pytest.mark.asyncio
async def test_happy_path_one_llm_call_and_events():
    repo, model = FakeRepo(), FakeModel()
    result = await ChatService(repo, model).send(
        session_id=repo.session_id, user_id=repo.owner, request=call(repo))
    assert result.intent == "history_question"
    assert result.fact_ids == ["fever__0"]
    assert len(repo.events) == 1
    assert [x.role for x in repo.messages] == ["student", "patient"]
    assert model.calls == 1


@pytest.mark.asyncio
async def test_private_fields_never_sent_to_model():
    repo, model = FakeRepo(), FakeModel()
    await ChatService(repo, model).send(
        session_id=repo.session_id, user_id=repo.owner, request=call(repo))
    prompt = json.dumps(model.last_messages, ensure_ascii=False)
    for term in ("Pneumonia", "التهاب رئوي", "Antibiotics", "15000", "Right basal shadow", "ground_truth"):
        assert term not in prompt


@pytest.mark.asyncio
async def test_duplicate_idempotency_returns_same_reply_not_extra_call():
    repo, model = FakeRepo(), FakeModel()
    request = call(repo)
    service = ChatService(repo, model)
    a = await service.send(session_id=repo.session_id, user_id=repo.owner, request=request)
    b = await service.send(session_id=repo.session_id, user_id=repo.owner, request=request)
    assert a == b
    assert model.calls == 1
    assert len(repo.events) == 1


@pytest.mark.asyncio
async def test_duplicate_with_different_content_rejected():
    repo, model = FakeRepo(), FakeModel()
    request = call(repo)
    service = ChatService(repo, model)
    await service.send(session_id=repo.session_id, user_id=repo.owner, request=request)
    with pytest.raises(HTTPException) as exc:
        await service.send(session_id=repo.session_id, user_id=repo.owner,
                           request=SendMessageRequest(client_message_id=request.client_message_id,
                                                      content="رسالة مختلفة"))
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_forbidden_owner_returns_not_found_and_no_call():
    repo, model = FakeRepo(), FakeModel()
    with pytest.raises(HTTPException) as exc:
        await ChatService(repo, model).send(
            session_id=repo.session_id, user_id=uuid4(), request=call(repo))
    assert exc.value.status_code == 404
    assert model.calls == 0


@pytest.mark.parametrize("field,value", [
    ("is_completed", True), ("is_paused", True), ("phase", "investigations"),
    ("is_approved_version", False),
])
@pytest.mark.asyncio
async def test_invalid_session_state_rejected_before_call(field, value):
    from dataclasses import replace
    repo, model = FakeRepo(), FakeModel()
    repo.snapshot = replace(repo.snapshot, **{field: value})
    with pytest.raises(HTTPException) as exc:
        await ChatService(repo, model).send(
            session_id=repo.session_id, user_id=repo.owner, request=call(repo))
    assert exc.value.status_code == 409
    assert model.calls == 0


@pytest.mark.asyncio
async def test_unknown_does_not_invent():
    repo = FakeRepo()
    model = FakeModel(PatientChatResult(
        intent="history_question", answerability="unknown", fact_ids=[],
        reply="عنده حساسية قوية من البنسلين.",
    ))
    result = await ChatService(repo, model).send(
        session_id=repo.session_id, user_id=repo.owner, request=call(repo))
    assert "البنسلين" not in result.reply
    assert result.fact_ids == []


@pytest.mark.asyncio
async def test_examination_does_not_autocall_f03_or_fake_results():
    repo = FakeRepo()
    model = FakeModel(PatientChatResult(
        intent="investigation_request", answerability="not_applicable", fact_ids=[],
        reply="WBC 15000",
    ))
    result = await ChatService(repo, model).send(
        session_id=repo.session_id, user_id=repo.owner, request=call(repo))
    assert "15000" not in result.reply
    assert result.intent == "investigation_request"


@pytest.mark.asyncio
async def test_reject_diagnosis_leak_and_no_persistence():
    repo = FakeRepo()
    model = FakeModel(PatientChatResult(
        intent="history_question", answerability="answered", fact_ids=["fever__0"],
        reply="عنده التهاب رئوي",
    ))
    with pytest.raises(HTTPException) as exc:
        await ChatService(repo, model).send(
            session_id=repo.session_id, user_id=repo.owner, request=call(repo))
    assert exc.value.status_code == 503
    assert not repo.events
    assert not repo.reserved


@pytest.mark.asyncio
async def test_reject_unsupported_numeric():
    repo = FakeRepo()
    model = FakeModel(PatientChatResult(
        intent="history_question", answerability="answered", fact_ids=["fever__0"],
        reply="حرارته 41 درجة",
    ))
    with pytest.raises(HTTPException) as exc:
        await ChatService(repo, model).send(
            session_id=repo.session_id, user_id=repo.owner, request=call(repo))
    assert exc.value.status_code == 503


@pytest.mark.asyncio
async def test_provider_failure_retry_can_use_same_key():
    repo, model = FakeRepo(), FakeModel(ProviderUnavailable())
    request = call(repo)
    with pytest.raises(HTTPException) as exc:
        await ChatService(repo, model).send(
            session_id=repo.session_id, user_id=repo.owner, request=request)
    assert exc.value.status_code == 503
    model.answer = PatientChatResult(
        intent="history_question", answerability="answered",
        fact_ids=["fever__0"], reply="الحرارة بدأت من يومين.")
    response = await ChatService(repo, model).send(
        session_id=repo.session_id, user_id=repo.owner, request=request)
    assert response.reply
    assert len(repo.events) == 1


@pytest.mark.asyncio
async def test_retry_after_session_finish_uses_existing_reply():
    from dataclasses import replace
    repo, model = FakeRepo(), FakeModel()
    request = call(repo)
    service = ChatService(repo, model)
    previous = await service.send(session_id=repo.session_id, user_id=repo.owner, request=request)
    repo.snapshot = replace(repo.snapshot, phase="completed", is_completed=True)
    result = await service.send(session_id=repo.session_id, user_id=repo.owner, request=request)
    assert result == previous
    assert model.calls == 1


def test_projection_never_exposes_private_fields():
    proj = project_history(blueprint())
    prompt = proj.as_prompt_data()
    assert '"final_diagnosis"' not in prompt
    assert "Antibiotics" not in prompt
    assert "Pneumonia" not in prompt
    assert len(proj.facts) == 2


def test_numeric_grounding_and_hidden_term_normalization():
    assert numbers_grounded("حرارته 40", "fever 40 C")
    assert not numbers_grounded("حرارته 42", "fever 40 C")
    assert contains_hidden_answer("عنده التهاب رئوي", ("إلتهاب رئوي",))


def test_invalid_case_blueprint_fails_closed():
    b = blueprint()
    b["schema_version"] = "3.1"
    with pytest.raises(HTTPException):
        project_history(b)


@pytest.mark.asyncio
async def test_single_history_question_uses_general_model_not_symptom_specific_rule():
    repo = FakeRepo()
    repo.snapshot.blueprint["history_items"].append({
        "id": "cough_duration", "category": "cough", "known": True,
        "facts": ["The child has been coughing for two days."],
    })
    model = FakeModel(PatientChatResult(
        intent="history_question", answerability="answered", fact_ids=["cough_duration__0"],
        reply="من يومين يا دكتور.",
    ))
    service = ChatService(repo, model)
    request = SendMessageRequest(client_message_id=uuid4(), content="ابنك بيكح من امتى؟")
    response = await service.send(session_id=repo.session_id, user_id=repo.owner, request=request)
    assert response.intent == "history_question"
    assert response.fact_ids == ["cough_duration__0"]
    assert response.model == "test-model"
    assert model.calls == 1
    again = await service.send(session_id=repo.session_id, user_id=repo.owner, request=request)
    assert again == response
    assert model.calls == 1


def test_duration_rescue_only_when_source_is_precise_and_question_relevant():
    from app.ai.f04.duration_router import grounded_duration_answer
    facts = [{"id": "cough__0", "category": "cough", "fact": "The child has been coughing for two days."}]
    assert grounded_duration_answer("ابنك بيكح من امتى؟", facts).reply == "من يومين يا دكتور."
    assert grounded_duration_answer("السخونية بدأت امتى؟", facts) is None
    assert grounded_duration_answer("هو بيكح؟", facts) is None
    assert grounded_duration_answer("ابنك بيكح من امتى؟", [{**facts[0], "fact": "The child has a cough."}]) is None
    assert grounded_duration_answer("ابنك بيكح من امتى؟", [{**facts[0], "fact": "The cough began about two days ago."}]) is None
    assert grounded_duration_answer("ابنك بيكح من امتى؟", [{**facts[0], "fact": "The cough got worse two days ago."}]) is None
    assert grounded_duration_answer("ابنك بيكح من امتى؟", [{**facts[0], "fact": "Cough has been worsening for two days."}]) is None
    assert grounded_duration_answer("ابنك بيكح من امتى؟", [{**facts[0], "fact": "Cough lasted two days and resolved."}]) is None
    assert grounded_duration_answer("ابنك بيكح من امتى وعنده سخونية؟", facts) is None
    fever = [{"id": "fever__0", "category": "fever", "fact": "Fever started three days ago."}]
    assert grounded_duration_answer("السخونية بدأت من امتى؟", fever).reply == "من تلات ايام يا دكتور."


def test_duration_rescue_requires_single_unambiguous_fact():
    from app.ai.f04.duration_router import grounded_duration_answer
    facts = [
        {"id": "cough__0", "category": "cough", "fact": "Coughing for two days."},
        {"id": "cough__1", "category": "cough", "fact": "Coughing for three days."},
    ]
    assert grounded_duration_answer("ابنك بيكح من امتى؟", facts) is None


def test_duration_reads_onset_and_complaint_when_cough_category_has_no_duration():
    from app.ai.f04.duration_router import grounded_duration_answer
    facts = [
        {"id": "chief_complaint__0", "category": "chief_complaint", "fact": "Fever and cough for three days."},
        {"id": "chief_complaint__1", "category": "chief_complaint", "fact": "Breathing became faster last night."},
        {"id": "onset_duration__0", "category": "onset_duration", "fact": "Fever and cough started three days ago."},
        {"id": "onset_duration__1", "category": "onset_duration", "fact": "Fast breathing began approximately twelve hours ago."},
        {"id": "cough__0", "category": "cough", "fact": "Cough is frequent."},
        {"id": "cough__1", "category": "cough", "fact": "Cough has become more noticeable over the last day."},
    ]
    got = grounded_duration_answer("ابنك بيكح من امتى؟", facts)
    assert got is not None
    assert got.fact_id == "onset_duration__0"
    assert got.reply == "من تلات ايام يا دكتور."
    assert grounded_duration_answer("السخونية بدأت امتى؟", facts).fact_id == "onset_duration__0"
    assert grounded_duration_answer("ابنك بيكح من امتى وعنده سخونية؟", facts) is None


def test_duration_does_not_borrow_unrelated_onset_or_hide_disagreement():
    from app.ai.f04.duration_router import grounded_duration_answer
    facts = [
        {"id": "onset_duration__0", "category": "onset_duration", "fact": "Fever started three days ago."},
        {"id": "cough__0", "category": "cough", "fact": "Cough is frequent."},
    ]
    assert grounded_duration_answer("ابنك بيكح من امتى؟", facts) is None
    facts.append({"id": "onset_duration__1", "category": "onset_duration", "fact": "Cough started two days ago."})
    assert grounded_duration_answer("ابنك بيكح من امتى؟", facts).reply == "من يومين يا دكتور."
    facts.append({"id": "chief_complaint__0", "category": "chief_complaint", "fact": "Fever and cough for three days."})
    assert grounded_duration_answer("ابنك بيكح من امتى؟", facts) is None


@pytest.mark.asyncio
async def test_duration_questions_do_not_require_case_specific_python_aliases():
    repo = FakeRepo()
    repo.snapshot.blueprint["history_items"] = [
        {"id": "chief_complaint", "category": "chief_complaint", "known": True,
         "facts": ["Fever and cough for three days."]},
        {"id": "onset_duration", "category": "onset_duration", "known": True,
         "facts": ["Fever and cough started three days ago."]},
        {"id": "cough", "category": "cough", "known": True,
         "facts": ["Cough is frequent.", "Cough has become more noticeable over the last day."]},
    ]
    model = FakeModel(PatientChatResult(
        intent="history_question", answerability="answered", fact_ids=["onset_duration__0"],
        reply="من تلات ايام يا دكتور.",
    ))
    request = SendMessageRequest(client_message_id=uuid4(), content="ابنك بيكح من امتى؟")
    service = ChatService(repo, model)
    result = await service.send(session_id=repo.session_id, user_id=repo.owner, request=request)
    assert result.fact_ids == ["onset_duration__0"]
    assert result.model == "test-model"
    assert model.calls == 1
    assert len(repo.events) == 1
    repeated = await service.send(session_id=repo.session_id, user_id=repo.owner, request=request)
    assert repeated == result
    assert model.calls == 1


def test_duration_does_not_confuse_symptom_onset_with_worsening_or_resolution():
    from app.ai.f04.duration_router import grounded_duration_answer
    facts = [
        {"id": "chief_complaint__0", "category": "chief_complaint", "fact": "Fever and cough for three days."},
        {"id": "onset_duration__0", "category": "onset_duration", "fact": "Fever and cough started three days ago."},
        {"id": "cough__0", "category": "cough", "fact": "Cough is frequent."},
        {"id": "cough__1", "category": "cough", "fact": "Cough has become more noticeable over the last day."},
    ]
    onset = grounded_duration_answer("ابنك بيكح من امتى؟", facts)
    assert onset is not None and onset.fact_id == "onset_duration__0"
    for question in (
        "الكحة زادت امتى؟",
        "الكحة بقت أسوأ امتى؟",
        "الكحة بتزيد من امتى؟",
        "الكحة خفت امتى؟",
        "الكحة بقت أحسن امتى؟",
        "مبقاش بيكح من امتى؟",
        "How long since cough got worse?",
    ):
        assert grounded_duration_answer(question, facts) is None, question


@pytest.mark.asyncio
async def test_worsening_question_uses_model_and_worsening_fact_not_onset_rule():
    repo = FakeRepo()
    repo.snapshot.blueprint["history_items"] = [
        {"id": "chief_complaint", "category": "chief_complaint", "known": True,
         "facts": ["Fever and cough for three days."]},
        {"id": "onset_duration", "category": "onset_duration", "known": True,
         "facts": ["Fever and cough started three days ago."]},
        {"id": "cough", "category": "cough", "known": True,
         "facts": ["Cough is frequent.", "Cough has become more noticeable over the last day."]},
    ]
    model = FakeModel(PatientChatResult(
        intent="history_question", answerability="answered", fact_ids=["cough__1"],
        reply="الكحة بقت أوضح خلال آخر يوم يا دكتور.",
    ))
    result = await ChatService(repo, model).send(
        session_id=repo.session_id, user_id=repo.owner,
        request=SendMessageRequest(client_message_id=uuid4(), content="الكحة زادت امتى؟"),
    )
    assert result.fact_ids == ["cough__1"]
    assert result.model == "test-model"
    assert model.calls == 1
