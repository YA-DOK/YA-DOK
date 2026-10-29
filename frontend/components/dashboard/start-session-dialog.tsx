"use client";

import Link from "next/link";
import { useEffect, useRef } from "react";
import { DashboardIcon } from "./dashboard-icon";
import { useDashboardUI, translated } from "./dashboard-ui";

export function StartSessionDialog() {
  const { locale, modalOpen, closeSession } = useDashboardUI();
  const dialogRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!modalOpen) return;
    const previousFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    dialogRef.current?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") closeSession();
      if (event.key !== "Tab" || !dialogRef.current) return;
      const controls = Array.from(dialogRef.current.querySelectorAll<HTMLElement>('a[href],button:not([disabled])'));
      if (!controls.length) return;
      const first = controls[0], last = controls[controls.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    };
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => { document.removeEventListener("keydown", onKey); document.body.style.overflow = ""; previousFocus?.focus(); };
  }, [modalOpen, closeSession]);

  if (!modalOpen) return null;
  return <div className="ydash-modal-backdrop" onMouseDown={event => { if (event.target === event.currentTarget) closeSession(); }}>
    <div className="ydash-modal ydash-glass" ref={dialogRef} tabIndex={-1} role="dialog" aria-modal="true" aria-labelledby="ydash-modal-title" dir={locale === "ar" ? "rtl" : "ltr"}>
      <div className="ydash-modal-top"><span className="ydash-kicker">YA-DOK / NEW SESSION</span><button className="ydash-icon-button" aria-label={translated(locale, "إغلاق", "Close")} onClick={closeSession}><DashboardIcon name="close"/></button></div>
      <div className="ydash-modal-orb"><DashboardIcon name="stethoscope" size={28}/></div>
      <h2 id="ydash-modal-title">{translated(locale, "اختار طريقة تدريبك", "Choose your session mode")}</h2>
      <p className="ydash-muted">{translated(locale, "حدّد نوع التجربة، وبعدها اختار التخصص والحالة.", "Choose your mode, then pick a specialty and case.")}</p>
      <div className="ydash-mode-grid">
        <Link className="ydash-mode-card" href="/dashboard/specialties?mode=training" onClick={closeSession}><DashboardIcon name="book" size={27}/><strong>{translated(locale, "وضع التدريب", "Training mode")}</strong><span>{translated(locale, "تعلّم وتدرّب. التلميحات تتفعّل مع محرك المحاكاة.", "Guided practice. Hints will activate with the simulation engine.")}</span><span className="ydash-mode-arrow"><DashboardIcon name="arrow"/></span></Link>
        <Link className="ydash-mode-card" href="/dashboard/specialties?mode=test" onClick={closeSession}><DashboardIcon name="target" size={27}/><strong>{translated(locale, "وضع الاختبار", "Test mode")}</strong><span>{translated(locale, "اختبر قراراتك. قواعد التقييم تتفعّل مع المحاكاة.", "Assess your decisions. Scoring rules activate with the simulation engine.")}</span><span className="ydash-mode-arrow"><DashboardIcon name="arrow"/></span></Link>
      </div>
      <p className="ydash-modal-footnote">{translated(locale, "إنشاء الجلسات الفعلية لسه تحت التطوير. تقدر تتصفح التخصصات والحالات المتاحة حاليًا.", "Session creation is still being built. You can explore available specialties and cases now.")}</p>
    </div>
  </div>;
}
