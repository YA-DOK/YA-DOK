/** LOCAL DEV ONLY. Never enable unpublished draft previews in production. */
import "server-only";
import { createClient } from "@/lib/supabase/server";
import type { StudentCasePage, StudentCaseSummary } from "@/lib/cases/api";

export type PreviewCaseSummary = StudentCaseSummary & { demo?: boolean; restricted?: boolean };
export type PreviewCasePage = Omit<StudentCasePage, "items"> & { items: PreviewCaseSummary[] };

const baseUrl = process.env.API_INTERNAL_URL || process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

async function previewRequest(path: string) {
  // This boundary is in addition to the backend local-database guard.
  if (process.env.NODE_ENV === "production") return null;
  const supabase = await createClient();
  const { data: userData } = await supabase.auth.getUser();
  if (!userData.user) return null;
  const { data: sessionData } = await supabase.auth.getSession();
  const token = sessionData.session?.access_token;
  if (!token) return null;
  const response = await fetch(new URL(path, baseUrl), {
    headers: { Authorization: `Bearer ${token}`, Accept: "application/json" },
    cache: "no-store", signal: AbortSignal.timeout(7000),
  });
  return response.ok ? response : null;
}

export async function listLocalDraftPreviews(): Promise<PreviewCasePage | null> {
  const result = await previewRequest("/api/v1/dev/cases?limit=50&offset=0");
  return result ? (await result.json()) as PreviewCasePage : null;
}

export async function getLocalDraftPreview(code: string): Promise<PreviewCaseSummary | null> {
  const result = await previewRequest(`/api/v1/dev/cases/${encodeURIComponent(code)}`);
  return result ? (await result.json()) as PreviewCaseSummary : null;
}
