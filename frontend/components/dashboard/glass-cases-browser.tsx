"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import type { StudentCasePage, StudentCaseSummary } from "@/lib/cases/api";
import { DashboardIcon } from "./dashboard-icon";
import { MedicalPhoto } from "./medical-photo";
import { medicalImages } from "@/lib/cases/medical-images";
import { useDashboardUI, translated } from "./dashboard-ui";

type Props = { data:StudentCasePage|null; error:boolean; specialty:string; difficulty:string; page:number; mode:string };
const ranks:Record<string,number>={beginner:0,intermediate:1,advanced:2};
export function artworkFor(item:StudentCaseSummary): string {
  if (item.case_id === "SYN-PED-002") return medicalImages.urinary;
  if (item.case_id === "SYN-SURG-003") return medicalImages.abdominal;
  if (item.case_id === "PED-RT-0002") return medicalImages.respiratory;
  if (item.specialty?.toLowerCase().includes("surg")) return medicalImages.surgery;
  return medicalImages.pediatrics;
}
export function fallbackFor(item:StudentCaseSummary): string {
  if (item.case_id === "SYN-PED-002") return "/cases/uti.svg";
  if (item.case_id === "SYN-SURG-003") return "/cases/abdominal.svg";
  if (item.case_id === "PED-RT-0002") return "/cases/respiratory.svg";
  if (item.specialty?.toLowerCase().includes("surg")) return "/cases/surgery.svg";
  return "/cases/pediatrics.svg";
}
function urlWithQuery(page:number,specialty:string,difficulty:string,mode:string){const q=new URLSearchParams();if(specialty)q.set("specialty",specialty);if(difficulty)q.set("difficulty",difficulty);if(mode)q.set("mode",mode);if(page>1)q.set("page",String(page));return `/dashboard/cases${q.size?"?"+q.toString():""}`;}
export function GlassCasesBrowser({data,error,specialty,difficulty,page,mode}:Props){
 const {locale}=useDashboardUI();const router=useRouter();const [sort,setSort]=useState("default");const [search,setSearch]=useState("");
 const items=useMemo(()=>{
  const needle=search.trim().toLocaleLowerCase();
  const rows=[...(data?.items||[])].filter(c=>(!specialty||c.specialty?.toLowerCase()===specialty.toLowerCase())&&(!difficulty||c.difficulty?.toLowerCase()===difficulty.toLowerCase())&&`${c.title||""} ${c.short_brief||""} ${c.specialty||""} ${c.case_id}`.toLocaleLowerCase().includes(needle));
  if(sort==="name")rows.sort((a,b)=>(a.title||"").localeCompare(b.title||""));
  if(sort==="duration")rows.sort((a,b)=>(a.estimated_duration_minutes??999)-(b.estimated_duration_minutes??999));
  if(sort==="difficulty")rows.sort((a,b)=>(ranks[a.difficulty?.toLowerCase()||""]??99)-(ranks[b.difficulty?.toLowerCase()||""]??99));
  return rows;
 },[data,search,sort,specialty,difficulty]);
 function randomPreview(){if(items.length){const item=items[Math.floor(Math.random()*items.length)];router.push(`/dashboard/cases/${encodeURIComponent(item.case_id)}`);}}

 return <div className="ydash-case-library">
   <header className="ydash-compact-heading ydash-cases-top"><div><span className="ydash-kicker">CASE LIBRARY / YA-DOK</span><h1>{translated(locale,"اختار حالتك القادمة", "Explore clinical cases")}</h1><p>{translated(locale,"تصفّح الحالات بالصور، وابحث أو رتّب حسب اللي يناسبك.","Find a case that fits your training goals. Search, filter and sort.")}</p></div><Link href="/dashboard/specialties" className="ydash-outline-action">{translated(locale,"التخصصات", "Specialties")}</Link></header>

   <div className="ydash-case-toolbar ydash-glass">
    <div className="ydash-case-search"><DashboardIcon name="compass" size={18}/><input value={search} onChange={e=>setSearch(e.target.value)} aria-label={translated(locale,"بحث في الحالات المحملة", "Search loaded cases")} placeholder={translated(locale,"ابحث في الحالات…", "Search loaded cases…")}/></div>
    <form className="ydash-case-inline-filters" action="/dashboard/cases" method="get">{mode&&<input type="hidden" name="mode" value={mode}/>}<select name="specialty" defaultValue={specialty} aria-label="Specialty"><option value="">{translated(locale,"كل التخصصات", "All specialties")}</option><option value="Pediatrics">{translated(locale,"طب الأطفال", "Pediatrics")}</option><option value="Surgery">{translated(locale,"الجراحة", "Surgery")}</option></select><select name="difficulty" defaultValue={difficulty} aria-label="Difficulty"><option value="">{translated(locale,"كل المستويات", "All levels")}</option><option value="beginner">{translated(locale,"مبتدئ", "Beginner")}</option><option value="intermediate">{translated(locale,"متوسط", "Intermediate")}</option><option value="advanced">{translated(locale,"متقدم", "Advanced")}</option></select><button type="submit" className="ydash-filter-apply">{translated(locale,"فلتر", "Filter")}</button></form>
    <select value={sort} onChange={e=>setSort(e.target.value)} aria-label="Sort cases"><option value="default">{translated(locale,"الترتيب الافتراضي", "Default sort")}</option><option value="name">{translated(locale,"الاسم", "Name")}</option><option value="difficulty">{translated(locale,"الصعوبة", "Difficulty")}</option><option value="duration">{translated(locale,"المدة", "Duration")}</option></select>
    <button type="button" className="ydash-random-button" disabled={!items.length} onClick={randomPreview}><DashboardIcon name="spark" size={17}/>{translated(locale,"حالة عشوائية", "Surprise me")}</button>
   </div>
   {error&&!data ? <div role="alert" className="ydash-case-empty ydash-glass"><DashboardIcon name="activity" size={30}/><h2>{translated(locale,"تعذّر تحميل الحالات", "Cases unavailable")}</h2><p>{translated(locale,"تأكد إن FastAPI وSupabase شغالين.","Check FastAPI and Supabase connections.")}</p></div> : <>
    <div className="ydash-case-count"><span>{items.length} {translated(locale,"حالات ظاهرة في الصفحة الحالية", "cases shown on this page")}</span>{mode&&<span className="ydash-mode-tag">{mode==="test"?"Test":"Training"}</span>}</div>
    {items.length ? <div className="ydash-cases-grid">{items.map((item,index)=><article key={`${item.case_id}:${item.version_number}`} className="ydash-case-card ydash-glass" style={{animationDelay:`${Math.min(index,9)*70}ms`}}>
      <div className="ydash-case-card-image"><MedicalPhoto src={artworkFor(item)} fallback={fallbackFor(item)} alt="Editorial medical image illustrating the specialty; not the case patient"/><div className="ydash-case-image-overlay"/><span className="ydash-case-image-status">PUBLISHED</span></div>
      <div className="ydash-case-card-body"><div className="ydash-case-card-top"><span>{item.specialty||"Restricted"}</span><span>{item.difficulty||"—"}</span></div><h2>{item.title||item.case_id}</h2><p>{item.short_brief||translated(locale,"افتح المعاينة للتفاصيل العامة.","Open preview for general details.")}</p><div className="ydash-case-card-footer"><small><DashboardIcon name="clock" size={15}/>{item.estimated_duration_minutes?`${item.estimated_duration_minutes} min`:"—"}</small><div className="ydash-card-actions"><Link href={`/dashboard/cases/${encodeURIComponent(item.case_id)}`} className="ydash-outline-action">{translated(locale,"التفاصيل", "Details")}</Link>
<Link
  href={`/simulation/preview?case=${encodeURIComponent(item.case_id)}&mode=${mode === "test" ? "test" : "training"}&new=1`}
  className="ydash-outline-action"
>
  Start <DashboardIcon name="play" size={16}/>
</Link>
</div></div></div>
     </article>)}</div> : <div className="ydash-case-empty ydash-glass"><DashboardIcon name="book" size={35}/><h2>{translated(locale,"مفيش حالات مطابقة حاليًا", "No matching cases")}</h2><p>No published cases match your filters.</p></div>}
    <nav className="ydash-case-pagination">{page>1&&<Link href={urlWithQuery(page-1,specialty,difficulty,mode)}>{translated(locale,"السابق", "Previous")}</Link>}<span>{translated(locale,"صفحة", "Page")} {page}</span>{data?.has_more&&<Link href={urlWithQuery(page+1,specialty,difficulty,mode)}>{translated(locale,"التالي", "Next")}</Link>}</nav>
   </>}
 </div>;
}
