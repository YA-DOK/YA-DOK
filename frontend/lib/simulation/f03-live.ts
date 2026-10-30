import { getAccessToken } from "@/lib/supabase/client";

export type F03Mode = "training" | "test";
export type F03Phase =
  | "introduction"
  | "history_taking"
  | "examination"
  | "investigations"
  | "diagnosis_and_plan"
  | "completed";

export type F03Session = {
  session_id: string;
  mode?: F03Mode;
  current_phase: F03Phase;
  is_paused: boolean;
  is_completed: boolean;
  diagnosis: string | null;
  treatment_plan: string | null;
  events: {
    event_id: string;
    event_type: string;
    phase: string;
    timestamp: string;
    details: Record<string, unknown>;
  }[];
  messages: {
    role: string;
    action: string;
    content: string;
  }[];
};

export class F03HttpError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
  }
}

const DEMO_CASE = {
  identity: {
    age: 6,
    sex: "male",
    weight_kg: 18,
  },
  presenting_problem: {
    chief_complaint: "Abdominal pain",
  },
  physical_examination: {
    General: "Synthetic patient appears alert and comfortable.",
    Vitals: {
      HR: 92,
      RR: 20,
      Temperature_C: 36.8,
      BP: "102/68",
      SpO2: 98,
    },
  },
  investigations: {
    CBC: "Synthetic teaching example only.",
  },
};

async function request<T>(
  path: string,
  method: "GET" | "POST" = "GET",
  body?: Record<string, unknown>,
  requestId?: string
): Promise<T> {
  const base = process.env.NEXT_PUBLIC_API_URL;

  if (!base) {
    throw new Error("NEXT_PUBLIC_API_URL is missing.");
  }

  const token = await getAccessToken();

  const response = await fetch(
    `${base.replace(/\/$/, "")}/api/v1/simulation${path}`,
    {
      method,
      cache: "no-store",
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: "application/json",
        ...(body ? { "Content-Type": "application/json" } : {}),
        ...(requestId ? { "Idempotency-Key": requestId } : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
    }
  );

  const data: unknown = await response.json().catch(() => null);

  if (!response.ok) {
    const detail =
      data && typeof data === "object" && "detail" in data
        ? (data as { detail: unknown }).detail
        : null;

    throw new F03HttpError(
      response.status,
      typeof detail === "string"
        ? detail
        : `Simulation API returned HTTP ${response.status}`
    );
  }

  return data as T;
}

export const f03Live = {
  ready() {
    return request<{ ready: boolean; storage: string }>("/demo-ready");
  },

  startDemo(mode: F03Mode) {
    return request<F03Session>("/sessions", "POST", {
      mode,
      case_data: DEMO_CASE,
    });
  },

  get(sessionId: string) {
    return request<F03Session>(`/sessions/${sessionId}`);
  },

  action(
    sessionId: string,
    action:
      | "phase"
      | "pause"
      | "resume"
      | "diagnosis"
      | "complete"
      | "examinations"
      | "investigations",
    body: Record<string, unknown>,
    requestId: string
  ) {
    return request<Record<string, unknown>>(
      `/sessions/${sessionId}/${action}`,
      "POST",
      body,
      requestId
    );
  },
};
