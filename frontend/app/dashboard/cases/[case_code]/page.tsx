import { connection } from "next/server";
import { notFound } from "next/navigation";
import { getPublishedCase } from "@/lib/cases/api";
import { GlassCasePreview } from "@/components/dashboard/glass-case-preview";

export const instant = false;
export default async function CasePreviewPage({params}:{params:Promise<{case_code:string}>}) {
  await connection();
  const {case_code}=await params;


  let item: Awaited<ReturnType<typeof getPublishedCase>> = null;
  let error = false;
  try {
    item = await getPublishedCase(case_code);
  } catch (err) {
    error = true;
    console.error(
      "[F02 CASE ERROR]",
      err instanceof Error ? err.message : "UNKNOWN_ERROR"
    );
  }

  if (!error && !item) notFound();
  return <GlassCasePreview item={item} error={error}/>;
}
