"use client";

import Link from "next/link";
import { useEffect, useRef, useState, type ReactNode, type CSSProperties } from "react";
import { DashboardIcon } from "@/components/dashboard/dashboard-icon";
import { useDashboardUI, translated } from "@/components/dashboard/dashboard-ui";

const indicators = [
  { icon: "book", ar: "الحالات المكتملة", en: "Completed cases", footAr: "بعد أول جلسة", footEn: "After your first session" },
  { icon: "target", ar: "متوسط التقييم", en: "Average score", footAr: "بعد التقييم", footEn: "After evaluation" },
  { icon: "clock", ar: "وقت التدريب", en: "Practice time", footAr: "بعد تتبع الجلسات", footEn: "After session tracking" },
] as const;

function ProgressRing({value, index}:{value:number|null; index:number}) {
  const safeValue = value === null ? 0 : Math.max(0, Math.min(100, value));
  return <div className="ydash-progress-ring" role="img" aria-label={value === null ? "No progress data yet" : `${safeValue}%`} style={{"--ring-target":safeValue} as CSSProperties}>
    <svg viewBox="0 0 112 112" aria-hidden="true"><circle className="ydash-ring-track" cx="56" cy="56" r="43"/><circle className="ydash-ring-fill" cx="56" cy="56" r="43" pathLength="100"/></svg>
    <span className="ydash-ring-value">{value===null?"—":`${safeValue}%`}</span><span className="ydash-ring-index">0{index+1}</span>
  </div>;
}
function useGreeting() {
  const [greeting, setGreeting] = useState<"welcome" | "morning" | "afternoon" | "evening">("welcome");
  useEffect(() => {
    const frame = requestAnimationFrame(() => {
      const hour = new Date().getHours();
      setGreeting(hour >= 5 && hour < 12 ? "morning" : hour >= 12 && hour < 17 ? "afternoon" : "evening");
    });
    return () => cancelAnimationFrame(frame);
  }, []);
  return greeting;
}
function FadeSection({children, delay=0, className=""}: {children: ReactNode; delay?:number; className?: string}) {
  const ref = useRef<HTMLElement>(null);
  useEffect(() => {
    const node = ref.current; if (!node) return;
    if (!("IntersectionObserver" in window)) { node.classList.add("ydash-visible"); return; }
    const observer = new IntersectionObserver(entries => {
      for (const entry of entries) entry.target.classList.toggle("ydash-visible", entry.isIntersecting);
    }, {threshold: .08});
    observer.observe(node);
    return () => observer.disconnect();
  }, []);
  return <section ref={ref} className={`ydash-reveal ${className}`} style={{transitionDelay:`${delay}ms`}}>{children}</section>;
}

