"use client";

import dynamic from "next/dynamic";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState, useSyncExternalStore, type CSSProperties, type ReactNode } from "react";
import { LogoutButton } from "@/components/auth/logout-button";
import { createClient } from "@/lib/supabase/client";
import { DashboardIcon, type IconName } from "./dashboard-icon";
import { DashboardUIProvider, useDashboardUI, translated } from "./dashboard-ui";
import { StartSessionDialog } from "./start-session-dialog";
import "./dashboard-glass.css";

const ClinicalWorld = dynamic(() => import("@/components/landing-lab/ClinicalWorld"), { ssr: false });

type NavItem = { id: string; icon: IconName; href?: string; ar: string; en: string; action?: "session" };
const navItems: NavItem[] = [
  { id: "home", icon: "home", href: "/dashboard", ar: "الرئيسية", en: "Home" },
  { id: "session", icon: "play", action: "session", ar: "ابدأ جلسة", en: "Start session" },
  { id: "specialties", icon: "compass", href: "/dashboard/specialties", ar: "استكشف الحالات", en: "Explore cases" },
  { id: "history", icon: "history", href: "/dashboard/history", ar: "سجل الجلسات", en: "History" },
  { id: "analytics", icon: "chart", href: "/dashboard/analytics", ar: "التحليلات", en: "Analytics" },
  { id: "leaderboard", icon: "trophy", href: "/dashboard/leaderboard", ar: "المتصدرون", en: "Leaderboard" },
  { id: "challenges", icon: "zap", href: "/dashboard/challenges", ar: "التحديات", en: "Challenges" },
  { id: "profile", icon: "user", href: "/dashboard/profile", ar: "الملف الشخصي", en: "Profile" },
  { id: "settings", icon: "settings", href: "/dashboard/settings", ar: "الإعدادات", en: "Settings" },
];

// YA-DOK F02: server-verified admin navigation. The API, NOT the UI, enforces access.
const adminCaseNav: NavItem = {
  id: "admin-cases", icon: "shield", href: "/dashboard/admin/cases",
  ar: "إدارة الحالات", en: "Case Management",
};
const adminApiBase = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

function subscribeDesktop(callback: () => void) {
  const desktop = window.matchMedia("(min-width: 900px)");
  const motion = window.matchMedia("(prefers-reduced-motion: no-preference)");
  desktop.addEventListener("change", callback);
  motion.addEventListener("change", callback);
  return () => { desktop.removeEventListener("change", callback); motion.removeEventListener("change", callback); };
}
function hasDesktopMotion() { return window.matchMedia("(min-width: 900px)").matches && window.matchMedia("(prefers-reduced-motion: no-preference)").matches; }
function noSceneOnServer() { return false; }

export function DashboardShell({ children, name, email, avatarUrl, unreadNotifications = 0 }: {children: ReactNode; name: string; email: string; avatarUrl?: string | null; unreadNotifications?: number}) {
  return <DashboardUIProvider name={name} email={email}><DashboardFrame name={name} avatarUrl={avatarUrl} unreadNotifications={unreadNotifications}>{children}</DashboardFrame></DashboardUIProvider>;
}

