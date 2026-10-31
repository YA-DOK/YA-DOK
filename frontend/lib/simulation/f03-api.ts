/**
 * YA-DOK Feature 03 HTTP client.
 * All mutations accept a stable request ID for safe retries.
 */

export type SimulationPhase =
  | "introduction"
  | "history_taking"
  | "examination"
  | "investigations"
  | "diagnosis_and_plan"
  | "completed";

export type SessionData = Record<string, unknown>;

export class SimulationApiError extends Error {
  constructor(
    public readonly status: number,
    message: string
  ) {
    super(message);
    this.name = "SimulationApiError";
  }
}

export function newActionId(): string {
  return crypto.randomUUID();
}

function apiBase(): string {
  const base = process.env.NEXT_PUBLIC_API_URL;

  if (!base) {
    throw new Error("NEXT_PUBLIC_API_URL is not configured");
  }

  return `${base.replace(/\/$/, "")}/api/v1/simulation`;
}

async function callApi(
  token: string,
  path: string,
  method: "GET" | "POST",
  body?: Record<string, unknown>,
  requestId?: string
): Promise<SessionData> {
  if (!token) {
    throw new SimulationApiError(401, "Authentication required");
  }

  const headers: Record<string, string> = {
    Authorization: `Bearer ${token}`,
    Accept: "application/json",
  };

  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }

  if (requestId) {
    headers["Idempotency-Key"] = requestId;
  }

  const response = await fetch(`${apiBase()}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: "no-store",
  });

  const raw = await response.text();
  let parsed: unknown = null;

  try {
    parsed = raw ? JSON.parse(raw) : null;
  } catch {
    parsed = raw;
  }

  if (!response.ok) {
    let message = `Simulation request failed (${response.status})`;

    if (parsed && typeof parsed === "object" && "detail" in parsed) {
      const detail = (parsed as { detail: unknown }).detail;
      message = typeof detail === "string"
        ? detail
        : JSON.stringify(detail);
    }

    throw new SimulationApiError(response.status, message);
  }

  return parsed && typeof parsed === "object" && !Array.isArray(parsed)
    ? parsed as SessionData
    : {};
}

export const simulationApi = {
  // Development only, until F02 supplies approved case versions.
  startDemo(token: string, caseData: Record<string, unknown>) {
    if (process.env.NODE_ENV !== "development") {
      throw new Error("Synthetic sessions are development-only");
    }

    return callApi(token, "/sessions", "POST", {
      case_data: caseData,
    });
  },

  get(token: string, sessionId: string) {
    return callApi(token, `/sessions/${sessionId}`, "GET");
  },

  phase(
    token: string,
    sessionId: string,
    phase: SimulationPhase,
    requestId: string
  ) {
    return callApi(
      token,
      `/sessions/${sessionId}/phase`,
      "POST",
      { phase },
      requestId
    );
  },

  pause(token: string, sessionId: string, requestId: string) {
    return callApi(
      token,
      `/sessions/${sessionId}/pause`,
      "POST",
      undefined,
      requestId
    );
  },

  resume(token: string, sessionId: string, requestId: string) {
    return callApi(
      token,
      `/sessions/${sessionId}/resume`,
      "POST",
      undefined,
      requestId
    );
  },

  diagnosis(
    token: string,
    sessionId: string,
    diagnosis: string,
    treatmentPlan: string,
    requestId: string
  ) {
    return callApi(
      token,
      `/sessions/${sessionId}/diagnosis`,
      "POST",
      {
        diagnosis,
        treatment_plan: treatmentPlan,
      },
      requestId
    );
  },

  complete(token: string, sessionId: string, requestId: string) {
    return callApi(
      token,
      `/sessions/${sessionId}/complete`,
      "POST",
      undefined,
      requestId
    );
  },
};