export default function DashboardPage() {
  const { locale, name, openSession } = useDashboardUI();
  const firstName = name.trim().split(/\s+/)[0] || "Doctor";
  const greeting = useGreeting();
  const salutation = {
    welcome: ["أهلاً بيك", "Welcome back"], morning: ["صباح الخير", "Good morning"],
    afternoon: ["مساء الخير", "Good afternoon"], evening: ["مساء الخير", "Good evening"],
  }[greeting][locale === "ar" ? 0 : 1];
  return <div className="ydash-home">
    <FadeSection className="ydash-intro" delay={25}>
      <div><div className="ydash-eyebrow"><span className="ydash-pulse-dot"/> WELCOME BACK · YOUR CLINICAL JOURNEY</div><h1>{salutation}، <em>{firstName}</em><span className="ydash-heading-spark">✦</span></h1><p>{translated(locale,"كل حالة بتقرّبك خطوة من التفكير الإكلينيكي بثقة.", "A little more clinical confidence with every case you explore.")}</p></div>
      <div className="ydash-pills"><span className="ydash-pill"><DashboardIcon name="trophy" size={17}/>{translated(locale,"الترتيب", "Rank")} <strong>—</strong></span><span className="ydash-pill"><DashboardIcon name="zap" size={17}/>{translated(locale,"إجمالي XP", "Total XP")} <strong>—</strong></span></div>
    </FadeSection>

    <FadeSection className="ydash-hero ydash-glass" delay={75}>
      <div className="ydash-hero-content"><span className="ydash-kicker">AI-POWERED CLINICAL SIMULATION</span><h2>{translated(locale,"المريض القادم مستني قرارك.", "Your next patient awaits your decision.")}</h2><p>{translated(locale,"ابدأ رحلتك في التدريب السريري. اختار وضع التدريب، ثم التخصص والحالة المناسبة ليك.", "Step into clinical practice. Pick a mode, choose a specialty and explore your next case.")}</p>
        <div className="ydash-hero-actions"><button type="button" className="ydash-primary-action" onClick={openSession}><DashboardIcon name="play" size={20}/>{translated(locale,"ابدأ جلسة جديدة", "Start new session")}<DashboardIcon name="arrow" size={17}/></button><Link className="ydash-secondary-action" href="/dashboard/specialties">{translated(locale,"استكشف الحالات", "Explore cases")}<DashboardIcon name="chevron" size={17}/></Link></div>
      </div><div aria-hidden="true" className="ydash-hero-art"><div className="ydash-hero-ring ring-a"/><div className="ydash-hero-ring ring-b"/><div className="ydash-hero-center"><DashboardIcon name="stethoscope" size={56}/></div><div className="ydash-hero-orbit-dot"/></div>
    </FadeSection>

    <FadeSection className="ydash-section" delay={100}><div className="ydash-section-heading"><div><span className="ydash-small-label">01 / OVERVIEW</span><h2>{translated(locale,"نظرة على رحلتك", "Your progress at a glance")}</h2><p>{translated(locale,"مؤشراتك الحقيقية هتظهر هنا مع بداية الجلسات والتقييم.", "Your real metrics will appear once sessions and evaluations are available.")}</p></div><Link href="/dashboard/analytics" className="ydash-text-link">{translated(locale,"تحليلات أكتر", "More analytics")} <DashboardIcon name="arrow" size={16}/></Link></div>
      <div className="ydash-stat-grid">{indicators.map((item, index) => <article className="ydash-stat-card ydash-glass" key={item.en} style={{animationDelay:`${index*110}ms`}}><div className="ydash-stat-copy"><span className="ydash-stat-icon"><DashboardIcon name={item.icon} size={20}/></span><h3>{translated(locale,item.ar,item.en)}</h3><p>{translated(locale,item.footAr,item.footEn)}</p></div><ProgressRing value={null} index={index}/></article>)}</div>
    </FadeSection>

    <div className="ydash-bottom-grid">
      <FadeSection className="ydash-challenge ydash-glass" delay={130}><div className="ydash-card-head"><span className="ydash-small-label">02 / YOUR NEXT MOVE</span><span className="ydash-mini-emblem"><DashboardIcon name="zap" size={20}/></span></div><h2>{translated(locale,"التحدي المقترح", "Suggested challenge")}</h2><div className="ydash-challenge-visual" aria-hidden="true"><DashboardIcon name="target" size={47}/><span>✦</span></div><h3>{translated(locale,"تحديك الجاي بيتجهّز", "Your next challenge is on its way")}</h3><p>{translated(locale,"لما نظام التحديات يجهز، هتلاقي تحديات مناسبة لمستواك وجوايزها هنا.", "Personalized challenges and their rewards will appear here when the challenge system launches.")}</p><div className="ydash-challenge-footer"><span><DashboardIcon name="zap" size={16}/> {translated(locale,"المكافأة: لسه متحددتش", "Reward: not defined yet")}</span><Link href="/dashboard/challenges" className="ydash-text-link">{translated(locale,"التحديات", "Challenges")} <DashboardIcon name="chevron" size={15}/></Link></div></FadeSection>
      <FadeSection className="ydash-leaderboard ydash-glass" delay={180}><div className="ydash-card-head"><span className="ydash-small-label">03 / THE COMMUNITY</span><span className="ydash-mini-emblem"><DashboardIcon name="trophy" size={20}/></span></div><h2>{translated(locale,"لوحة المتصدرين", "Leaderboard")}</h2><p className="ydash-muted">{translated(locale,"ترتيبك هيتحدّث من الداتا الفعلية لما نظام XP يجهز.", "Rankings will update from real XP data once the points system is implemented.")}</p><div className="ydash-my-rank"><div className="ydash-rank-avatar">{Array.from(name)[0] || "Y"}</div><div><strong>{firstName}</strong><small>{translated(locale,"ترتيبك الحالي", "Your rank")}</small></div><span>—</span></div><div className="ydash-ranking-empty"><DashboardIcon name="trophy" size={31}/><strong>{translated(locale,"مفيش ترتيب متاح حاليًا", "No rankings yet")}</strong><span>{translated(locale,"هنا هيظهر جزء من الترتيب بشكل مباشر بعد تفعيل الـ Leaderboard.", "Live standings will appear here when the leaderboard service is connected.")}</span></div><Link href="/dashboard/leaderboard" className="ydash-outline-action">{translated(locale,"عرض القائمة الكاملة", "View full leaderboard")} <DashboardIcon name="arrow" size={16}/></Link></FadeSection>
    </div>
  </div>;
}
