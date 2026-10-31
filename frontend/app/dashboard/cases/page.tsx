import { connection } from "next/server";
import { listPublishedCases, type StudentCasePage } from "@/lib/cases/api";
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
  let data: StudentCasePage | null = null;
  let error = false;
  try { data = await listPublishedCases({specialty,difficulty,limit:12,offset:(page-1)*12}); }
  catch {error = true;}
  return <GlassCasesBrowser data={data} error={error} specialty={specialty} difficulty={difficulty} page={page} mode={mode}/>;
}