function DashboardFrame({ children, name, avatarUrl, unreadNotifications }: { children: ReactNode; name: string; avatarUrl?: string | null; unreadNotifications: number }) {
  const { locale, theme, setLocale, setTheme, openSession } = useDashboardUI();
  const pathname = usePathname();
  const [mobileNav, setMobileNav] = useState(false);
  const [canManageCases, setCanManageCases] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    async function verifyCaseAdmin() {
      try {
        const { data: { session } } = await createClient().auth.getSession();
        if (!session?.access_token) return;
        const response = await fetch(new URL("/api/v1/admin/cases?limit=1", adminApiBase), {
          cache: "no-store",
          headers: { Authorization: `Bearer ${session.access_token}` },
          signal: controller.signal,
        });
        if (!controller.signal.aborted) setCanManageCases(response.ok);
      } catch {
        if (!controller.signal.aborted) setCanManageCases(false);
      }
    }
    void verifyCaseAdmin();
    return () => controller.abort();
  }, []);
  // Keep Case Management beside Explore Cases only for server-authorized admins.
  const visibleNavItems = canManageCases
    ? [...navItems.slice(0, 3), adminCaseNav, ...navItems.slice(3)]
    : navItems;
  const [floatingPanel, setFloatingPanel] = useState<"notifications" | "assistant" | null>(null);
  const floatingCloseRef = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    if (!floatingPanel) return;
    const onKey = (event: KeyboardEvent) => { if (event.key === "Escape") setFloatingPanel(null); };
    window.addEventListener("keydown", onKey);
    const focusFrame = window.requestAnimationFrame(() => floatingCloseRef.current?.focus());
    return () => { window.removeEventListener("keydown", onKey); window.cancelAnimationFrame(focusFrame); };
  }, [floatingPanel]);
  const sceneEnabled = useSyncExternalStore(subscribeDesktop, hasDesktopMotion, noSceneOnServer);
  const activeRailIndex = pathname.startsWith("/dashboard/cases") ? 2 : visibleNavItems.findIndex(item => item.href && (item.href === "/dashboard" ? pathname === "/dashboard" : pathname === item.href || pathname.startsWith(item.href + "/")));
  const userInitial = Array.from(name.trim())[0] || "Y";
  const validAvatar = typeof avatarUrl === "string" && (avatarUrl.startsWith("https://") || avatarUrl.startsWith("/"));
  const nav = (item: NavItem) => {
    const active = item.id === "specialties" && pathname.startsWith("/dashboard/cases") ? true : (item.href === "/dashboard" ? pathname === "/dashboard" : Boolean(item.href && (pathname === item.href || pathname.startsWith(item.href + "/"))));
    const label = translated(locale, item.ar, item.en);
    const contents = <><DashboardIcon name={item.icon} size={21}/><span className="ydash-nav-tooltip" role="tooltip">{label}</span></>;
    const common = `ydash-rail-item${active ? " is-active" : ""}`;
    if (item.action === "session") return <button type="button" aria-label={label} title={label} className={common} onClick={() => { setMobileNav(false); openSession(); }} key={item.id}>{contents}</button>;
    return <Link key={item.id} href={item.href!} title={label} aria-label={label} aria-current={active ? "page" : undefined} className={common} onClick={() => setMobileNav(false)}>{contents}</Link>;
  };
  return <div className={`ydash ${theme === "dark" ? "ydash-dark" : "ydash-light"}`} dir={locale === "ar" ? "rtl" : "ltr"}>
    <div aria-hidden="true" className="ydash-atmosphere">
      {sceneEnabled && <div className="ydash-scene"><ClinicalWorld focus="doctor"/></div>}
      <div className="ydash-frost"/>
      <div className="ydash-ambient-light"/>
    </div>

    {mobileNav && <button className="ydash-mobile-scrim" aria-label={translated(locale,"إغلاق القائمة", "Close navigation")} onClick={() => setMobileNav(false)}/>}
    <aside className={`ydash-rail ydash-glass${mobileNav ? " ydash-rail-open" : ""}`} aria-label={translated(locale,"التنقل الرئيسي", "Main navigation")}>
      <div className="ydash-rail-top"><span className="ydash-rail-mark"><DashboardIcon name="stethoscope" size={22}/></span></div>
      <nav className="ydash-rail-nav" style={{ "--ydash-active-index": Math.max(0, activeRailIndex) } as CSSProperties}>{visibleNavItems.map(nav)}</nav>
      <div className="ydash-rail-bottom"><span className="ydash-rail-dot" title="YA-DOK"/><span className="ydash-rail-version">V1</span></div>
    </aside>

    <div className="ydash-workspace">
      <header className="ydash-topbar ydash-glass">
        <div className="ydash-brandline">
          <button type="button" aria-label={translated(locale,"فتح القائمة", "Open menu")} className="ydash-icon-button ydash-menu-trigger" onClick={() => setMobileNav(true)}><DashboardIcon name="menu"/></button>
          <Link href="/dashboard" className="ydash-brand" aria-label="YA-DOK home"><Image src="/brand/yadok-logo.png" alt="YA-DOK" width={100} height={45} priority className="ydash-logo"/></Link>
          <span className="ydash-brand-divider"/><span className="ydash-brand-caption">CLINICAL SPACE</span>
        </div>
        <div className="ydash-top-actions">
          <button type="button" className="ydash-language-switch" title={translated(locale, "تغيير اللغة", "Change language")} aria-label={translated(locale, "التبديل إلى الإنجليزية", "Switch to Arabic")} onClick={() => setLocale(locale === "ar" ? "en" : "ar")}> <DashboardIcon name="globe" size={17}/> {locale === "ar" ? "EN" : "عربي"}</button>
          <button type="button" className="ydash-icon-button" title={translated(locale,"تغيير المظهر", "Toggle theme")} aria-label={translated(locale,"تغيير المظهر", "Toggle theme")} onClick={() => setTheme(theme === "light" ? "dark" : "light")}>{theme === "light" ? <DashboardIcon name="moon"/> : <DashboardIcon name="sun"/>}</button>
          <button type="button" className="ydash-icon-button ydash-notify-button" aria-label={translated(locale, "الإشعارات", "Notifications")} title={translated(locale,"الإشعارات", "Notifications")} aria-expanded={floatingPanel === "notifications"} onClick={() => setFloatingPanel("notifications")}><DashboardIcon name="bell" size={19}/>{unreadNotifications>0&&<span className="ydash-notification-count">{unreadNotifications>99?"99+":unreadNotifications}</span>}</button>
          <Link href="/dashboard/profile" className="ydash-avatar-button" aria-label={translated(locale,"ملفي الشخصي", "My profile")} title={translated(locale,"ملفي الشخصي", "My profile")}>
            {validAvatar ? <Image unoptimized src={avatarUrl!} alt="" width={40} height={40} className="ydash-avatar-photo"/> : <span>{userInitial}</span>}
            <i className="ydash-avatar-status"/>
          </Link>
        </div>
      </header>
      <main className="ydash-main" id="main-content"><div key={pathname} className="ydash-page-enter">{children}</div></main>
      <footer className="ydash-footline">YA-DOK <span>·</span> {translated(locale,"منصّة تدريب سريري تعليمية", "Clinical learning experience")}</footer>
    </div>
    <button type="button" className="ydash-assistant-fab" aria-label={translated(locale,"افتح مساعد يا دُك", "Open YA-DOK assistant")} title={translated(locale,"المساعد الذكي", "AI assistant")} onClick={() => setFloatingPanel("assistant")}><DashboardIcon name="spark" size={24}/><span className="ydash-assistant-glow"/></button>
    {floatingPanel && <div className="ydash-float-backdrop" onMouseDown={(e) => {if(e.target === e.currentTarget) setFloatingPanel(null);}}>
      <section role="dialog" aria-modal="true" aria-label={floatingPanel === "notifications" ? translated(locale,"الإشعارات", "Notifications") : translated(locale,"مساعد يا دُك", "YA-DOK Assistant")} className="ydash-floating-window ydash-glass">
        <div className="ydash-float-head"><span className="ydash-floating-icon"><DashboardIcon name={floatingPanel === "notifications" ? "bell" : "spark"} size={21}/></span><div><h2>{floatingPanel === "notifications" ? translated(locale,"الإشعارات", "Notifications") : translated(locale,"مساعد يا دُك", "YA-DOK Assistant")}</h2><small>{floatingPanel === "notifications" ? translated(locale,"تحديثات حسابك", "Your updates") : translated(locale,"المساعد الذكي · قريبًا", "AI support · coming soon")}</small></div><button ref={floatingCloseRef} type="button" className="ydash-icon-button" onClick={() => setFloatingPanel(null)} aria-label={translated(locale,"إغلاق", "Close")}><DashboardIcon name="close" size={18}/></button></div>
        {floatingPanel === "notifications" ? <div className="ydash-float-empty"><DashboardIcon name="bell" size={32}/><h3>{translated(locale,"مفيش إشعارات لحد دلوقتي", "All caught up")}</h3><p>{translated(locale,"أي تحديثات جديدة هتظهر هنا لما نوصل خدمة الإشعارات.", "New messages will appear here once notifications are connected.")}</p></div> : <div className="ydash-chat-body"><div className="ydash-chat-message"><span className="ydash-chat-avatar"><DashboardIcon name="spark" size={17}/></span><p>{translated(locale,"أهلًا! أنا مساعد YA-DOK الافتراضي. قريبًا هقدر أساعدك في استخدام المنصة والرد على استفساراتك. المحادثة الفعلية لسه تحت التطوير.", "Hi! I'm the YA-DOK virtual assistant. Soon I'll help you navigate the platform and answer support questions. Live chat is not available yet.")}</p></div><div className="ydash-chat-compose"><input type="text" aria-label={translated(locale,"المحادثة قريبًا", "Chat coming soon")} placeholder={translated(locale,"المحادثة قيد التجهيز…", "Chat is coming soon…")} disabled/><button type="button" aria-label={translated(locale,"الإرسال غير متاح", "Sending unavailable")} disabled><DashboardIcon name="send" size={18}/></button></div></div>}
      </section>
    </div>}
    <StartSessionDialog/>
  </div>;
}

export function DashboardLogout() { return <div className="ydash-logout"><LogoutButton/></div>; }
