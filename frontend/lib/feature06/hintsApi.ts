
export type HintResponse = {
  allowed: boolean;
  hint_level: number | null;
  hint: string | null;
  remaining_hints: number | null;
  reason: string | null;
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "http://127.0.0.1:8000";

export async function requestHint(
  sessionId: string
): Promise<HintResponse> {
  if (!sessionId.trim()) {
    throw new Error("Session ID is required");
  }

  const url =
    `${API_BASE_URL.replace(/\/$/, "")}` +
    `/api/v1/simulations/` +
    `${encodeURIComponent(sessionId)}/hints`;

  const response = await fetch(url, {
    method: "POST",
    credentials: "include",
    cache: "no-store",
    headers: {
      Accept: "application/json",
    },
  });

  const data: unknown = await response.json().catch(() => null);

  if (!response.ok) {
    const message =
      typeof data === "object" &&
      data !== null &&
      "detail" in data &&
      typeof data.detail === "string"
        ? data.detail
        : `Request failed (${response.status})`;

    throw new Error(message);
  }

  if (
    typeof data !== "object" ||
    data === null ||
    !("allowed" in data) ||
    typeof data.allowed !== "boolean"
  ) {
    throw new Error("Invalid hint response");
  }

  return data as HintResponse;
}
