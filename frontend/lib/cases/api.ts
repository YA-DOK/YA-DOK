/** Server-only adapter for the Feature 02 learner-safe FastAPI endpoints. */
import "server-only";
import { createClient } from "@/lib/supabase/server";

export type StudentCaseSummary = {
  case_id: string;
  version_number: number;
  title: string | null;
  subtitle: string | null;
  short_brief: string | null;
  specialty: string | null;
  setting: string | null;
  difficulty: string | null;
  estimated_duration_minutes: number | null;
};

export type StudentCasePage = {
  items: StudentCaseSummary[];
  limit: number;
  offset: number;
  has_more: boolean;
};

export type CaseFilters = {
  specialty?: string;
  difficulty?: string;
  limit?: number;
  offset?: number;
};

const baseUrl =
  process.env.API_INTERNAL_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

async function authenticatedGet(path: string): Promise<Response> {
  const supabase = await createClient();

  // getUser verifies the user with Supabase; getSession is used *only* to read
  // the access token. FastAPI validates that JWT again on every request.
  const { data: userData, error: userError } = await supabase.auth.getUser();
  if (userError || !userData.user) {
    throw new Error("AUTH_REQUIRED");
  }

  const { data: sessionData, error: sessionError } =
    await supabase.auth.getSession();
  const accessToken = sessionData.session?.access_token;
  if (sessionError || !accessToken) {
    throw new Error("AUTH_REQUIRED");
  }

  return fetch(new URL(path, baseUrl), {
    method: "GET",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      Accept: "application/json",
    },
    cache: "no-store",
    signal: AbortSignal.timeout(10000),
  });
}

export async function listPublishedCases(
  filters: CaseFilters = {},
): Promise<StudentCasePage> {
  const q = new URLSearchParams();
  if (filters.specialty) q.set("specialty", filters.specialty);
  if (filters.difficulty) q.set("difficulty", filters.difficulty);
  q.set("limit", String(filters.limit ?? 12));
  q.set("offset", String(filters.offset ?? 0));

  const response = await authenticatedGet(`/api/v1/cases?${q.toString()}`);
  if (!response.ok) throw new Error(`CASE_LIBRARY_HTTP_${response.status}`);
  return (await response.json()) as StudentCasePage;
}

export async function getPublishedCase(
  caseCode: string,
): Promise<StudentCaseSummary | null> {
  const response = await authenticatedGet(
    `/api/v1/cases/${encodeURIComponent(caseCode)}`,
  );
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`CASE_PREVIEW_HTTP_${response.status}`);
  return (await response.json()) as StudentCaseSummary;
}
