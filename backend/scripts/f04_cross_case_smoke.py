"""Manual F04 cross-case smoke test (memory only; NO Supabase writes).

Usage, from backend/:
  python scripts/f04_cross_case_smoke.py             # offline fixture/splitter checks
  python scripts/f04_cross_case_smoke.py --live      # 4 REAL OpenRouter calls (paid)

Synthetic engineering scenarios are NOT reviewed medical cases and are NOT
suitable for F02 publication. This is a focused F04 generalization probe.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
import time
from uuid import uuid4
from pathlib import Path

# Direct execution from backend/scripts still needs backend/ on the import path.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx
from fastapi import HTTPException

from app.ai.f04.blueprint import project_history
from app.ai.f04.contracts import (
    PatientReply, Reservation, SendMessageRequest, SessionSnapshot, StoredMessage,
)
from app.ai.f04.coverage import question_parts
from app.ai.f04.provider import ModelSettings, OpenRouterTextModel
from app.ai.f04.service import ChatService
from app.core.config import settings

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")


def history(item_id: str, fact: str | None, *, category: str | None = None) -> dict:
    return {"id": item_id, "category": category or item_id,
            "known": fact is not None, "facts": [fact] if fact else []}


# Deliberately minimum F04 projection fields: cannot be published via F02.
# Facts are invented for *software tests only*, not clinically reviewed cases.
SCENARIOS = {
    "GI_CAREGIVER": {
        "blueprint": {
            "schema_version": "3.2",
            "patient": {"display_name": "Fictional toddler A", "age_months": 16, "sex": "female"},
            "persona": {"respondent_role": "mother", "speech_language": "ar-EG", "emotional_state": "worried"},
            "history_items": [
                history("vomiting", "Vomiting happens shortly after feeding."),
                history("urine_output", "There are fewer wet diapers than usual."),
                history("allergy", None),
            ],
        },
        "questions": [
            ("الترجيع بيحصل بعد الرضاعة والبول قل؟", "answered", {"vomiting__0", "urine_output__0"}, 2),
            ("عندها حساسية من البنسلين؟", "unknown", set(), 1),
        ],
    },
    "ADULT_CHEST_PAIN": {
        "blueprint": {
            "schema_version": "3.2",
            "patient": {"display_name": "Fictional adult B", "age_months": 480, "sex": "female"},
            "persona": {"respondent_role": "patient", "speech_language": "ar-EG", "emotional_state": "anxious"},
            "history_items": [
                history("pain", "Chest pain radiates to the left arm."),
                history("allergy", "No known drug allergies."),
            ],
        },
        "questions": [
            ("وجع الصدر بيمتد للدراع الشمال وعندك حساسية من أدوية؟", "answered", {"pain__0", "allergy__0"}, 2),
        ],
    },
    "NEURO_CAREGIVER": {
        "blueprint": {
            "schema_version": "3.2",
            "patient": {"display_name": "Fictional child C", "age_months": 72, "sex": "male"},
            "persona": {"respondent_role": "father", "speech_language": "ar-EG", "emotional_state": "worried"},
            "history_items": [
                history("seizure", "The seizure lasted four minutes.", category="other"),
                history("past_history", "There have been no previous seizure episodes."),
            ],
        },
        "questions": [
            ("التشنج استمر كام دقيقة وحصل قبل كده؟", "answered", {"seizure__0", "past_history__0"}, 2),
        ],
    },
}


class MemoryRepository:
    """Minimal contract fake; it never opens a DB connection."""
    def __init__(self, blueprint: dict):
        self.user_id = uuid4()
        self.session_id = uuid4()
        self.snapshot = SessionSnapshot(
            session_id=self.session_id, owner_user_id=self.user_id,
            phase="history_taking", is_completed=False, is_paused=False,
            blueprint=blueprint, case_version_id="synthetic-in-memory-only",
            is_approved_version=True,  # mock session only; NOT an F02 approval
        )
        self.reservations: dict = {}
        self.messages: list[StoredMessage] = []

    async def get_session(self, session_id):
        return self.snapshot if session_id == self.session_id else None

    async def find_completed_reply(self, *, session_id, client_message_id, content):
        item = self.reservations.get((session_id, client_message_id))
        return item[1] if item and item[0] == content else None

    async def reserve_message(self, *, session_id, client_message_id, content):
        key = (session_id, client_message_id)
        old = self.reservations.get(key)
        if old is not None:
            if old[0] != content:
                raise HTTPException(409, "IDEMPOTENCY_CONFLICT")
            return Reservation(state="existing", existing=old[1]) if old[1] else Reservation(state="in_progress")
        self.reservations[key] = (content, None)
        return Reservation(state="reserved", lease_token="memory-only")

    async def recent_messages(self, session_id, *, limit):
        return self.messages[-limit:]

    async def finish_message(self, *, session_id, client_message_id, reply: PatientReply, lease_token):
        key = (session_id, client_message_id)
        content, _ = self.reservations[key]
        self.reservations[key] = (content, reply)
        self.messages.extend([StoredMessage(role="student", content=content),
                              StoredMessage(role="patient", content=reply.reply)])

    async def release_reservation(self, *, session_id, client_message_id, lease_token):
        key = (session_id, client_message_id)
        if key in self.reservations and self.reservations[key][1] is None:
            del self.reservations[key]

    async def list_messages(self, *, session_id, limit):
        return self.messages[-limit:]


def offline_check():
    total = 0
    for case_id, entry in SCENARIOS.items():
        projection = project_history(entry["blueprint"])
        print("CASE:", case_id, "ROLE:", projection.caregiver)
        for question, status, expected_ids, n_spans in entry["questions"]:
            spans = question_parts(question)
            assert len(spans) == n_spans, (case_id, spans)
            assert expected_ids.issubset(set(projection.ids)), (case_id, expected_ids)
            print("  QUESTION:", question)
            print("  SPANS:", " | ".join(spans))
            print("  EXPECTED_FACT_IDS:", ", ".join(sorted(expected_ids)) or "(none)")
            total += 1
    print(f"OFFLINE_FIXTURE_CHECK: PASS ({len(SCENARIOS)} cases, {total} questions)")


async def live_run():
    if not settings.openrouter_api_key:
        raise SystemExit("Missing OPENROUTER_API_KEY in project .env; no requests made")
    timeout = 25.0
    cases_passed, total = 0, 0
    async with httpx.AsyncClient() as client:
        model = OpenRouterTextModel(ModelSettings(
            api_key=settings.openrouter_api_key,
            model=settings.llm_model or "openai/gpt-6-luna",
            timeout_seconds=timeout,
        ), client)
        for case_name, entry in SCENARIOS.items():
            repo = MemoryRepository(entry["blueprint"])
            service = ChatService(repo, model)
            for question, expected_answerability, expected_ids, _ in entry["questions"]:
                total += 1
                print("\n===", case_name, "===", flush=True)
                print("QUESTION:", question, flush=True)
                started = time.perf_counter()
                try:
                    result = await service.send(
                        session_id=repo.session_id, user_id=repo.user_id,
                        request=SendMessageRequest(client_message_id=uuid4(), content=question),
                    )
                except HTTPException as exc:
                    detail = exc.detail
                    code = detail.get("code", "UNCLASSIFIED") if isinstance(detail, dict) else "HTTP_ERROR"
                    print("HTTP_STATUS:", exc.status_code, "ERROR_CODE:", code)
                    print("SECONDS:", round(time.perf_counter() - started, 2))
                    continue
                print("ANSWERABILITY:", result.answerability)
                print("FACT_IDS:", ", ".join(result.fact_ids) or "(none)")
                print("REPLY:", result.reply)
                print("MODEL:", result.model)
                print("SECONDS:", round(time.perf_counter() - started, 2))
                ok = (result.intent == "history_question"
                      and result.answerability == expected_answerability
                      and set(result.fact_ids) == expected_ids)
                print("STRUCTURAL_CHECK:", ok)
                cases_passed += int(ok)
    print(f"\nLIVE_STRUCTURAL_RESULTS: {cases_passed}/{total}")
    print("Manual semantic review remains necessary: citations alone do NOT prove clinical relevance.")
    print("NO_SUPABASE_ACCESS_OR_WRITES: True")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="use OpenRouter; up to 4 paid requests, no DB writes")
    args = parser.parse_args()
    offline_check()
    if args.live:
        asyncio.run(live_run())
    else:
        print("Offline-only. To run real-model tests, add --live (4 paid API requests).")
