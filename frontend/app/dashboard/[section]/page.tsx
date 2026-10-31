"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { DashboardIcon, type IconName } from "@/components/dashboard/dashboard-icon";
import { DashboardLogout } from "@/components/dashboard/dashboard-shell";
import { SessionHistory } from "@/components/dashboard/session-history";
import { useDashboardUI, translated } from "@/components/dashboard/dashboard-ui";

const sections: Record<string, {ar:string; en:string; icon:IconName; arDesc:string; enDesc:string}> = {
  history: {ar:"سجل الجلسات", en:"Session history", icon:"history", arDesc:"هنا هتظهر جلساتك السابقة والتقارير بعد تفعيل محرك الجلسات.",enDesc:"Your completed sessions and reports will appear when session tracking is connected."},
  analytics: {ar:"تحليلات الأداء", en:"Performance analytics", icon:"chart", arDesc:"هنعرض درجاتك ونقاط القوة والضعف من بيانات التقييم الحقيقية.", enDesc:"Scores, strengths and improvement areas will use real evaluation data."},
  leaderboard: {ar:"لوحة المتصدرين", en:"Leaderboard", icon:"trophy", arDesc:"ترتيب الطلاب وXP هيتعرضوا من النظام الفعلي لما نقاط الخبرة تتنفذ.", enDesc:"Student ranks and XP will come from the real gamification service."},
  challenges: {ar:"التحديات", en:"Challenges", icon:"zap", arDesc:"التحديات المقترحة والمكافآت قيد التطوير.", enDesc:"Suggested challenges and rewards are under development."},
  profile: {ar:"ملفك الشخصي", en:"Your profile", icon:"user", arDesc:"بيانات حسابك الحالية. تعديل الصورة والمعلومات الشخصية هيتضاف لما Profile Editor يجهز.", enDesc:"Your current account information. Avatar and profile editing will follow with the profile editor."},
  settings: {ar:"الإعدادات", en:"Settings", icon:"settings", arDesc:"تقدر تغيّر اللغة والمظهر من الشريط العلوي. باقي إعدادات الحساب لسه بتتجهز.", enDesc:"Language and theme are already available in the top bar. Other account settings are being prepared."},
};
export default function DashboardSectionPage() {
  const {section} = useParams<{section:string}>();
  const {locale,name,email} = useDashboardUI();
  const current = sections[section];
  if (!current) return <div className="ydash-subpage"><div className="ydash-glass ydash-placeholder"><h1>{translated(locale,"الصفحة مش موجودة", "Page not found")}</h1><Link href="/dashboard" className="ydash-outline-action">{translated(locale,"العودة للرئيسية", "Back to home")}</Link></div></div>;
  return <div className="ydash-subpage"><div className="ydash-subpage-hero ydash-glass"><span className="ydash-kicker">YA-DOK / STUDENT SPACE</span><h1><DashboardIcon name={current.icon} size={32}/> {translated(locale,current.ar,current.en)}</h1><p>{translated(locale,current.arDesc,current.enDesc)}</p></div>
    {section === "history" ? <SessionHistory /> : section === "profile" ? <div className="ydash-glass ydash-profile-panel"><div className="ydash-profile-avatar">{Array.from(name)[0] || "Y"}</div><div><span className="ydash-small-label">ACCOUNT</span><h2>{name}</h2><p dir="ltr">{email}</p></div><DashboardLogout/></div> : <div className="ydash-glass ydash-placeholder"><div className="ydash-placeholder-symbol"><DashboardIcon name={current.icon} size={46}/></div><h2>{translated(locale,"القسم ده لسه تحت التطوير", "This section is coming soon")}</h2><p>{translated(locale,"مش هنعرض بيانات تجريبية وكأنها نتائج فعلية. هيرتبط بالـ Backend الخاصة بيه لما تتنفذ.", "No made-up data. This page will use its real backend when the feature is implemented.")}</p><Link href="/dashboard" className="ydash-outline-action">{translated(locale,"ارجع للرئيسية", "Back to dashboard")} <DashboardIcon name="arrow" size={16}/></Link></div>}
  </div>;
}
