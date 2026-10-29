"use client";

import { useCallback, useRef, useState } from "react";
import { createClient } from "@/lib/supabase/client";

type Phase =
  | "introduction"
  | "history_taking"
  | "examination"
  | "investigations"
  | "diagnosis_and_plan"
  | "completed";

type ChatMessage = {
  role: "patient" | "doctor" | "system";
  content: string;
};

type SimulationSession = {
  session_id: string;
  current_phase: Phase;
  is_completed?: boolean;
  is_paused?: boolean;
};

const PHASES: { id: Phase; label: string }[] = [
  { id: "introduction", label: "Introduction" },
  { id: "history_taking", label: "Medical History" },
  { id: "examination", label: "Physical Examination" },
  { id: "investigations", label: "Investigations" },
  { id: "diagnosis_and_plan", label: "Diagnosis & Treatment" },
  { id: "completed", label: "Completed" },
];

const SAMPLE_CASE = {
  patient: {
    name: "مريض تجريبي",
    age: 35,
    sex: "male",
  },
  chief_complaint: "ألم في البطن بقاله يومين",
  history: {
    symptoms: "ألم في البطن بدأ من يومين",
    duration: "يومين",
    associated_symptoms: [],
    medical_history: [],
    medications: [],
    allergies: [],
  },
  physical_examination: {},
  investigations: {},
  diagnosis: "مثال تعليمي فقط - غير محدد",
  treatment_plan: "مثال تعليمي فقط - يُحدد حسب الحالة",
};

const PHASE_DESCRIPTIONS: Record<Phase, string> = {
  introduction:
    "Start by introducing yourself to the patient and understanding the reason for the visit.",
  history_taking:
    "Gather details about the symptoms and medical history.",
  examination: "Request the appropriate physical examinations.",
  investigations:
    "Request the necessary laboratory tests and investigations.",
  diagnosis_and_plan:
    "Enter your suspected diagnosis and treatment plan.",
  completed: "The simulation has ended.",
};

function getErrorMessage(data: unknown): string {
  if (typeof data === "string") return data;

  if (data && typeof data === "object") {
    const value = data as Record<string, unknown>;

    if (typeof value.detail === "string") return value.detail;
    if (typeof value.message === "string") return value.message;
    if (typeof value.error === "string") return value.error;
  }

  return "An unexpected error occurred. Please try again.";
}

function getResponseText(data: unknown): string {
  if (typeof data === "string") return data;

  if (data && typeof data === "object") {
    const value = data as Record<string, unknown>;

    for (const key of [
      "answer",
      "response",
      "message",
      "result",
      "content",
      "reply",
    ]) {
      if (typeof value[key] === "string") {
        return value[key] as string;
      }
    }

    return JSON.stringify(data, null, 2);
  }

  return "The request was completed, but no additional response details were returned.";
}

