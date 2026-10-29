"use client";

import Link from "next/link";
import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import { DashboardIcon } from "@/components/dashboard/dashboard-icon";
import { MedicalPhoto } from "@/components/dashboard/medical-photo";
import { translated, useDashboardUI } from "@/components/dashboard/dashboard-ui";
import { medicalImages } from "@/lib/cases/medical-images";

const specialties = [
  {value:"", en:"All cases", ar:"كل الحالات", briefEn:"Browse all available cases", briefAr:"استكشف الحالات المتاحة", image:medicalImages.all, fallback:"/cases/all-cases.svg", enabled:true, isAll:true, alt:"Clinician consulting a patient"},
  {value:"Pediatrics", en:"Pediatrics", ar:"طب الأطفال", briefEn:"Clinical training for young patients", briefAr:"تدريب سريري لطب الأطفال", image:medicalImages.pediatrics, fallback:"/cases/pediatrics.svg", enabled:true, isAll:false, alt:"Pediatric doctor speaking with a parent and child"},
  {value:"Internal Medicine", en:"Internal Medicine", ar:"الباطنة", briefEn:"Coming soon", briefAr:"قريبًا", image:medicalImages.internal, fallback:"/cases/internal.svg", enabled:false, isAll:false, alt:"Physician consulting an adult patient"},
  {value:"Surgery", en:"Surgery", ar:"الجراحة", briefEn:"Coming soon", briefAr:"قريبًا", image:medicalImages.surgery, fallback:"/cases/surgery.svg", enabled:false, isAll:false, alt:"Surgical team in an operating theatre"},
  {value:"Cardiology", en:"Cardiology", ar:"القلب", briefEn:"Coming soon", briefAr:"قريبًا", image:medicalImages.cardiology, fallback:"/cases/internal.svg", enabled:false, isAll:false, alt:"ECG cardiac monitoring display"},
  {value:"Neurology", en:"Neurology", ar:"الأعصاب", briefEn:"Coming soon", briefAr:"قريبًا", image:medicalImages.neurology, fallback:"/cases/all-cases.svg", enabled:false, isAll:false, alt:"Doctors examining a brain MRI"},
] as const;

function SpecialtyContent() {
  const { locale } = useDashboardUI();
  const params = useSearchParams();
  const [notice, setNotice] = useState<string | null>(null);
  const mode = params.get("mode") === "test" ? "test" : params.get("mode") === "training" ? "training" : "";
  return <div className="ydash-subpage ydash-modern-specialties">
    <header className="ydash-compact-heading"><div><span className="ydash-kicker">EXPLORE / SPECIALTIES</span><h1>{translated(locale,"اختار التخصص", "Choose a specialty")}</h1><p>{translated(locale,"اختار تخصص علشان تستكشف الحالات المتاحة.","Choose a specialty and discover available clinical cases.")}</p></div>{mode && <span className="ydash-mode-tag">{mode === "test" ? "Test" : "Training"}</span>}</header>
    <div className="ydash-specialties-tiles">{specialties.map((item,index) => {
      const q = new URLSearchParams();
      if (item.value) q.set("specialty", item.value);
      if (mode) q.set("mode", mode);
      const content = <>
        <div className="ydash-tile-image"><MedicalPhoto src={item.image} fallback={item.fallback} alt={item.alt} priority={index<2}/><div className="ydash-tile-gradient"/></div>
        <div className="ydash-tile-content"><span className="ydash-small-label">{item.enabled ? "AVAILABLE" : "COMING SOON"}</span><h2>{translated(locale,item.ar,item.en)}</h2><p>{translated(locale,item.briefAr,item.briefEn)}</p></div>
        <span className={item.enabled ? "ydash-tile-arrow" : "ydash-tile-lock"}><DashboardIcon name={item.enabled ? "arrow" : "lock"} size={19}/></span>
      </>;
      return item.enabled
        ? <Link key={item.en} href={`/dashboard/cases${q.size ? "?"+q.toString() : ""}`} className={`ydash-specialty-tile ydash-glass is-available${item.isAll ? " is-all-cases" : ""}`} style={{animationDelay:`${index*60}ms`}}>{content}</Link>
        : <button type="button" key={item.en} className="ydash-specialty-tile ydash-glass is-locked" style={{animationDelay:`${index*60}ms`}} onClick={() => setNotice(translated(locale,`تخصص ${item.ar} لسه مش متاح. هيتفتح في تحديث جاي.`,`${item.en} is coming in a future update.`))} aria-label={translated(locale,`${item.ar} — قريبًا`,`${item.en} — coming soon`)}>{content}</button>;
    })}</div>
    {notice && <div className="ydash-locked-toast ydash-glass" role="status"><DashboardIcon name="lock" size={18}/><span>{notice}</span><button type="button" onClick={() => setNotice(null)} aria-label={translated(locale,"إغلاق", "Dismiss")}><DashboardIcon name="close" size={17}/></button></div>}
  </div>;
}
export default function SpecialtiesPage() {
  return <Suspense fallback={<div className="ydash-loading ydash-glass">Loading specialties…</div>}><SpecialtyContent/></Suspense>;
}
