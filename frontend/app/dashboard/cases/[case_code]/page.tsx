import { localUiDemoCase } from "@/lib/cases/local-ui-demo";
import { connection } from "next/server";
import { notFound } from "next/navigation";
import { getPublishedCase } from "@/lib/cases/api";
import { getLocalDraftPreview } from "@/lib/cases/demo-api";
import { GlassCasePreview } from "@/components/dashboard/glass-case-preview";

export const instant = false;
export default async function CasePreviewPage({params}:{params:Promise<{case_code:string}>}) {
  await connection();
  const {case_code}=await params;
  if (
    process.env.NODE_ENV !== "production" &&
    case_code === localUiDemoCase.case_id
  ) {
    return <GlassCasePreview item={localUiDemoCase} error={false}/>;
  }

  let item: Awaited<ReturnType<typeof getPublishedCase>> = null;
  let error = false;
  try {item=await getPublishedCase(case_code);} catch {error=true;}
  if (process.env.NODE_ENV !== "production" && !item) {
    try { item = await getLocalDraftPreview(case_code); if(item) error = false; } catch { /* local-only */ }
  }
  if (!error && !item) notFound();
  return <GlassCasePreview item={item} error={error}/>;
}