export default function SimulationPage() {
  const [caseJson, setCaseJson] = useState(
    JSON.stringify(SAMPLE_CASE, null, 2),
  );

  const [session, setSession] = useState<SimulationSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState("");
  const [examination, setExamination] = useState("");
  const [investigation, setInvestigation] = useState("");
  const [diagnosis, setDiagnosis] = useState("");
  const [treatmentPlan, setTreatmentPlan] = useState("");
  const [resultLog, setResultLog] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Prevents concurrent requests when buttons are clicked rapidly.
  const actionLock = useRef(false);

  const apiBase = (
    process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"
  ).replace(/\/+$/, "");

  const apiRequest = useCallback(
    async (path: string, method = "GET", body?: unknown) => {
      const supabase = createClient();

      const {
        data: { session: authSession },
        error: authError,
      } = await supabase.auth.getSession();

      if (authError || !authSession?.access_token) {
        throw new Error(
          "You need to sign in first. Return to the login page and try again.",
        );
      }

      const response = await fetch(
        `${apiBase}/api/v1/simulation${path}`,
        {
          method,
          headers: {
            Authorization: `Bearer ${authSession.access_token}`,
            "Content-Type": "application/json",
          },
          ...(body !== undefined
            ? { body: JSON.stringify(body) }
            : {}),
        },
      );

      const text = await response.text();
      let data: unknown = null;

      if (text) {
        try {
          data = JSON.parse(text);
        } catch {
          data = text;
        }
      }

      if (!response.ok) {
        throw new Error(
          `HTTP ${response.status}: ${getErrorMessage(data)}`,
        );
      }

      return data;
    },
    [apiBase],
  );

  async function runAction(action: () => Promise<void>) {
    if (actionLock.current) return;

    actionLock.current = true;
    setLoading(true);
    setError("");

    try {
      await action();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "An error occurred while performing the operation.",
      );
    } finally {
      actionLock.current = false;
      setLoading(false);
    }
  }

  function requirePhase(expected: Phase, message: string): boolean {
    if (!session) {
      setError("Start a simulation session first.");
      return false;
    }

    if (session.is_completed || session.current_phase === "completed") {
      setError("The session has already ended.");
      return false;
    }

    if (session.is_paused) {
      setError("The session is paused.");
      return false;
    }

    if (session.current_phase !== expected) {
      setError(message);
      return false;
    }

    return true;
  }

  async function startSimulation() {
    await runAction(async () => {
      let parsedCase: unknown;

      try {
        parsedCase = JSON.parse(caseJson);
      } catch {
        throw new Error("The case data is not valid JSON.");
      }

      if (
        !parsedCase ||
        typeof parsedCase !== "object" ||
        Array.isArray(parsedCase)
      ) {
        throw new Error("The case data must be a JSON object.");
      }

      const data = (await apiRequest("/sessions", "POST", {
        case_data: parsedCase,
      })) as SimulationSession;

      if (!data?.session_id) {
        throw new Error("The backend did not return a session ID.");
      }

      setSession(data);
      setMessages([
        {
          role: "system",
          content: "The simulation session started successfully.",
        },
      ]);
      setResultLog([]);
      setDiagnosis("");
      setTreatmentPlan("");
      setQuestion("");
      setExamination("");
      setInvestigation("");
    });
  }

  async function sendQuestion() {
    if (!question.trim()) return;

    if (
      !requirePhase(
        "history_taking",
        "Patient questions are only available during the medical history phase. Move to the appropriate phase first.",
      )
    ) {
      return;
    }

    const submittedQuestion = question.trim();

    await runAction(async () => {
      const data = await apiRequest(
        `/sessions/${session!.session_id}/patient-question`,
        "POST",
        { question: submittedQuestion },
      );

      setMessages((current) => [
        ...current,
        { role: "doctor", content: submittedQuestion },
        { role: "patient", content: getResponseText(data) },
      ]);

      setQuestion("");
    });
  }

  async function requestExamination() {
    if (!examination.trim()) return;

    if (
      !requirePhase(
        "examination",
        "Physical examination requests are only available during the physical examination phase.",
      )
    ) {
      return;
    }

    const name = examination.trim();

    await runAction(async () => {
      const data = await apiRequest(
        `/sessions/${session!.session_id}/examinations`,
        "POST",
        { examination_name: name },
      );

      setResultLog((current) => [
        `Physical examination: ${name}\n${getResponseText(data)}`,
        ...current,
      ]);

      setExamination("");
    });
  }

  async function requestInvestigation() {
    if (!investigation.trim()) return;

    if (
      !requirePhase(
        "investigations",
        "Investigation requests are only available during the investigations phase.",
      )
    ) {
      return;
    }

    const name = investigation.trim();

    await runAction(async () => {
      const data = await apiRequest(
        `/sessions/${session!.session_id}/investigations`,
        "POST",
        { investigation_name: name },
      );

      setResultLog((current) => [
        `Test or investigation: ${name}\n${getResponseText(data)}`,
        ...current,
      ]);

      setInvestigation("");
    });
  }

  async function advancePhase() {
    if (!session) return;

    if (session.is_completed || session.current_phase === "completed") {
      setError("The session has already ended.");
      return;
    }

    const currentIndex = PHASES.findIndex(
      (phase) => phase.id === session.current_phase,
    );

    if (currentIndex < 0) {
      setError("The current phase is unknown. Start a new session.");
      return;
    }

    const nextPhase = PHASES[currentIndex + 1];

    if (!nextPhase || nextPhase.id === "completed") {
      setError("Cannot move to another phase. Complete the diagnosis first.");
      return;
    }

    await runAction(async () => {
      const data = (await apiRequest(
        `/sessions/${session.session_id}/phase`,
        "POST",
        { phase: nextPhase.id },
      )) as Partial<SimulationSession>;

      // Use the phase returned by the backend when available.
      const confirmedPhase = data?.current_phase;

      if (
        confirmedPhase &&
        !PHASES.some((phase) => phase.id === confirmedPhase)
      ) {
        throw new Error("The backend returned an unrecognized phase name.");
      }

      const phaseToUse = confirmedPhase ?? nextPhase.id;

      setSession((current) =>
        current
          ? {
              ...current,
              current_phase: phaseToUse,
            }
          : current,
      );

      const confirmedLabel =
        PHASES.find((phase) => phase.id === phaseToUse)?.label ??
        phaseToUse;

      setMessages((current) => [
        ...current,
        {
          role: "system",
          content: `Current phase: ${confirmedLabel}`,
        },
      ]);
    });
  }

  async function submitDiagnosis() {
    if (
      !requirePhase(
        "diagnosis_and_plan",
        "Submit the diagnosis and treatment plan only during the diagnosis and treatment phase.",
      )
    ) {
      return;
    }

    if (!diagnosis.trim() || !treatmentPlan.trim()) {
      setError("Enter the diagnosis and treatment plan first.");
      return;
    }

    await runAction(async () => {
      const data = await apiRequest(
        `/sessions/${session!.session_id}/diagnosis`,
        "POST",
        {
          diagnosis: diagnosis.trim(),
          treatment_plan: treatmentPlan.trim(),
        },
      );

      setResultLog((current) => [
        `Diagnosis and treatment plan submitted.\n${getResponseText(data)}`,
        ...current,
      ]);
    });
  }

  async function completeSimulation() {
    if (!session) return;

    if (session.current_phase !== "diagnosis_and_plan") {
      setError(
        "Move to the diagnosis and treatment phase before ending the session.",
      );
      return;
    }

    await runAction(async () => {
      await apiRequest(
        `/sessions/${session.session_id}/complete`,
        "POST",
      );

      setSession((current) =>
        current
          ? {
              ...current,
              current_phase: "completed",
              is_completed: true,
            }
          : current,
      );

      setMessages((current) => [
        ...current,
        {
          role: "system",
          content:
            "The session has ended. Review the results log and the diagnosis you submitted.",
        },
      ]);
    });
  }

  const currentPhaseIndex = session
    ? PHASES.findIndex((phase) => phase.id === session.current_phase)
    : -1;

  const isCompleted =
    Boolean(session?.is_completed) ||
    session?.current_phase === "completed";

  const currentPhase = session?.current_phase;

  return (
    <main
      dir="ltr"
      className="min-h-screen bg-[#F5F7F3] px-4 py-6 text-[#20392D] sm:px-6 lg:px-8"
    >
      <div className="mx-auto max-w-7xl space-y-6">
        <header className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm font-medium text-[#6A8A76]">
              YA-DOK / Simulation Engine
            </p>

            <h1 className="mt-2 text-2xl font-bold sm:text-3xl">
              Clinical Simulation
            </h1>

            <p className="mt-2 text-sm leading-7 text-[#718174]">
              Practice clinical reasoning through an interactive session.
            </p>
          </div>

          {session && (
            <div className="rounded-xl border border-[#DFE8DC] bg-white px-4 py-3 text-sm">
              <span className="text-[#718174]">Session ID: </span>
              <span className="font-mono font-semibold">
                {session.session_id.slice(0, 8)}
              </span>
            </div>
          )}
        </header>

        {error && (
          <div
            role="alert"
            className="flex items-start justify-between gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800"
          >
            <p className="leading-7">{error}</p>

            <button
              type="button"
              onClick={() => setError("")}
              className="font-bold"
              aria-label="Close error message"
            >
              ×
            </button>
          </div>
        )}

        {!session ? (
          <section className="rounded-2xl border border-[#DFE8DC] bg-white p-5 shadow-sm sm:p-8">
            <div className="max-w-3xl">
              <span className="rounded-full bg-[#ECF3EB] px-3 py-1.5 text-xs font-semibold text-[#397253]">
                New Session
              </span>

              <h2 className="mt-5 text-xl font-bold">
                Start with a Medical Case
              </h2>

              <p className="mt-2 text-sm leading-7 text-[#718174]">
                Paste the case data in JSON format. You can use the sample
                below for testing or replace it with case data from the case
                management system.
              </p>
            </div>

            <div className="mt-6">
              <div className="mb-2 flex items-center justify-between gap-3">
                <label
                  htmlFor="case-json"
                  className="text-sm font-semibold"
                >
                  Medical Case Data
                </label>

                <button
                  type="button"
                  onClick={() =>
                    setCaseJson(JSON.stringify(SAMPLE_CASE, null, 2))
                  }
                  className="text-xs font-semibold text-[#397253] underline"
                >
                  Restore Example
                </button>
              </div>

              <textarea
                id="case-json"
                value={caseJson}
                onChange={(event) => setCaseJson(event.target.value)}
                spellCheck={false}
                className="min-h-[320px] w-full rounded-xl border border-[#DDE6DA] bg-[#FAFCF9] p-4 font-mono text-sm leading-6 outline-none focus:border-[#6A9A75] focus:ring-2 focus:ring-[#6A9A75]/15"
              />
            </div>

            <button
              type="button"
              onClick={startSimulation}
              disabled={loading}
              className="mt-5 rounded-xl bg-[#153E32] px-6 py-3 text-sm font-bold text-white transition hover:bg-[#245440] disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "Starting session..." : "Start Simulation"}
            </button>

            <p className="mt-4 text-xs leading-6 text-[#87958A]">
              This sample is for technical integration testing only; it is not
              a verified medical case or a treatment recommendation.
            </p>
          </section>
        ) : (
          <>
            {/* Phase progress */}
            <section className="rounded-2xl border border-[#DFE8DC] bg-white p-5 shadow-sm sm:p-6">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <h2 className="font-bold">Session Phases</h2>

                <span className="text-sm text-[#718174]">
                  {isCompleted ? "Session Completed" : "Current Phase"}
                </span>
              </div>

              <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
                {PHASES.map((phase, index) => {
                  const active = index === currentPhaseIndex;
                  const finished = index < currentPhaseIndex;

                  return (
                    <div
                      key={phase.id}
                      className={`rounded-xl border p-3 ${
                        active
                          ? "border-[#397253] bg-[#ECF3EB]"
                          : finished
                            ? "border-[#D7E5D3] bg-[#F7FAF5]"
                            : "border-[#E7ECE5] bg-white"
                      }`}
                    >
                      <div
                        className={`flex h-8 w-8 items-center justify-center rounded-lg text-xs font-bold ${
                          active || finished
                            ? "bg-[#397253] text-white"
                            : "bg-[#F0F2ED] text-[#718174]"
                        }`}
                      >
                        {finished
                          ? "✓"
                          : String(index + 1).padStart(2, "0")}
                      </div>

                      <p className="mt-3 text-sm font-semibold">
                        {phase.label}
                      </p>
                    </div>
                  );
                })}
              </div>

              {currentPhase && (
                <p className="mt-5 text-sm leading-7 text-[#718174]">
                  {PHASE_DESCRIPTIONS[currentPhase]}
                </p>
              )}

              {!isCompleted && (
                <button
                  type="button"
                  onClick={advancePhase}
                  disabled={
                    loading ||
                    currentPhaseIndex < 0 ||
                    currentPhaseIndex >= PHASES.length - 2
                  }
                  className="mt-4 rounded-xl border border-[#D6E2D2] px-4 py-2.5 text-sm font-semibold text-[#356B47] hover:bg-[#F4F8F2] disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Next Phase →
                </button>
              )}
            </section>

            <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1.3fr)_minmax(320px,0.7fr)]">
              {/* Patient chat */}
              <section className="overflow-hidden rounded-2xl border border-[#DFE8DC] bg-white shadow-sm">
                <div className="border-b border-[#E7ECE5] p-5">
                  <h2 className="font-bold">Patient Chat</h2>

                  <p className="mt-1 text-sm text-[#718174]">
                    {currentPhase === "history_taking"
                      ? "Ask about symptoms and medical history."
                      : "Patient chat is only available during the medical history phase."}
                  </p>
                </div>

                <div
                  aria-live="polite"
                  className="flex min-h-[320px] max-h-[480px] flex-col gap-3 overflow-y-auto bg-[#FAFCF9] p-4"
                >
                  {messages.map((message, index) => (
                    <div
                      key={`${index}-${message.role}`}
                      className={`max-w-[90%] whitespace-pre-wrap rounded-2xl p-3 text-sm leading-7 ${
                        message.role === "doctor"
                          ? "self-start rounded-br-sm bg-[#153E32] text-white"
                          : message.role === "patient"
                            ? "self-end rounded-bl-sm border border-[#DFE8DC] bg-white text-[#20392D]"
                            : "self-center bg-[#ECF3EB] text-[#397253]"
                      }`}
                    >
                      <p className="mb-1 text-xs font-bold opacity-75">
                        {message.role === "doctor"
                          ? "You - Doctor"
                          : message.role === "patient"
                            ? "Patient"
                            : "System"}
                      </p>

                      {message.content}
                    </div>
                  ))}
                </div>

                {!isCompleted && (
                  <form
                    className="flex gap-2 border-t border-[#E7ECE5] p-4"
                    onSubmit={(event) => {
                      event.preventDefault();
                      void sendQuestion();
                    }}
                  >
                    <input
                      value={question}
                      onChange={(event) => setQuestion(event.target.value)}
                      placeholder="Example: When did the pain start?"
                      maxLength={3000}
                      disabled={
                        loading || currentPhase !== "history_taking"
                      }
                      className="min-w-0 flex-1 rounded-xl border border-[#DDE6DA] px-4 py-3 text-sm outline-none focus:border-[#6A9A75] disabled:bg-gray-100"
                    />

                    <button
                      type="submit"
                      disabled={
                        loading ||
                        !question.trim() ||
                        currentPhase !== "history_taking" ||
                        isCompleted
                      }
                      className="rounded-xl bg-[#153E32] px-4 py-3 text-sm font-bold text-white disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      Send
                    </button>
                  </form>
                )}
              </section>

              {/* Clinical actions */}
              <div className="space-y-5">
                <section className="rounded-2xl border border-[#DFE8DC] bg-white p-5 shadow-sm">
                  <h2 className="font-bold">Physical Examination</h2>

                  <p className="mt-2 text-sm leading-7 text-[#718174]">
                    {currentPhase === "examination"
                      ? "Enter the physical examination you want to request."
                      : "Available when you reach the physical examination phase."}
                  </p>

                  <form
                    className="mt-4 space-y-3"
                    onSubmit={(event) => {
                      event.preventDefault();
                      void requestExamination();
                    }}
                  >
                    <input
                      value={examination}
                      onChange={(event) => setExamination(event.target.value)}
                      placeholder="Example: Abdominal examination"
                      maxLength={200}
                      disabled={
                        loading || currentPhase !== "examination"
                      }
                      className="w-full rounded-xl border border-[#DDE6DA] px-3 py-3 text-sm outline-none focus:border-[#6A9A75] disabled:bg-gray-100"
                    />

                    <button
                      type="submit"
                      disabled={
                        loading ||
                        isCompleted ||
                        currentPhase !== "examination" ||
                        !examination.trim()
                      }
                      className="w-full rounded-xl border border-[#D6E2D2] px-4 py-3 text-sm font-semibold text-[#356B47] hover:bg-[#F4F8F2] disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      Request Examination
                    </button>
                  </form>
                </section>

                <section className="rounded-2xl border border-[#DFE8DC] bg-white p-5 shadow-sm">
                  <h2 className="font-bold">Tests & Investigations</h2>

                  <p className="mt-2 text-sm leading-7 text-[#718174]">
                    {currentPhase === "investigations"
                      ? "Request a laboratory test or diagnostic investigation."
                      : "Available when you reach the investigations phase."}
                  </p>

                  <form
                    className="mt-4 space-y-3"
                    onSubmit={(event) => {
                      event.preventDefault();
                      void requestInvestigation();
                    }}
                  >
                    <input
                      value={investigation}
                      onChange={(event) =>
                        setInvestigation(event.target.value)
                      }
                      placeholder="Example: Complete blood count (CBC)"
                      maxLength={200}
                      disabled={
                        loading || currentPhase !== "investigations"
                      }
                      className="w-full rounded-xl border border-[#DDE6DA] px-3 py-3 text-sm outline-none focus:border-[#6A9A75] disabled:bg-gray-100"
                    />

                    <button
                      type="submit"
                      disabled={
                        loading ||
                        isCompleted ||
                        currentPhase !== "investigations" ||
                        !investigation.trim()
                      }
                      className="w-full rounded-xl border border-[#D6E2D2] px-4 py-3 text-sm font-semibold text-[#356B47] hover:bg-[#F4F8F2] disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      Request Test
                    </button>
                  </form>
                </section>

                <section className="rounded-2xl border border-[#DFE8DC] bg-white p-5 shadow-sm">
                  <h2 className="font-bold">Diagnosis & Treatment Plan</h2>

                  <p className="mt-2 text-sm leading-7 text-[#718174]">
                    {currentPhase === "diagnosis_and_plan"
                      ? "Record your clinical conclusion and proposed plan."
                      : "Diagnosis entry is available during the diagnosis and treatment phase."}
                  </p>

                  <div className="mt-4 space-y-3">
                    <label
                      htmlFor="diagnosis"
                      className="block text-sm font-medium"
                    >
                      Suspected Diagnosis
                    </label>

                    <textarea
                      id="diagnosis"
                      value={diagnosis}
                      onChange={(event) => setDiagnosis(event.target.value)}
                      rows={3}
                      placeholder="Enter the diagnosis and your reasoning..."
                      disabled={
                        loading || currentPhase !== "diagnosis_and_plan"
                      }
                      className="w-full rounded-xl border border-[#DDE6DA] p-3 text-sm leading-6 outline-none focus:border-[#6A9A75] disabled:bg-gray-100"
                    />

                    <label
                      htmlFor="treatment-plan"
                      className="block text-sm font-medium"
                    >
                      Treatment Plan
                    </label>

                    <textarea
                      id="treatment-plan"
                      value={treatmentPlan}
                      onChange={(event) =>
                        setTreatmentPlan(event.target.value)
                      }
                      rows={4}
                      placeholder="Enter the treatment and required follow-up plan..."
                      disabled={
                        loading || currentPhase !== "diagnosis_and_plan"
                      }
                      className="w-full rounded-xl border border-[#DDE6DA] p-3 text-sm leading-6 outline-none focus:border-[#6A9A75] disabled:bg-gray-100"
                    />

                    <button
                      type="button"
                      onClick={submitDiagnosis}
                      disabled={
                        loading ||
                        isCompleted ||
                        currentPhase !== "diagnosis_and_plan"
                      }
                      className="w-full rounded-xl bg-[#397253] px-4 py-3 text-sm font-bold text-white hover:bg-[#2D6145] disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      Submit Diagnosis & Plan
                    </button>
                  </div>
                </section>

                <section className="rounded-2xl border border-[#DFE8DC] bg-white p-5 shadow-sm">
                  <h2 className="font-bold">Results Log</h2>

                  {resultLog.length === 0 ? (
                    <p className="mt-3 text-sm leading-7 text-[#87958A]">
                      Examination results and responses will appear here after
                      requests are processed.
                    </p>
                  ) : (
                    <div className="mt-4 space-y-3">
                      {resultLog.map((result, index) => (
                        <pre
                          key={`${index}-${result.slice(0, 15)}`}
                          className="whitespace-pre-wrap break-words rounded-xl bg-[#F6F8F4] p-3 text-xs leading-6 text-[#405747]"
                        >
                          {result}
                        </pre>
                      ))}
                    </div>
                  )}
                </section>

                {!isCompleted && (
                  <button
                    type="button"
                    onClick={completeSimulation}
                    disabled={loading}
                    className="w-full rounded-xl bg-[#153E32] px-5 py-4 text-sm font-bold text-white transition hover:bg-[#245440] disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {loading ? "Processing..." : "End Simulation"}
                  </button>
                )}

                {isCompleted && (
                  <div className="rounded-xl border border-[#CFE1CB] bg-[#ECF3EB] p-4 text-sm font-semibold leading-7 text-[#356B47]">
                    The session has ended successfully. The results shown here
                    are the responses returned by the backend.
                  </div>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </main>
  );
}