"use client";

import Link from "next/link";
import type { StudentCaseSummary } from "@/lib/cases/api";
import { DashboardIcon } from "./dashboard-icon";
import { MedicalPhoto } from "./medical-photo";
import { artworkFor, fallbackFor } from "./glass-cases-browser";
import { useDashboardUI, translated } from "./dashboard-ui";

export function GlassCasePreview({item,error}:{item:StudentCaseSummary|null;error:boolean}){
 const {locale}=useDashboardUI();
 if(error||!item)return <div className="ydash-case-empty ydash-glass"><DashboardIcon name="activity" size={35}/><h1>{translated(locale,"تعذّر تحميل الحالة", "Could not load this case")}</h1><p>{translated(locale,"تأكد إن الـ Backend شغالة وحاول تاني.", "Check your backend connection and try again.")}</p><Link className="ydash-outline-action" href="/dashboard/cases">{translated(locale,"مكتبة الحالات", "Case library")}</Link></div>;
 return <div className="ydash-preview"><Link href="/dashboard/cases" className="ydash-text-link"><DashboardIcon name="arrow" size={17}/>{translated(locale,"العودة لمكتبة الحالات", "Back to case library")}</Link>
 <section className="ydash-preview-card ydash-glass"><span className="ydash-kicker">CLINICAL CASE / PREVIEW</span><div className="ydash-preview-badges"><span>{item.specialty||translated(locale,"غير محدد", "Unspecified")}</span><span>{item.difficulty||"—"}</span></div><h1>{item.title||item.case_id}</h1>
    {item.subtitle&&<p>{item.subtitle}</p>}<div
      className="ydash-preview-art ydash-preview-photo"

    ><MedicalPhoto src={artworkFor(item)} fallback={fallbackFor(item)} alt="Representative editorial medical scene, not the simulated patient"/></div><p>{item.short_brief||translated(locale,"لا يوجد وصف تمهيدي متاح.", "No introduction available.")}</p><div className="ydash-preview-details"><span><DashboardIcon name="compass" size={18}/>{translated(locale,"المكان", "Setting")}: {item.setting||"—"}</span><span><DashboardIcon name="clock" size={18}/>{translated(locale,"المدة", "Duration")}: {item.estimated_duration_minutes?`${item.estimated_duration_minutes} min`:"—"}</span></div></section>
 <section id="start-simulation" className="ydash-preview-cta ydash-glass">
      <div>
        <h2>Choose Simulation Mode</h2>
        <p>"Start a simulation from this published case."</p>
      </div>
      <div style={{display:"flex",gap:12,flexWrap:"wrap"}}>
      <Link className="ydash-outline-action"
        href={`/simulation/preview?case=${encodeURIComponent(item.case_id)}&mode=training&new=1`}>
        Training Mode
      </Link>
      <Link className="ydash-outline-action"
        href={`/simulation/preview?case=${encodeURIComponent(item.case_id)}&mode=test&new=1`}>
        Test Mode
      </Link>
    </div>
    </section>
 </div>;
}
