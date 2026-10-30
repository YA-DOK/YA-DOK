import { localUiDemoCase } from "@/lib/cases/local-ui-demo";
import { connection } from "next/server";
import { listPublishedCases, type StudentCasePage } from "@/lib/cases/api";
import { listLocalDraftPreviews, type PreviewCasePage } from "@/lib/cases/demo-api";
import { GlassCasesBrowser } from "@/components/dashboard/glass-cases-browser";

export const instant = false;

type Params = {specialty?:string|string[]; difficulty?:string|string[]; page?:string|string[]; mode?:string|string[]};
function first(input: string|string[]|undefined) {return typeof input === "string" ? input : input?.[0] || "";}
export default async function CasesLibraryPage({searchParams}: {searchParams:Promise<Params>}) {
  await connection();
  const query = await searchParams;
  const specialty = first(query.specialty).slice(0,100).trim();
  const difficulty = first(query.difficulty).slice(0,60).trim();
  const mode = first(query.mode) === "test" ? "test" : first(query.mode) === "training" ? "training" : "";
  const requested = Number.parseInt(first(query.page),10);
  const page = Number.isSafeInteger(requested) ? Math.max(1, Math.min(requested,834)) : 1;
  let data: PreviewCasePage | StudentCasePage | null = null;
  let error = false;
  try { data = await listPublishedCases({specialty,difficulty,limit:12,offset:(page-1)*12}); }
  catch {error = true;}
  // Only the local development backend can expose draft metadata previews.
  if (process.env.NODE_ENV !== "production" && page === 1) {
    try {
      const drafts = await listLocalDraftPreviews();
      if (drafts?.items.length) {
        data = {items:[...(data?.items || []), ...drafts.items], limit:50, offset:0, has_more:Boolean(data?.has_more)};
        error = false;
      }
    } catch { /* dev-only API optional; published catalogue remains authoritative */ }
  }
  if (process.env.NODE_ENV !== "production" && page === 1) {
    data = {
      items: [
        ...(data?.items || []).filter(
          (item) => item.case_id !== localUiDemoCase.case_id
        ),
        localUiDemoCase,
      ],
      limit: 50,
      offset: 0,
      has_more: Boolean(data?.has_more),
    };
    error = false;
  }

  return <GlassCasesBrowser data={data} error={error} specialty={specialty} difficulty={difficulty} page={page} mode={mode}/>;
}
