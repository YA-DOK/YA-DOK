"use client";

import dynamic from "next/dynamic";
import type { CSSProperties, FormEvent } from "react";
import { useEffect, useRef, useState } from "react";
import { GlassAuthPortal, type AuthMode } from "../../components/landing-lab/GlassAuthPortal";

// This page is intentionally isolated from the existing Authentication system.
// It imports the existing Stage 02 scene without modifying it.
const ClinicalWorld = dynamic(
  () => import("../../components/landing-lab/ClinicalWorld"),
  { ssr: false, loading: () => <div className="yd-sceneLoading" aria-label="Loading clinic" /> },
);

type Locale = "ar" | "en";
type Theme = "light" | "dark";
type NavId = "home" | "discover" | "about" | "team" | "contact";

const dictionary = {
  ar: {
    home: "الرئيسية", discover: "اكتشف", about: "من نحن", team: "الفريق", contact: "تواصل معنا",
    login: "تسجيل الدخول", signup: "إنشاء حساب", language: "English", mode: "تبديل المظهر",
    heroTag: "YOUR CLINICAL JOURNEY STARTS HERE", heroTitle: "اتدرّب بثقة مع YA-DOK.",
    heroText: "تجربة تعليمية طبية تفاعلية، بتقرّبك من المواقف الإكلينيكية الحقيقية.",
    heroScroll: "انزل واكتشف YA-DOK", section01: "01 / من نحن",
    aboutTitle: "من دراسة الحالة إلى القرار الإكلينيكي.",
    aboutText: "YA-DOK بيقدم تجربة محاكاة إكلينيكية تفاعلية: تتكلم مع مريض افتراضي، تجمع التاريخ المرضي، تختار الفحوصات المناسبة، وتختبر تفكيرك في التشخيص والخطة العلاجية داخل بيئة آمنة للتعلم.",
    aboutSecondary: "وبعد كل جلسة، تحصل على تقرير يساعدك تفهم قراراتك ونقاط التطوير. الصورة بتوضح فكرة المحاكاة، مش واجهة النظام النهائية.",
    progressTitle: "مؤشرات تجريبية لتوضيح شكل التقرير", sample: "بيانات تجريبية للعرض فقط — مش إحصائيات فعلية",
    progress: ["جمع التاريخ المرضي", "اختيار الفحوصات", "التفكير الإكلينيكي"],
    counts: ["مستخدم تجريبي", "زيارة تجريبية", "حالة تجريبية"],
    section02: "02 / الفريق", teamTitle: "الناس اللي ورا YA-DOK.",
    teamText: "تعرّف على أعضاء الفريق الثمانية اللي بيبنوا YA-DOK.",
    member: "عضو الفريق", photoSoon: "مكان صورة العضو", role: "عضو فريق YA-DOK",
    section03: "03 / تواصل معنا", contactTitle: "عندك سؤال أو اقتراح؟",
    contactText: "عندك سؤال أو فكرة؟ ابعتلنا رسالة على الإيميل الرسمي لفريق YA-DOK.",
    contactInfo: "بيانات التواصل", contactPending: "yaadok.2027@gmail.com",
    contactForm: "جهز رسالتك", name: "اسمك", email: "بريدك الإلكتروني", message: "رسالتك",
    namePlaceholder: "اكتب اسمك", emailPlaceholder: "name@example.com", messagePlaceholder: "اكتب رسالتك هنا...",
    copy: "نسخ الرسالة", copied: "تم نسخ الرسالة", copyError: "لم يتم النسخ، جرّب مرة تانية",
    copyHint: "الزر بينسخ الرسالة فقط، مش بيبعتها — مفيش Backend للتواصل مضاف.",
    footer: "مشروع تخرج • YA-DOK", coming: "قريبًا", menu: "فتح القائمة",
  },
  en: {
    home: "Home", discover: "Discover", about: "About us", team: "Team", contact: "Contact us",
    login: "Log in", signup: "Sign up", language: "العربية", mode: "Toggle theme",
    heroTag: "YOUR CLINICAL JOURNEY STARTS HERE", heroTitle: "Practice with purpose.",
    heroText: "An interactive medical learning experience that brings clinical practice closer to real life.",
    heroScroll: "Scroll to discover YA-DOK", section01: "01 / ABOUT US",
    aboutTitle: "From the patient story to clinical decisions.",
    aboutText: "YA-DOK brings clinical simulation into an interactive learning experience. Talk to a virtual patient, take their history, request relevant investigations, and practice your clinical reasoning in a safe environment.",
    aboutSecondary: "After each session, a feedback report helps you review decisions and identify areas to improve. The visual illustrates the concept, not a screenshot of the finished platform.",
    progressTitle: "Demo learning metrics", sample: "Demo data for presentation only — not real statistics",
    progress: ["History taking", "Investigation choices", "Clinical reasoning"],
    counts: ["Demo users", "Demo visits", "Demo cases"],
    section02: "02 / THE TEAM", teamTitle: "The people behind YA-DOK.",
    teamText: "Meet the eight people behind YA-DOK.",
    member: "Team member", photoSoon: "Member photo placeholder", role: "YA-DOK team member",
    section03: "03 / CONTACT US", contactTitle: "Have a question or an idea?",
    contactText: "Have a question or an idea? Send your message to the YA-DOK team.",
    contactInfo: "Contact details", contactPending: "yaadok.2027@gmail.com",
    contactForm: "Prepare your message", name: "Your name", email: "Your email", message: "Your message",
    namePlaceholder: "Enter your name", emailPlaceholder: "name@example.com", messagePlaceholder: "Write your message here...",
    copy: "Copy message", copied: "Message copied", copyError: "Could not copy; please try again",
    copyHint: "This copies your message only; it does not send it. No contact backend is connected.",
    footer: "Graduation project • YA-DOK", coming: "Coming soon", menu: "Open menu",
  },
} as const;

const navIds: NavId[] = ["home", "discover", "about", "team", "contact"];

function Glyph({ name, size = 18 }: { name: "sun" | "moon" | "globe" | "arrow" | "menu" | "close" | "spark" | "mail" | "down" | "home" | "discover" | "about" | "team" | "contact"; size?: number }) {
  const common = { width: size, height: size, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round" as const, strokeLinejoin: "round" as const, "aria-hidden": true as const };
  switch (name) {
    case "sun": return <svg {...common}><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M4.9 4.9l1.4 1.4m11.4 11.4 1.4 1.4M2 12h2m16 0h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>;
    case "moon": return <svg {...common}><path d="M20.9 13a9 9 0 0 1-9.9-9.9A9 9 0 1 0 20.9 13Z"/></svg>;
    case "globe": return <svg {...common}><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3.5 4 3.5 14 0 18M12 3c-3.5 4-3.5 14 0 18"/></svg>;
    case "arrow": return <svg {...common}><path d="M5 12h14m-6-6 6 6-6 6"/></svg>;
    case "menu": return <svg {...common}><path d="M4 7h16M4 12h16M4 17h16"/></svg>;
    case "close": return <svg {...common}><path d="m5 5 14 14M19 5 5 19"/></svg>;
    case "spark": return <svg {...common}><path d="m12 2 1.9 6.1L20 10l-6.1 1.9L12 18l-1.9-6.1L4 10l6.1-1.9L12 2Zm7 13 .8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8L19 15Z"/></svg>;
    case "mail": return <svg {...common}><rect x="3" y="5" width="18" height="14" rx="3"/><path d="m4 7 8 6 8-6"/></svg>;
    case "down": return <svg {...common}><path d="m6 9 6 6 6-6"/></svg>;
    case "home": return <svg {...common}><path d="m3 10 9-7 9 7v10H3z"/><path d="M9 20v-7h6v7"/></svg>;
    case "discover": return <svg {...common}><circle cx="12" cy="12" r="9"/><path d="m15.8 8.2-2.2 5.4-5.4 2.2 2.2-5.4z"/></svg>;
    case "about": return <svg {...common}><circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10v.5"/></svg>;
    case "team": return <svg {...common}><circle cx="9" cy="8" r="3"/><path d="M3 20v-2a6 6 0 0 1 12 0v2M17 5a3 3 0 0 1 0 6m1 5c1.5.6 3 1.5 3 4"/></svg>;
    case "contact": return <svg {...common}><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m4 7 8 6 8-6"/></svg>;
  }
}

function DemoCounter({ target }: { target: number }) {
  const el = useRef<HTMLSpanElement>(null);
  const [value, setValue] = useState(0);
  useEffect(() => {
    const node = el.current;
    if (!node) return;
    let raf = 0;
    let active = false;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting && !active) {
        active = true;
        cancelAnimationFrame(raf);
        if (reduced) { setValue(target); return; }
        setValue(0);
        const started = performance.now();
        const tick = (now: number) => {
          if (!active) return;
          const fraction = Math.min(1, (now - started) / 1650);
          setValue(Math.round(target * (1 - Math.pow(1 - fraction, 3))));
          if (fraction < 1) raf = requestAnimationFrame(tick);
        };
        raf = requestAnimationFrame(tick);
      } else if (!entry.isIntersecting && active) {
        active = false;
        cancelAnimationFrame(raf);
        setValue(0); // Replay on the next visit, not just the first one.
      }
    }, { threshold: 0.2, rootMargin: "-84px 0px -30px 0px" });
    observer.observe(node);
    return () => { observer.disconnect(); cancelAnimationFrame(raf); };
  }, [target]);
  return <span ref={el} className="yd-counter">{value.toLocaleString("en-US")}<span className="yd-counterPlus">+</span></span>;
}

// Portraits are intentionally not invented. Add the real photos locally.
// Photo order: frontend/public/team/member-01.jpg ... member-08.jpg.
const teamMembers = [
  { id: 1, nameEn: "Ashraf Amr Ibrahim", nameAr: "Ashraf Amr Ibrahim", photo: "/team/member-01.jpg" },
  { id: 2, nameEn: "Kareem Abdelnaser Elazazy", nameAr: "Kareem Abdelnaser Elazazy", photo: "/team/member-02.jpg" },
  { id: 3, nameEn: "Youssef Ali Elfar", nameAr: "Youssef Ali Elfar", photo: "/team/member-03.jpg" },
  { id: 4, nameEn: "Nouran HossamEldin Said", nameAr: "Nouran HossamEldin Said", photo: "/team/member-04.jpg" },
  { id: 5, nameEn: "Basmala Magdy Mohamed", nameAr: "Basmala Magdy Mohamed", photo: "/team/member-05.jpg" },
  { id: 6, nameEn: "Naira Gamal Badry Mohamed Ahmed", nameAr: "Naira Gamal Badry Mohamed Ahmed", photo: "/team/member-06.jpg" },
  { id: 7, nameEn: "Sara Mohamed Salem", nameAr: "Sara Mohamed Salem", photo: "/team/member-07.jpg" },
  { id: 8, nameEn: "Nagwa Ashraf Mohamed", nameAr: "Nagwa Ashraf Mohamed", photo: "/team/member-08.jpg" },
 ] as const;

function TeamDeck({ locale }: { locale: Locale }) {
  const [selected, setSelected] = useState<number | null>(null);
  return (
    <div className="yd-teamDeck" role="group" aria-label={locale === "ar" ? "أعضاء فريق YA-DOK" : "YA-DOK team members"}>
      {teamMembers.map((person, index) => (
        <button key={person.id} type="button"
          className={`yd-fanCard${selected === index ? " yd-fanSelected" : ""}`}
          style={{ "--fan-x": `${Math.round((index - 3.5) * 132)}px`, "--fan-y": `${Math.abs(index - 3.5) * 13}px`, "--fan-rotation": `${(index - 3.5) * -3}deg`, "--fan-delay": `${index * 100}ms`, "--fan-z": index + 10 } as CSSProperties}
          onPointerEnter={() => setSelected(index)}
          onPointerLeave={() => setSelected(null)}
          onFocus={() => setSelected(index)}
          onBlur={() => setSelected(null)}
          onClick={() => setSelected(index)}
          aria-label={person.nameEn} aria-pressed={selected === index}>
          <span className="yd-fanCount">{String(person.id).padStart(2,"0")}</span>
          <img className="yd-fanPhoto" src={person.photo} alt={person.nameEn} loading={index < 4 ? "eager" : "lazy"} onError={event => { event.currentTarget.style.opacity = "0"; }} />
          <span className="yd-fanFallback" aria-hidden="true">{person.nameEn.split(" ").slice(0,2).map(word => word[0]).join("")}</span>
          <span className="yd-fanInfo"><strong>{locale === "ar" ? person.nameAr : person.nameEn}</strong><small>YA-DOK TEAM</small></span>
        </button>
      ))}
      <span className="yd-deckHint">{locale === "ar" ? "قف على صورة أو اضغط لتتعرف على العضو" : "Hover or tap a card to meet the member"}</span>
    </div>
  );
}

function GuideAvatar() {
  // Transparent WebP rendered for this project. A visual guide, not a live 3D talking agent.
  return <img className="yd-guideAvatar" src="/brand/yadok-doctor-guide.webp" alt="YA-DOK virtual medical guide" width={580} height={870} draggable={false}/>;
}

type TourStep = "closed" | "welcome" | "doctor" | "paper" | "finish";

const tourText = {
  en: {
    introTitle: "Welcome to YA-DOK", intro: "I'll take you on a quick tour of our virtual clinical training experience. Choose how you'd like to explore.",
    tour3d: "Start 3D tour", demo: "Watch demo", soon: "Video coming soon", close: "Exit tour", next: "Next", back: "Back",
    doctorTitle: "Meet your virtual patient", doctor: "Practice talking to a patient, asking the right questions and collecting a full medical history. Your clinical decisions shape the simulation.",
    paperTitle: "Choose investigations", paper: "Request the tests and scans you need, then use the findings to support your diagnosis and clinical reasoning.",
    finishTitle: "Ready to practice?", finish: "Your next patient is waiting. Create your free YA-DOK account to start your clinical journey.",
    start: "Let's go — Sign up", login: "I have an account", openAuth: "Open full secure page", accountTitle: "Continue your YA-DOK journey", secure: "Your existing authentication system is used here.",
  },
  ar: {
    introTitle: "أهلًا بيك في YA-DOK", intro: "هآخدك في جولة سريعة تتعرف فيها على تجربة التدريب الطبي الافتراضي. اختار طريقة الاستكشاف.",
    tour3d: "ابدأ جولة 3D", demo: "شاهد الديمو", soon: "الفيديو قريبًا", close: "إنهاء الجولة", next: "التالي", back: "رجوع",
    doctorTitle: "اتعرف على المريض الافتراضي", doctor: "اتدرب على الحوار مع المريض، واسأله الأسئلة المناسبة واجمع التاريخ المرضي. قراراتك هي اللي هتوجّه المحاكاة.",
    paperTitle: "اختار الفحوصات", paper: "اطلب التحاليل والأشعات اللي تحتاجها، واستخدم النتائج في الوصول للتشخيص وتفسير قراراتك الطبية.",
    finishTitle: "جاهز تبدأ التدريب؟", finish: "مريضك الافتراضي الجاي مستنيك. اعمل حساب YA-DOK وابدأ رحلتك.",
    start: "يلا نبدأ — إنشاء حساب", login: "عندي حساب", openAuth: "افتح الصفحة الآمنة كاملة", accountTitle: "كمّل رحلتك في YA-DOK", secure: "نظام التسجيل الحالي هو المستخدم بدون تعديل.",
  },
} as const;

// Fully self-contained styling. No CSS Module import to get lost during ZIP extraction.
const CSS = `
.yd-page{--yd-text:#173b3a;--yd-textMuted:#607b7a;--yd-bg:#f4faf7;--yd-bg2:#e6f3ef;--yd-card:rgba(255,255,255,.72);--yd-border:rgba(40,104,96,.17);--yd-accent:#147b70;--yd-strong:#083c3a;--yd-shadow:rgba(20,75,68,.11);color:var(--yd-text);background:var(--yd-bg);font-family:inherit;min-height:100dvh;overflow:hidden;isolation:isolate;transition:background .85s,color .85s}
.yd-page *{box-sizing:border-box}.yd-page button,.yd-page input,.yd-page textarea{font:inherit}.yd-page button{cursor:pointer}.yd-page button:focus-visible,.yd-page a:focus-visible,.yd-page input:focus-visible,.yd-page textarea:focus-visible{outline:3px solid #58cdbc;outline-offset:3px}.yd-page a{text-decoration:none;color:inherit}
.yd-page.yd-dark{--yd-text:#e9faf5;--yd-textMuted:#a6c5bd;--yd-bg:#071b22;--yd-bg2:#0e2930;--yd-card:rgba(19,51,56,.72);--yd-border:rgba(160,231,215,.18);--yd-accent:#79e7cc;--yd-strong:#b3fae7;--yd-shadow:rgba(0,0,0,.28)}
.yd-page.yd-flipping{pointer-events:none;animation:yd-flipWorld .82s cubic-bezier(.55,.03,.35,.99) both;transform-origin:50% 40%;backface-visibility:hidden}
@keyframes yd-flipWorld{0%{transform:perspective(1700px) rotateY(0) scale(1)}43%{transform:perspective(1700px) rotateY(78deg) scale(.91)}51%{transform:perspective(1700px) rotateY(92deg) scale(.9)}60%{transform:perspective(1700px) rotateY(-66deg) scale(.93)}100%{transform:perspective(1700px) rotateY(0) scale(1)}}
.yd-topbar{position:fixed;z-index:80;top:22px;left:clamp(14px,3.2vw,56px);right:clamp(14px,3.2vw,56px);height:60px;display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:16px;pointer-events:none}
.yd-topbar>*{pointer-events:auto}.yd-brand{justify-self:start;display:inline-flex;align-items:center;gap:10px;border:1px solid var(--yd-border);border-radius:18px;background:var(--yd-card);backdrop-filter:blur(24px);-webkit-backdrop-filter:blur(24px);box-shadow:0 8px 35px var(--yd-shadow);height:56px;padding:6px 14px 6px 8px}.yd-brand img{width:94px;height:42px;object-fit:contain}.yd-brandFallback{font-size:14px;font-weight:900;letter-spacing:.14em}.yd-dark .yd-brand img{background:rgba(255,255,255,.93);border-radius:12px;padding:4px}
.yd-nav{position:relative;display:flex;align-items:center;justify-content:center;direction:ltr;height:56px;padding:6px;border-radius:22px;border:1px solid var(--yd-border);background:var(--yd-card);box-shadow:0 12px 42px var(--yd-shadow);backdrop-filter:blur(26px);-webkit-backdrop-filter:blur(26px);white-space:nowrap}.yd-navPill{position:absolute;top:6px;bottom:6px;left:0;border-radius:16px;background:var(--yd-strong);box-shadow:0 3px 15px var(--yd-shadow);transition:transform .45s cubic-bezier(.2,.9,.2,1),width .45s cubic-bezier(.2,.9,.2,1);pointer-events:none;z-index:0}
.yd-navButton{border:0;background:transparent;padding:10px 17px;position:relative;z-index:1;color:var(--yd-textMuted);font-size:13px;font-weight:750;transition:color .3s,opacity .2s;border-radius:15px;min-width:72px;text-align:center}.yd-navButton.yd-selected{color:var(--yd-bg)}.yd-dark .yd-navButton.yd-selected{color:#092b30}.yd-navButton:disabled{cursor:default;opacity:.46}.yd-navButton:not(:disabled):hover:not(.yd-selected){color:var(--yd-text)}
.yd-actions{display:flex;align-items:center;justify-self:end;gap:7px;direction:ltr}.yd-iconButton,.yd-langButton,.yd-authButton{border:1px solid var(--yd-border);background:var(--yd-card);color:var(--yd-text);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);height:44px;border-radius:15px;display:inline-flex;align-items:center;justify-content:center;gap:7px;font-weight:750;font-size:12px;box-shadow:0 5px 24px var(--yd-shadow);transition:transform .2s,background .3s}.yd-actions button:hover,.yd-actions a:hover{transform:translateY(-3px)}.yd-iconButton{width:44px}.yd-langButton{padding:0 13px;min-width:87px}.yd-authButton{padding:0 16px}.yd-authButton.yd-primary{background:var(--yd-strong);color:var(--yd-bg)}.yd-dark .yd-authButton.yd-primary{color:#082a2a}.yd-mobileButton{display:none}.yd-mobileMenu{display:none}
.yd-hero{position:relative;min-height:100dvh;height:100dvh;overflow:hidden;background:#eef7f2}.yd-scene{position:absolute;inset:0;filter:none;transition:filter 1s ease}.yd-dark .yd-scene{filter:brightness(.43) saturate(.9) hue-rotate(10deg)}.yd-sceneLoading{position:absolute;inset:0;background:radial-gradient(ellipse at center,#f1f8f5,#dbeae3)}
.yd-hero::after{content:'';position:absolute;z-index:1;inset:0;pointer-events:none;background:linear-gradient(180deg,rgba(245,251,248,.22) 0%,transparent 24%,transparent 68%,rgba(246,251,249,.17) 100%);transition:background .85s}.yd-dark .yd-hero::after{background:linear-gradient(180deg,rgba(2,24,31,.34),transparent 40%,rgba(3,23,31,.21))}
.yd-heroOverlay{position:absolute;z-index:2;left:clamp(18px,4vw,75px);bottom:clamp(25px,6vh,65px);max-width:420px;pointer-events:none}.yd-heroTag{display:inline-flex;align-items:center;gap:8px;font-size:10px;font-weight:900;letter-spacing:.2em;text-transform:uppercase;color:#186f68;margin-bottom:12px}.yd-dark .yd-heroTag{color:#80e6ce}.yd-heroDot{width:8px;height:8px;border-radius:100%;background:#1ca58d;box-shadow:0 0 0 6px rgba(22,167,138,.12)}.yd-heroOverlay h1{font-size:clamp(25px,3.2vw,48px);letter-spacing:-.045em;line-height:1.1;margin:0 0 12px;font-weight:900;color:var(--yd-text);text-shadow:0 1px 20px rgba(255,255,255,.3)}.yd-heroOverlay p{font-size:clamp(12px,1.15vw,15px);line-height:1.8;color:var(--yd-textMuted);margin:0}.yd-heroScroll{display:inline-flex;align-items:center;gap:9px;margin-top:20px;font-size:12px;font-weight:750;color:var(--yd-text);border:1px solid var(--yd-border);border-radius:999px;background:var(--yd-card);padding:10px 13px;backdrop-filter:blur(10px);pointer-events:auto;box-shadow:0 8px 25px var(--yd-shadow)}.yd-heroScroll svg{animation:yd-nudge 1.8s infinite}@keyframes yd-nudge{50%{transform:translateY(4px)}}
.yd-mainSection{position:relative;background:var(--yd-bg);padding:clamp(90px,11vw,145px) 6vw;transition:background .85s;scroll-margin-top:75px}.yd-sectionInner{max-width:1210px;margin:0 auto}.yd-sectionEyebrow{display:inline-flex;align-items:center;gap:8px;text-transform:uppercase;color:var(--yd-accent);font-weight:900;font-size:12px;letter-spacing:.12em;margin-bottom:22px}.yd-sectionEyebrow::before{content:'';display:block;width:26px;height:2px;background:currentColor}.yd-sectionTitle{font-size:clamp(32px,4.9vw,66px);font-weight:900;line-height:1.14;letter-spacing:-.055em;max-width:750px;margin:0 0 24px}.yd-sectionLead{line-height:1.95;font-size:clamp(15px,1.6vw,19px);max-width:690px;color:var(--yd-textMuted);margin:0}.yd-sectionSmall{font-size:14px;color:var(--yd-textMuted);line-height:1.8;max-width:650px;margin-top:18px}
.yd-aboutTop{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,.85fr);align-items:start;gap:50px}.yd-aboutAccent{border:1px solid var(--yd-border);border-radius:30px;background:linear-gradient(140deg,var(--yd-card),transparent);padding:35px;min-height:310px;display:flex;flex-direction:column;align-items:center;justify-content:center;position:relative;overflow:hidden}.yd-orbit{width:min(250px,100%);aspect-ratio:1;border:1px solid var(--yd-border);border-radius:50%;display:flex;align-items:center;justify-content:center;animation:yd-spin 27s linear infinite}.yd-orbit::before{content:'';position:absolute;width:71%;height:71%;border:1px dashed var(--yd-border);border-radius:50%}.yd-orbitCore{width:110px;height:110px;border-radius:32px;display:grid;place-items:center;background:var(--yd-strong);color:var(--yd-bg);font-weight:900;font-size:23px;letter-spacing:-.05em;animation:yd-counterspin 27s linear infinite;box-shadow:0 20px 45px var(--yd-shadow)}@keyframes yd-spin{to{transform:rotate(360deg)}}@keyframes yd-counterspin{to{transform:rotate(-360deg)}}
.yd-metrics{margin-top:86px;border-radius:31px;border:1px solid var(--yd-border);background:var(--yd-card);padding:clamp(24px,4vw,52px);box-shadow:0 16px 55px var(--yd-shadow)}.yd-metricsHead{display:flex;align-items:center;justify-content:space-between;gap:24px;flex-wrap:wrap;margin-bottom:38px}.yd-metrics h3{font-size:clamp(23px,2.8vw,33px);margin:0}.yd-demoTag{border:1px solid var(--yd-border);border-radius:999px;background:var(--yd-bg2);padding:8px 13px;font-size:11px;color:var(--yd-textMuted);font-weight:700}.yd-progressRows{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:30px}.yd-progressLabel{display:flex;justify-content:space-between;gap:6px;font-weight:750;font-size:13px;margin-bottom:13px}.yd-progressTrack{height:10px;border-radius:100px;background:var(--yd-bg2);overflow:hidden}.yd-progressFill{display:block;height:100%;border-radius:100px;background:linear-gradient(90deg,#167c71,#80e5cf);transform:scaleX(0);transform-origin:left center;transition:transform 1.6s cubic-bezier(.13,1,.22,1)}.yd-visible .yd-progressFill{transform:scaleX(1)}.yd-statGrid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:30px}.yd-statBox{background:var(--yd-bg2);border:1px solid var(--yd-border);border-radius:20px;padding:27px}.yd-counter{display:block;font-weight:900;font-size:clamp(26px,3vw,43px);letter-spacing:-.04em;font-variant-numeric:tabular-nums}.yd-counterPlus{font-size:.6em;color:var(--yd-accent)}.yd-statBox p{color:var(--yd-textMuted);font-size:12px;margin:6px 0 0}
.yd-teamSection{background:var(--yd-bg2)}.yd-teamHeader{display:flex;justify-content:space-between;align-items:end;gap:20px;flex-wrap:wrap;margin-bottom:44px}.yd-teamHeader .yd-sectionTitle{margin-bottom:10px}.yd-teamGrid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:18px}.yd-personCard{overflow:hidden;border-radius:24px;background:var(--yd-card);border:1px solid var(--yd-border);box-shadow:0 14px 30px var(--yd-shadow);transition:transform .35s,box-shadow .35s,opacity .7s,translate .7s}.yd-personCard:hover{transform:translateY(-8px);box-shadow:0 20px 44px var(--yd-shadow)}.yd-personArt{height:225px;position:relative;display:flex;align-items:end;justify-content:center;overflow:hidden;isolation:isolate}.yd-personArt-0{background:linear-gradient(140deg,#bedad4,#82b9b0)}.yd-personArt-1{background:linear-gradient(140deg,#e6dfcb,#b9c7bf)}.yd-personArt-2{background:linear-gradient(140deg,#bad6db,#85afc4)}.yd-personArt-3{background:linear-gradient(140deg,#d4d0e9,#aca6cb)}.yd-personHalo{position:absolute;width:155px;height:155px;top:22px;border-radius:50%;background:rgba(255,255,255,.26);border:1px solid rgba(255,255,255,.32)}.yd-personSilhouette{position:relative;z-index:1;width:83%;height:94%;color:#597d79;filter:drop-shadow(0 -5px 0 rgba(255,255,255,.14))}.yd-personArt-1 .yd-personSilhouette{color:#777e71}.yd-personArt-2 .yd-personSilhouette{color:#527b91}.yd-personArt-3 .yd-personSilhouette{color:#78738e}.yd-personNumber{position:absolute;top:15px;left:16px;z-index:2;color:rgba(18,59,56,.53);font-size:13px;font-weight:900}.yd-personDetails{padding:19px 21px 23px}.yd-personDetails h3{font-size:16px;margin:0 0 5px}.yd-personDetails p{font-size:12px;color:var(--yd-textMuted);margin:0}
.yd-contactLayout{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:40px;align-items:start}.yd-contactInfo{margin-top:35px;border:1px solid var(--yd-border);background:var(--yd-card);border-radius:25px;padding:27px}.yd-contactInfo h3{font-size:18px;margin:0 0 12px}.yd-contactInfo p{color:var(--yd-textMuted);font-size:14px;line-height:1.8;margin:0}.yd-contactForm{padding:33px;border:1px solid var(--yd-border);border-radius:28px;background:var(--yd-card);box-shadow:0 16px 44px var(--yd-shadow)}.yd-contactForm h3{margin:0 0 24px;font-size:23px}.yd-field{display:block;margin-bottom:18px}.yd-field span{display:block;font-size:13px;font-weight:750;margin-bottom:9px}.yd-field input,.yd-field textarea{width:100%;min-width:0;border:1px solid var(--yd-border);background:var(--yd-bg);border-radius:13px;padding:14px 16px;color:var(--yd-text);outline:0;resize:vertical}.yd-field textarea{min-height:125px}.yd-field input::placeholder,.yd-field textarea::placeholder{color:var(--yd-textMuted);opacity:.7}.yd-copyButton{border:0;border-radius:14px;padding:13px 24px;background:var(--yd-strong);color:var(--yd-bg);font-weight:800;display:inline-flex;align-items:center;gap:10px}.yd-dark .yd-copyButton{color:#082a2a}.yd-contactHint{font-size:11px;line-height:1.6;color:var(--yd-textMuted);margin:13px 0 0}.yd-footer{background:var(--yd-bg2);border-top:1px solid var(--yd-border);padding:28px 6vw;color:var(--yd-textMuted);font-size:12px;text-align:center}
.yd-reveal{opacity:0;translate:0 33px;transition:opacity .8s ease,translate .8s cubic-bezier(.2,.9,.25,1)}.yd-reveal.yd-visible{opacity:1;translate:0 0}
.yd-themeCurtain{position:fixed;z-index:200;inset:0;pointer-events:none;display:flex;justify-content:center;align-items:center;background:radial-gradient(circle at center,rgba(158,231,205,.25) 0%,transparent 58%);animation:yd-themeFlash 1.15s both}.yd-themeCurtain.yd-showMoon{background:radial-gradient(circle at center,rgba(80,143,177,.31),rgba(7,25,38,.13) 40%,transparent 73%)}.yd-themeSymbol{display:grid;place-items:center;width:145px;height:145px;border-radius:50%;background:rgba(255,255,255,.87);color:#dfac38;box-shadow:0 0 0 25px rgba(255,255,255,.12),0 0 0 54px rgba(255,255,255,.06),0 30px 70px rgba(0,0,0,.17);backdrop-filter:blur(12px);animation:yd-themePop 1.15s ease both}.yd-showMoon .yd-themeSymbol{background:#122c44;color:#bcd8ff;box-shadow:0 0 0 25px rgba(89,139,185,.13),0 0 0 54px rgba(71,115,157,.06),0 30px 70px rgba(0,0,0,.25)}@keyframes yd-themePop{0%{opacity:0;transform:scale(.45) rotate(-75deg)}25%{opacity:1;transform:scale(1.1) rotate(5deg)}52%{opacity:1;transform:scale(1) rotate(0)}85%{opacity:1;transform:scale(1.02)}100%{opacity:0;transform:scale(1.8) rotate(25deg)}}@keyframes yd-themeFlash{0%{opacity:0}20%{opacity:1}75%{opacity:1}100%{opacity:0}}
@media(max-width:1270px){.yd-navButton{padding:10px 11px;min-width:62px}.yd-topbar{left:18px;right:18px;gap:9px}.yd-authButton{padding:0 12px}.yd-brand img{width:78px}}
@media(max-width:1050px){.yd-topbar{grid-template-columns:auto 1fr;gap:9px}.yd-nav{display:none}.yd-actions{grid-column:2}.yd-mobileButton{display:inline-flex}.yd-mobileMenu{position:fixed;top:90px;right:18px;left:18px;z-index:80;display:flex;flex-direction:column;padding:12px;border-radius:22px;border:1px solid var(--yd-border);background:var(--yd-card);backdrop-filter:blur(28px);-webkit-backdrop-filter:blur(28px);box-shadow:0 15px 45px var(--yd-shadow)}.yd-mobileMenu button{border:0;border-radius:12px;background:transparent;color:var(--yd-text);font-weight:800;text-align:start;padding:13px}.yd-mobileMenu button.yd-selected{background:var(--yd-strong);color:var(--yd-bg)}.yd-mobileMenu button:disabled{opacity:.4}.yd-aboutTop{gap:26px}}
@media(max-width:720px){.yd-topbar{top:12px;left:12px;right:12px;height:48px}.yd-brand{height:48px;padding:5px 8px}.yd-brand img{width:58px;height:36px}.yd-actions{gap:5px}.yd-authButton{font-size:11px;padding:0 10px;height:39px}.yd-langButton{min-width:43px;padding:0 8px;height:39px;font-size:0}.yd-langButton svg{width:19px}.yd-iconButton{width:39px;height:39px}.yd-actions .yd-login{display:none}.yd-heroOverlay{bottom:27px;left:20px;right:20px;max-width:315px}.yd-heroOverlay h1{font-size:27px}.yd-heroOverlay p{font-size:12px}.yd-aboutTop,.yd-contactLayout{grid-template-columns:1fr}.yd-aboutAccent{min-height:250px;order:-1}.yd-progressRows,.yd-statGrid{grid-template-columns:1fr}.yd-teamGrid{grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.yd-personArt{height:175px}.yd-personDetails{padding:15px}.yd-personDetails h3{font-size:13px}.yd-personDetails p{font-size:11px}.yd-mainSection{padding:94px 20px}.yd-metrics{margin-top:40px}.yd-contactForm{padding:22px}.yd-mobileMenu{top:69px;left:12px;right:12px}}
@media(max-width:400px){.yd-brand img{width:46px}.yd-actions .yd-primary{padding:0 8px}.yd-heroOverlay{max-width:260px}.yd-heroTag{font-size:8px}}
@media(prefers-reduced-motion:reduce){.yd-page,.yd-page *,.yd-page *::before,.yd-page *::after{animation-duration:.01ms!important;transition-duration:.01ms!important;scroll-behavior:auto!important}.yd-reveal{opacity:1;translate:0 0}.yd-progressFill{transform:scaleX(1)}}

/* Task 04: smooth section-by-section navigation; small-screen tall sections remain scrollable. */
html:has(.yd-page){scroll-snap-type:y mandatory;scroll-behavior:smooth}
.yd-page{overflow:clip;transition:background .25s,color .25s}
.yd-hero,.yd-mainSection{scroll-snap-align:start;scroll-snap-stop:always}
.yd-mainSection{min-height:100svh;padding:100px 5vw 46px;display:flex;align-items:center}
.yd-sectionInner{width:100%}
.yd-sectionTitle{font-size:clamp(27px,3.4vw,50px);margin-bottom:15px}
.yd-sectionLead{font-size:clamp(14px,1.2vw,17px);line-height:1.8}
.yd-sectionSmall{font-size:13px;margin-top:9px;line-height:1.7}
.yd-sectionEyebrow{margin-bottom:12px}
.yd-aboutTop{gap:34px;align-items:center;grid-template-columns:minmax(0,1.04fr) minmax(0,.96fr)}
.yd-aboutAccent{min-height:220px;padding:9px;background:rgba(255,255,255,.06);border-radius:23px}
.yd-simImageWrap{width:100%;height:min(29vh,266px);min-height:185px;position:relative;border-radius:17px;overflow:hidden}
.yd-simImageWrap img{width:100%;height:100%;object-fit:cover;display:block;filter:saturate(1.07)}
.yd-simImageWrap::after{content:"";position:absolute;inset:60% 0 0;background:linear-gradient(transparent,rgba(2,29,39,.45));pointer-events:none}
.yd-simLive{position:absolute;bottom:15px;left:15px;z-index:1;color:#fff;font-size:12px;display:flex;gap:8px;align-items:center;background:rgba(7,33,43,.58);backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,.25);padding:7px 11px;border-radius:99px}
.yd-liveDot{width:7px;height:7px;border-radius:50%;background:#6df3d6;box-shadow:0 0 0 3px rgba(109,243,214,.14)}
.yd-simCaption{position:absolute;z-index:1;top:21px;right:20px;background:rgba(9,35,44,.76);border:1px solid rgba(255,255,255,.15);color:#dafaf3;border-radius:99px;display:flex;align-items:center;gap:5px;padding:7px 10px;font-size:10px;letter-spacing:.09em}
.yd-metrics{margin-top:20px;padding:clamp(18px,2vw,25px);border-radius:24px}
.yd-metricsHead{margin-bottom:18px}.yd-metrics h3{font-size:20px}
.yd-progressRows{gap:20px}.yd-progressTrack{height:12px;background:color-mix(in srgb,var(--yd-accent) 14%,transparent);box-shadow:inset 0 2px 4px rgba(0,0,0,.1)}
.yd-progressFill{transform:scaleX(0);transition:transform 1.15s cubic-bezier(.18,.84,.25,1);transition-delay:var(--yd-delay,0ms);box-shadow:0 0 20px rgba(46,217,184,.19)}
.yd-metrics.yd-visible .yd-progressFill{transform:scaleX(1)}
.yd-statGrid{margin-top:18px}.yd-statBox{padding:15px 20px;border-radius:16px}.yd-counter{font-size:clamp(24px,2.4vw,33px)}
/* iOS-inspired frosted capsule + sliding liquid thumb. */
.yd-topbar{z-index:100;top:14px;left:clamp(14px,2.6vw,40px);right:clamp(14px,2.6vw,40px)}
.yd-nav{height:57px;padding:5px;gap:1px;border-radius:999px;background:linear-gradient(145deg,rgba(255,255,255,.68),rgba(233,245,246,.32));border:1px solid rgba(255,255,255,.74);box-shadow:0 14px 36px rgba(31,53,59,.13),inset 0 2px 2px rgba(255,255,255,.85),inset 0 -3px 7px rgba(83,110,117,.1);backdrop-filter:blur(25px) saturate(190%);-webkit-backdrop-filter:blur(25px) saturate(190%)}
.yd-dark .yd-nav{background:linear-gradient(140deg,rgba(34,61,72,.77),rgba(13,39,48,.55));border-color:rgba(225,255,250,.24);box-shadow:0 16px 36px rgba(0,0,0,.28),inset 0 1px rgba(255,255,255,.13)}
.yd-navPill{top:5px;bottom:5px;background:linear-gradient(165deg,rgba(255,255,255,.96),rgba(205,227,228,.92));border-radius:999px;box-shadow:0 3px 8px rgba(23,56,63,.18),inset 0 1px 3px rgba(255,255,255,.9),0 0 0 1px rgba(255,255,255,.55);transition:transform .42s cubic-bezier(.2,1.14,.35,1),width .42s cubic-bezier(.2,1.14,.35,1)}
.yd-dark .yd-navPill{background:linear-gradient(150deg,rgba(115,164,173,.62),rgba(66,105,117,.76));box-shadow:0 5px 13px rgba(0,0,0,.25),inset 0 1px 2px rgba(255,255,255,.17)}
.yd-navButton{display:flex;align-items:center;gap:7px;justify-content:center;padding:11px 14px;border-radius:999px;min-width:82px;color:#3e595b;font-size:12px;font-weight:760}
.yd-navButton svg{flex:none}.yd-navButton.yd-selected{color:#16383e}.yd-dark .yd-navButton{color:#c2d9d7}.yd-dark .yd-navButton.yd-selected{color:#e6fffa}
.yd-navButton:disabled{opacity:.65;cursor:not-allowed}
.yd-brand,.yd-iconButton,.yd-authButton{background:rgba(255,255,255,.48);border-color:rgba(255,255,255,.57);backdrop-filter:blur(19px) saturate(150%);-webkit-backdrop-filter:blur(19px) saturate(150%)}
.yd-dark .yd-brand,.yd-dark .yd-iconButton,.yd-dark .yd-authButton{background:rgba(30,62,68,.65);border-color:rgba(200,255,247,.16)}
.yd-langSwitch{display:flex;position:relative;align-items:center;justify-content:space-between;height:43px;width:84px;padding:3px;border-radius:99px;border:1px solid var(--yd-border);background:var(--yd-card);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);isolation:isolate;box-shadow:0 5px 22px var(--yd-shadow)}
.yd-langSwitch>span:not(.yd-langThumb){position:relative;z-index:1;flex:1;text-align:center;color:var(--yd-textMuted);font-size:12px;font-weight:800;transition:color .24s}
.yd-langSwitch>span.yd-langActive{color:var(--yd-strong)}
.yd-langThumb{position:absolute!important;z-index:0!important;left:3px;top:3px;width:calc((100% - 6px)/2);height:calc(100% - 6px);border-radius:99px;background:rgba(255,255,255,.95);box-shadow:0 2px 9px rgba(0,0,0,.14);transition:transform .32s cubic-bezier(.2,1.2,.28,1)}
.yd-dark .yd-langThumb{background:#4f8b83}
.yd-languageWave{position:fixed;inset:0;z-index:150;pointer-events:none;display:grid;place-items:center;animation:yd-languageMask .48s ease-out both;background:linear-gradient(110deg,transparent 0%,rgba(32,137,124,.25) 40%,rgba(106,226,201,.45) 53%,transparent 68%);backdrop-filter:blur(2px)}
.yd-languageWave span{font-weight:900;font-size:clamp(27px,5vw,60px);color:var(--yd-strong);text-shadow:0 3px 20px rgba(255,255,255,.45);animation:yd-langWords .48s ease-out both}
@keyframes yd-languageMask{0%{clip-path:polygon(-30% 0,-5% 0,-5% 100%,-30% 100%);opacity:0}22%{opacity:1}75%{opacity:1}100%{clip-path:polygon(105% 0,135% 0,135% 100%,105% 100%);opacity:0}}
@keyframes yd-langWords{0%,100%{opacity:0;transform:translateY(18px) scale(.95)}30%,70%{opacity:1;transform:translateY(0) scale(1)}}
.yd-page.yd-flipping{animation:none;pointer-events:auto;transform:none}
.yd-themeCurtain{animation-duration:.78s}.yd-themeSymbol{width:115px;height:115px;animation-duration:.78s}
.yd-scene,.yd-hero::after{transition:none}.yd-dark .yd-scene{filter:none}.yd-dark .yd-hero::after{background:rgba(5,21,30,.19)}
/* Team cards arrive individually, not all at once. */
.yd-teamGrid{grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}
.yd-teamHeader{margin-bottom:17px}
.yd-personCard{opacity:0;transform:translate3d(0,29px,0) scale(.97);transition:transform .5s cubic-bezier(.19,1,.22,1),opacity .5s ease,box-shadow .25s;transition-delay:calc(var(--yd-index)*105ms);border-radius:20px;will-change:opacity,transform}
.yd-teamGrid.yd-visible .yd-personCard{opacity:1;transform:translate3d(0,0,0) scale(1)}
.yd-teamGrid.yd-visible .yd-personCard:hover{transform:translateY(-6px)}
.yd-personArt{height:clamp(150px,21vh,188px)}
.yd-placeholderFace{position:absolute;bottom:0;width:95px;height:142px;display:flex;justify-content:center}
.yd-placeholderHead{position:absolute;top:15px;width:55px;height:60px;border-radius:44% 44% 50% 50%;background:#7a9f9b;box-shadow:inset -9px 0 0 rgba(0,0,0,.08)}
.yd-placeholderBody{position:absolute;bottom:-27px;width:116px;height:94px;border-radius:60px 60px 0 0;background:#456c75}
.yd-teamPortrait{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0;transition:opacity .35s ease;z-index:1}
.yd-teamPortrait.yd-portraitReady{opacity:1}
.yd-personArtShine{position:absolute;inset:0;z-index:2;pointer-events:none;background:linear-gradient(135deg,rgba(255,255,255,.22),transparent 46%)}
.yd-personDetails{padding:14px 16px}.yd-personDetails h3{font-size:14px}
.yd-reveal{transition:opacity .65s ease,translate .65s cubic-bezier(.2,.9,.25,1)}
@media(max-width:1250px){.yd-navButton{min-width:auto;padding:11px 9px;gap:5px;font-size:11px}.yd-topbar{left:14px;right:14px}.yd-brand img{width:77px}.yd-authButton{padding:0 10px}}
@media(max-width:1090px){.yd-mainSection{min-height:100svh;padding:90px 5vw 35px}.yd-personArt{height:158px}}
@media(max-width:1050px){.yd-nav{display:none}.yd-mobileMenu{z-index:110}.yd-langSwitch{width:77px;height:40px}}
@media(max-width:720px){html:has(.yd-page){scroll-snap-type:y proximity}.yd-mainSection{display:block;min-height:100svh;padding:86px 20px 40px}.yd-aboutTop{grid-template-columns:1fr;gap:15px}.yd-aboutAccent{order:0;min-height:190px}.yd-simImageWrap{height:190px}.yd-metrics{margin-top:16px}.yd-progressRows,.yd-statGrid{grid-template-columns:1fr;gap:10px}.yd-statGrid{grid-template-columns:repeat(3,minmax(0,1fr))}.yd-statBox{padding:10px}.yd-counter{font-size:21px}.yd-personArt{height:145px}.yd-teamGrid{gap:10px}.yd-sectionTitle{font-size:30px}.yd-aboutAccent{padding:6px}.yd-simCaption{display:none}}
@media(prefers-reduced-motion:reduce){html:has(.yd-page){scroll-behavior:auto;scroll-snap-type:y proximity}.yd-languageWave,.yd-themeCurtain{display:none}.yd-teamGrid .yd-personCard{opacity:1;transform:none;transition:none}.yd-progressFill{transform:scaleX(1)}}


/* Task 05: fixed visual layout, repeatable reveals and legibility. */
.yd-page{color:var(--yd-text);color-scheme:dark;}
.yd-page:not(.yd-dark){color-scheme:light}
.yd-topbar,.yd-nav,.yd-actions,.yd-brand{direction:ltr}
.yd-topbar{height:60px;isolation:isolate}
.yd-nav{flex-wrap:nowrap;min-width:0;gap:2px}
.yd-navButton{flex:0 0 99px;width:99px;min-width:99px;padding:10px 5px;white-space:nowrap;line-height:1.2;font-size:12px}
.yd-navButton[data-nav="contact"]{flex-basis:115px;width:115px;min-width:115px}
.yd-navButton.yd-selected{color:#103b3d!important;text-shadow:none}
.yd-dark .yd-navButton.yd-selected{color:#fff!important}
.yd-dark .yd-navPill{background:linear-gradient(145deg,#326877,#447e89);border:1px solid rgba(217,255,248,.32)}
.yd-navButton:not(.yd-selected){color:var(--yd-text)!important;opacity:.83}
.yd-navButton:disabled{opacity:.55}
.yd-brand img{object-fit:contain}
.yd-dark .yd-brand{background:rgba(16,46,51,.79)}
.yd-dark .yd-brand img{background:rgba(255,255,255,.96)}
.yd-page .yd-sectionTitle,.yd-page .yd-personDetails h3{color:var(--yd-text)}
.yd-page .yd-sectionLead,.yd-page .yd-sectionSmall,.yd-page .yd-personDetails p{color:var(--yd-textMuted)}
.yd-dark .yd-demoTag,.yd-dark .yd-contactHint,.yd-dark .yd-progressLabel,.yd-dark .yd-field span{color:#c1dbd5}
.yd-dark .yd-statBox,.yd-dark .yd-contactForm{background:rgba(18,53,61,.83);border-color:rgba(165,238,225,.22)}
.yd-dark .yd-statBox p{color:#b6d5d0}
.yd-dark .yd-authButton:not(.yd-primary),.yd-dark .yd-iconButton,.yd-dark .yd-langSwitch{color:#ebfcfa}
.yd-dark .yd-authButton.yd-primary{color:#073a37;background:#8bf1d4}
.yd-langSwitch{direction:ltr;flex:none}
.yd-langSwitch>span:not(.yd-langThumb){min-width:0;color:var(--yd-textMuted)}
.yd-langSwitch>span.yd-langActive{color:var(--yd-strong)}
.yd-page .yd-heroTag{font-weight:850}
/* Snap gently, not mandatory: long sections must remain fully scrollable. */
html:has(.yd-page){scroll-snap-type:y proximity;scroll-padding-top:0;scroll-behavior:smooth}
.yd-page .yd-mainSection{display:block;min-height:100svh;height:auto;scroll-snap-align:start;scroll-snap-stop:normal;scroll-margin-top:0;padding:clamp(122px,14vh,150px) clamp(20px,5vw,84px) clamp(65px,9vh,100px)}
.yd-page .yd-sectionInner{max-width:1270px;width:100%}
.yd-page .yd-aboutTop{align-items:center;gap:clamp(22px,4vw,55px)}
.yd-page .yd-metrics{margin-top:clamp(24px,4vh,45px)}
.yd-page .yd-teamHeader{margin-bottom:28px}
.yd-page .yd-sectionEyebrow{margin-bottom:13px}
.yd-page .yd-sectionTitle{margin-bottom:17px;line-height:1.14}
.yd-page .yd-sectionLead{line-height:1.7}
.yd-page .yd-sectionSmall{line-height:1.6;margin-top:12px}
/* Hidden until each entry, then a distinct scroll-in reveal. */
.yd-page .yd-reveal{opacity:0;translate:none;transform:translate3d(0,48px,0) scale(.985);filter:blur(6px);transition:opacity .85s cubic-bezier(.2,.8,.2,1),transform .85s cubic-bezier(.2,.8,.2,1),filter .85s ease}
.yd-page .yd-reveal.yd-visible{opacity:1;transform:translate3d(0,0,0) scale(1);filter:blur(0)}
.yd-progressFill{transform-origin:left center;transition:transform 1.4s cubic-bezier(.12,.82,.22,1);transition-delay:var(--yd-delay,0ms)}
/* Frosted team cards with a visible one-by-one sequence on EVERY entry. */
.yd-page .yd-teamGrid{direction:ltr;gap:clamp(12px,1.2vw,18px)}
.yd-page .yd-personCard{position:relative;background:linear-gradient(155deg,rgba(255,255,255,.77),rgba(221,240,236,.62));border:1px solid rgba(255,255,255,.87);box-shadow:0 16px 40px rgba(19,77,75,.12),inset 0 1px 2px rgba(255,255,255,.7);backdrop-filter:blur(22px) saturate(145%);-webkit-backdrop-filter:blur(22px) saturate(145%);opacity:0;transform:translate3d(0,55px,0) scale(.95);transition:opacity .68s ease,transform .68s cubic-bezier(.17,.85,.25,1),box-shadow .3s ease;transition-delay:0ms}
.yd-page.yd-dark .yd-personCard{background:linear-gradient(145deg,rgba(44,85,91,.72),rgba(9,37,46,.86));border-color:rgba(181,247,229,.23);box-shadow:0 14px 34px rgba(0,0,0,.25),inset 0 1px 1px rgba(255,255,255,.09)}
.yd-page .yd-teamGrid.yd-visible .yd-personCard{opacity:1;transform:translate3d(0,0,0) scale(1);transition-delay:calc(var(--yd-index) * 220ms)}
.yd-page .yd-teamGrid.yd-visible .yd-personCard:hover{transform:translateY(-7px) scale(1.015);transition-delay:0ms;box-shadow:0 22px 46px rgba(4,68,74,.24)}
.yd-page .yd-personArt{height:clamp(160px,22vh,202px);background-blend-mode:soft-light}
.yd-page .yd-personDetails{padding:15px 14px 18px;min-height:92px}
.yd-page .yd-personDetails h3{font-size:clamp(12px,1.05vw,15px);line-height:1.27;overflow-wrap:anywhere;min-height:2.55em;margin-bottom:8px}
.yd-page .yd-personDetails p{font-size:11px;line-height:1.4}
.yd-page .yd-personNumber{color:rgba(10,51,55,.7);background:rgba(255,255,255,.62);padding:5px 7px;border-radius:10px}
.yd-page .yd-personArtShine{background:linear-gradient(137deg,rgba(255,255,255,.24),transparent 65%)}
/* Maintain sane layouts with the topbar on tablets and phones. */
@media(max-width:1250px){.yd-navButton{flex-basis:83px;width:83px;min-width:83px;font-size:11px;gap:4px}.yd-navButton[data-nav="contact"]{flex-basis:100px;width:100px;min-width:100px}}
@media(max-width:1050px){.yd-nav{display:none}}
@media(max-width:720px){.yd-page .yd-mainSection{padding:100px 20px 68px}.yd-page .yd-aboutTop{grid-template-columns:1fr}.yd-page .yd-teamGrid{grid-template-columns:repeat(2,minmax(0,1fr))}.yd-page .yd-personDetails{padding:12px;min-height:105px}.yd-page .yd-personDetails h3{font-size:12px}.yd-page .yd-teamGrid.yd-visible .yd-personCard{transition-delay:calc(var(--yd-index) * 135ms)}.yd-page .yd-metrics{margin-top:20px}}
@media(prefers-reduced-motion:reduce){.yd-page .yd-reveal,.yd-page .yd-personCard{opacity:1!important;transform:none!important;filter:none!important;transition:none!important}.yd-progressFill{transform:scaleX(1)!important}}
/* Task 06: final visual polish only; scoped to /landing-lab. */
.yd-page{font-family:"Segoe UI",Arial,sans-serif;-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
.yd-page [dir="rtl"]{font-family:"Cairo","Segoe UI",Tahoma,sans-serif}
.yd-page .yd-heroOverlay{max-width:410px;padding:19px 22px 20px;border-radius:24px;border:1px solid rgba(220,255,247,.25);background:linear-gradient(140deg,rgba(8,34,43,.88),rgba(8,36,44,.73));box-shadow:0 14px 42px rgba(8,39,42,.28),inset 0 1px rgba(255,255,255,.10);backdrop-filter:blur(14px) saturate(120%);-webkit-backdrop-filter:blur(14px) saturate(120%)}
.yd-page .yd-heroOverlay h1{color:#f4fffd!important;text-shadow:0 3px 12px rgba(0,0,0,.25);font-weight:850;font-size:clamp(27px,2.7vw,39px);line-height:1.13;letter-spacing:-.035em;margin-bottom:10px}
.yd-page .yd-heroOverlay p{color:#d8eeeb!important;font-size:clamp(12px,1vw,14px);line-height:1.57}
.yd-page .yd-heroTag,.yd-page.yd-dark .yd-heroTag{color:#89ffe3!important;letter-spacing:.12em;font-size:10px}
.yd-page .yd-heroScroll{color:#0a3837!important;background:#92f0da!important;border-color:#b9fff0;padding:9px 14px;margin-top:13px;font-weight:850;box-shadow:0 8px 20px rgba(9,37,40,.18)}
.yd-page .yd-heroScroll:hover{transform:translateY(-2px)}
.yd-page .yd-mainSection{padding:clamp(106px,12vh,124px) clamp(20px,5vw,84px) clamp(28px,4vh,45px);min-height:100svh;scroll-margin-top:0;overflow:visible}
.yd-page .yd-sectionInner{max-width:1300px}
.yd-page .yd-sectionTitle{font-size:clamp(29px,3.0vw,43px);line-height:1.11;letter-spacing:-.042em;margin-bottom:11px;font-weight:850}
.yd-page .yd-sectionEyebrow{margin-bottom:10px;font-size:11px;letter-spacing:.12em}
.yd-page .yd-sectionLead{font-size:clamp(13px,1.05vw,15px);line-height:1.56;color:var(--yd-textMuted)}
.yd-page .yd-sectionSmall{font-size:12px;line-height:1.52;margin-top:10px}
.yd-page .yd-aboutTop{grid-template-columns:minmax(0,1.1fr) minmax(0,.9fr);gap:30px}
.yd-page .yd-aboutAccent{min-height:0;padding:8px;border-radius:23px}
.yd-page .yd-simImageWrap{height:clamp(170px,23vh,212px);min-height:0}
.yd-page .yd-metrics{margin-top:16px;padding:17px 21px 19px;border-radius:23px}
.yd-page .yd-metricsHead{margin-bottom:13px;gap:12px}
.yd-page .yd-metrics h3{font-size:clamp(17px,1.5vw,20px)}
.yd-page .yd-demoTag{padding:6px 11px;font-size:10px}
.yd-page .yd-progressRows{gap:16px}
.yd-page .yd-progressLabel{font-size:11px;margin-bottom:7px}
.yd-page .yd-progressTrack{height:9px}
.yd-page .yd-statGrid{gap:12px;margin-top:13px}
.yd-page .yd-statBox{padding:13px 17px;border-radius:15px}
.yd-page .yd-statBox p{font-size:11px;margin-top:3px}
.yd-page .yd-counter{font-size:clamp(24px,2vw,30px)}
.yd-page .yd-teamHeader{margin-bottom:16px;gap:14px}
.yd-page .yd-teamHeader .yd-sectionTitle{margin-bottom:6px}
.yd-page .yd-teamGrid{gap:12px}
.yd-page .yd-personCard{border-radius:18px;overflow:hidden}
.yd-page .yd-personArt{height:clamp(135px,17.4vh,170px)}
.yd-page .yd-personDetails{padding:12px 15px 12px;min-height:65px}
.yd-page .yd-personDetails h3{font-size:clamp(12px,.93vw,14px);line-height:1.17;min-height:0;margin-bottom:6px;font-weight:800}
.yd-page .yd-personDetails p{font-size:10.5px;line-height:1.3}
.yd-page .yd-teamPortrait{object-position:center 27%}
.yd-page .yd-photoPending{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;align-items:center;gap:11px;background:radial-gradient(circle at 50% 38%,rgba(255,255,255,.48),transparent 54%)}
.yd-page .yd-photoInitials{display:grid;place-items:center;width:76px;height:76px;border-radius:24px;font-size:30px;font-weight:850;color:#194b4c;background:rgba(255,255,255,.48);border:1px solid rgba(255,255,255,.6);box-shadow:0 10px 24px rgba(25,75,71,.12)}
.yd-page .yd-photoPending small{letter-spacing:.13em;font-size:9px;font-weight:800;color:rgba(22,71,71,.75)}
.yd-page .yd-personArtShine{pointer-events:none}
.yd-page .yd-personNumber{font-size:11px;padding:4px 7px}
.yd-page .yd-navButton,.yd-page .yd-authButton{letter-spacing:0;font-weight:750}
.yd-page .yd-teamSection{background:linear-gradient(180deg,var(--yd-bg2),var(--yd-bg2))}
/* When the viewport is short, content can scroll rather than clip beneath the taskbar. */
@media (max-height:760px) and (min-width:1051px){
  .yd-page .yd-mainSection{padding-top:100px;padding-bottom:30px}
  .yd-page .yd-simImageWrap{height:155px}
  .yd-page .yd-personArt{height:128px}
  .yd-page .yd-personDetails{padding:10px 13px;min-height:60px}
  .yd-page .yd-teamHeader{margin-bottom:13px}
  .yd-page .yd-metrics{padding:14px 18px;margin-top:12px}
}
@media (max-width:1050px){
  .yd-page .yd-mainSection{padding-top:105px;padding-bottom:42px}
  .yd-page .yd-teamGrid{grid-template-columns:repeat(2,minmax(0,1fr))}
  .yd-page .yd-personArt{height:190px}
  .yd-page .yd-aboutTop{gap:20px}
}
@media (max-width:720px){
  .yd-page .yd-mainSection{padding:92px 19px 46px}
  .yd-page .yd-heroOverlay{left:14px;right:14px;bottom:20px;padding:14px 16px;max-width:340px}
  .yd-page .yd-heroOverlay h1{font-size:28px}
  .yd-page .yd-aboutTop{grid-template-columns:1fr;gap:16px}
  .yd-page .yd-simImageWrap{height:185px}
  .yd-page .yd-progressRows,.yd-page .yd-statGrid{grid-template-columns:1fr}
  .yd-page .yd-teamGrid{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
  .yd-page .yd-personArt{height:165px}
  .yd-page .yd-personDetails{min-height:83px;padding:12px 10px}
  .yd-page .yd-metrics{margin-top:17px}
}
@media (prefers-reduced-motion:reduce){.yd-page .yd-heroScroll:hover{transform:none}}


.yd-fanFallback{position:absolute;inset:0;display:grid;place-items:center;font-size:46px;font-weight:900;letter-spacing:.06em;color:#baf5e7;background:linear-gradient(120deg,#123d49,#458f87)}
.yd-fanPhoto{position:relative;z-index:1}
/* Task 07: fanned 8-person deck; accessible via hover, click and keyboard. */
.yd-teamDeck{position:relative;width:100%;height:425px;isolation:isolate;margin:14px auto 0;perspective:1300px}
.yd-fanCard{position:absolute;left:50%;top:22px;width:clamp(160px,18vw,246px);height:318px;padding:0;border:1px solid rgba(164,242,227,.35);border-radius:22px;overflow:hidden;background:#163c43;box-shadow:0 24px 50px rgba(0,0,0,.30);opacity:0;cursor:pointer;text-align:left;
 transform:translateX(calc(-50% + var(--fan-x))) translateY(calc(var(--fan-y) + 60px)) rotate(var(--fan-rotation)) scale(.94);
 transition:transform .55s cubic-bezier(.18,1,.22,1), opacity .55s,filter .4s,box-shadow .4s;
 transition-delay:var(--fan-delay);z-index:var(--fan-z);transform-origin:50% 90%;}
.yd-teamDeck.yd-visible .yd-fanCard{opacity:1;transform:translateX(calc(-50% + var(--fan-x))) translateY(var(--fan-y)) rotate(var(--fan-rotation)) scale(1)}
.yd-teamDeck.yd-visible .yd-fanCard:is(:hover,:focus-visible,.yd-fanSelected){z-index:50;box-shadow:0 32px 72px rgba(0,0,0,.50),0 0 0 2px #7ef3db;transition-delay:0ms;transform:translateX(calc(-50% + var(--fan-x))) translateY(-28px) rotate(0deg) scale(1.16)}
.yd-teamDeck:has(.yd-fanSelected) .yd-fanCard:not(.yd-fanSelected){filter:brightness(.69) saturate(.76)}
.yd-fanPhoto{width:100%;height:100%;object-fit:cover;object-position:50% 25%;display:block}
.yd-fanCount{position:absolute;z-index:3;top:13px;left:13px;padding:5px 9px;border-radius:12px;color:white;background:rgba(10,40,47,.65);backdrop-filter:blur(8px);font-size:12px;font-weight:700;line-height:1.1}
.yd-fanInfo{position:absolute;z-index:2;inset:auto 0 0;padding:40px 15px 17px;color:#fff;background:linear-gradient(transparent,rgba(3,22,30,.72) 25%,rgba(3,22,30,.95));display:flex;flex-direction:column;gap:7px;transform:translateY(22px);transition:transform .33s ease}
.yd-fanCard:is(:hover,:focus-visible,.yd-fanSelected) .yd-fanInfo{transform:translateY(0)}
.yd-fanInfo strong{font-size:14px;line-height:1.22;text-wrap:balance;display:block;text-shadow:0 2px 10px #11252b}
.yd-fanInfo small{letter-spacing:.13em;font-size:9px;color:#91e8d7}
.yd-deckHint{position:absolute;bottom:2px;left:50%;transform:translateX(-50%);white-space:nowrap;font-size:12px;color:var(--yd-textMuted)}
.yd-teamSection .yd-sectionInner{max-width:1320px}
/* Cinematic Discover keeps the SAME existing canvas, never mounts a second WebGL context. */
.yd-page.yd-touring .yd-hero{position:fixed!important;inset:0!important;z-index:110!important;min-height:100dvh;height:100dvh}
.yd-page.yd-touring .yd-heroOverlay{display:none}
.yd-page.yd-touring .yd-topbar{opacity:0;pointer-events:none}
.yd-tourShade{position:fixed;inset:0;z-index:125;pointer-events:none;background:linear-gradient(90deg,rgba(2,17,23,.35),transparent 72%)}
.yd-guideShell{position:fixed;bottom:clamp(17px,3vw,32px);left:clamp(15px,3vw,43px);z-index:140;display:flex;align-items:flex-end;max-width:min(880px,94vw);pointer-events:none}
.yd-guideAvatar{width:clamp(112px,16vw,200px);height:auto;max-height:34vh;flex:none;filter:drop-shadow(0 18px 20px rgba(0,0,0,.28));animation:ydGuideBob 3s ease-in-out infinite;transform-origin:bottom}
@keyframes ydGuideBob{50%{transform:translateY(-8px)}}
.yd-guideSpeech{pointer-events:auto;position:relative;max-width:min(470px,57vw);min-width:270px;margin:0 0 40px -14px;padding:24px 25px 21px;border:1px solid rgba(202,255,242,.48);background:rgba(7,35,45,.86);backdrop-filter:blur(28px) saturate(150%);-webkit-backdrop-filter:blur(28px) saturate(150%);box-shadow:0 22px 60px rgba(0,0,0,.40),inset 0 1px rgba(255,255,255,.18);border-radius:24px;color:#ecfffa;animation:ydSpeechIn .45s both}
.yd-guideSpeech::before{content:'';position:absolute;left:-11px;bottom:28px;width:20px;height:20px;transform:rotate(45deg);background:rgba(7,35,45,.86);border-left:1px solid rgba(202,255,242,.48);border-bottom:1px solid rgba(202,255,242,.48)}
@keyframes ydSpeechIn{from{opacity:0;transform:translateY(16px) scale(.97)}to{opacity:1;transform:translateY(0) scale(1)}}
.yd-guideSpeech .yd-step{font-size:11px;color:#86e8d5;text-transform:uppercase;letter-spacing:.2em;font-weight:900}
.yd-guideSpeech h2{font-size:clamp(20px,2vw,28px);margin:9px 0 12px;line-height:1.17;color:#fff;font-weight:850}
.yd-guideSpeech p{font-size:14px;line-height:1.65;color:#cae5de;margin:0 0 18px}
.yd-guideActions{display:flex;gap:9px;flex-wrap:wrap}
.yd-guideActions button,.yd-guideActions a{display:inline-flex;align-items:center;justify-content:center;gap:9px;border:1px solid rgba(176,238,226,.35);border-radius:12px;padding:12px 15px;background:rgba(255,255,255,.09);color:#fff;font-size:13px;font-weight:800;text-decoration:none}
.yd-guideActions .yd-guidePrimary{background:#74eed3;color:#083934;border-color:#74eed3}
.yd-guideActions button:disabled{opacity:.5;cursor:not-allowed}
.yd-tourExit{position:fixed;z-index:150;top:28px;right:clamp(18px,4vw,65px);background:rgba(9,34,43,.85);color:#fff;border:1px solid rgba(255,255,255,.3);border-radius:99px;padding:10px 20px;backdrop-filter:blur(24px);font-weight:800}
.yd-tourScreenshot{position:fixed;z-index:130;right:clamp(18px,5vw,65px);top:14%;width:min(345px,28vw);padding:7px;background:rgba(4,27,36,.78);border:1px solid rgba(164,240,229,.5);border-radius:22px;box-shadow:0 18px 55px rgba(0,0,0,.4);backdrop-filter:blur(16px);animation:ydSpeechIn .55s both}
.yd-tourScreenshot img{display:block;width:100%;height:auto;border-radius:15px}.yd-tourScreenshot figcaption{color:#dafff6;font-size:11px;padding:7px 8px 4px}
/* Auth portal is intentionally a glass FRAME around the existing original auth routes. */
.yd-authBackdrop{position:fixed;inset:0;z-index:165;display:flex;align-items:center;justify-content:flex-end;padding:clamp(20px,5vw,80px);background:linear-gradient(110deg,rgba(3,22,29,.12),rgba(3,22,29,.52));backdrop-filter:blur(2px)}
.yd-authPortal{position:relative;max-width:100%;width:clamp(400px,46vw,680px);height:min(77dvh,690px);min-height:470px;border:1px solid rgba(231,255,252,.53);border-radius:28px;display:flex;flex-direction:column;overflow:hidden;color:white;background:rgba(8,39,48,.76);backdrop-filter:blur(26px) saturate(160%);-webkit-backdrop-filter:blur(26px) saturate(160%);box-shadow:0 35px 115px rgba(0,0,0,.55),inset 0 1px rgba(255,255,255,.3);animation:ydPortalIn .62s cubic-bezier(.18,1,.24,1) both}
@keyframes ydPortalIn{from{opacity:0;transform:translateX(90px) rotateY(-20deg) scale(.94)}to{opacity:1;transform:translateX(0) rotateY(0) scale(1)}}
.yd-authPortalHeader{display:flex;align-items:center;justify-content:space-between;gap:9px;padding:16px 20px;border-bottom:1px solid rgba(240,255,250,.2)}
.yd-authPortalHeader strong{font-size:14px}.yd-authPortalHeader button{border:1px solid rgba(255,255,255,.2);color:white;background:rgba(255,255,255,.1);border-radius:10px;padding:8px 10px;cursor:pointer}
.yd-authModes{display:flex;gap:5px;padding:6px;background:rgba(0,0,0,.15);border-radius:99px}
.yd-authModes button{border:0;background:transparent;color:#c3e5db;padding:8px 13px;border-radius:99px;min-width:66px}
.yd-authModes button.yd-authActive{background:#7debd5;color:#0a3c3e}
.yd-authFrame{border:0;flex:1;width:100%;background:#e9f5f1;animation:ydFrameFlip .46s ease both}
@keyframes ydFrameFlip{0%{opacity:0;transform:perspective(800px) rotateY(15deg) scale(.97)}100%{opacity:1;transform:rotateY(0) scale(1)}}
.yd-authPortalFooter{padding:12px 20px;color:#d6ede8;font-size:11px;display:flex;justify-content:space-between;align-items:center;gap:8px}
.yd-authPortalFooter a{color:#80f0d5;text-decoration:underline}
.yd-authToast{position:fixed;z-index:190;left:50%;top:50%;transform:translate(-50%,-50%);background:rgba(11,52,47,.94);border:2px solid #90f6e0;color:white;display:grid;place-items:center;border-radius:28px;padding:30px 45px;box-shadow:0 10px 70px #0008;animation:ydSpeechIn .35s both}
.yd-authToast span{font-size:55px;color:#8bffe0}
@media(max-width:1050px){.yd-teamDeck{height:390px}.yd-fanCard{height:280px}}
@media(max-width:1050px){.yd-teamDeck{display:flex;position:relative;overflow-x:auto;scroll-snap-type:x mandatory;gap:12px;align-items:center;height:315px;padding:8px 7px 22px;perspective:none}.yd-teamDeck .yd-fanCard,.yd-teamDeck.yd-visible .yd-fanCard,.yd-teamDeck.yd-visible .yd-fanCard:is(:hover,:focus-visible,.yd-fanSelected){position:relative;left:auto;top:auto;flex:0 0 185px;width:185px;height:250px;transform:none;opacity:1;scroll-snap-align:center}.yd-deckHint{display:none}.yd-guideAvatar{width:98px}.yd-guideShell{left:10px;right:10px;bottom:12px}.yd-guideSpeech{min-width:0;max-width:none;flex:1;margin:0 0 13px -8px;padding:17px}.yd-guideSpeech h2{font-size:17px}.yd-guideSpeech p{font-size:12px}.yd-guideActions button{padding:9px 12px}.yd-tourScreenshot{display:none}.yd-authBackdrop{justify-content:center;padding:10px}.yd-authPortal{width:100%;height:82dvh;min-height:400px}.yd-authPortalHeader{padding:11px}.yd-authPortalHeader strong{font-size:12px}.yd-authPortalFooter{font-size:10px}}
@media(prefers-reduced-motion:reduce){.yd-guideAvatar{animation:none}}

/* Task 08 guide: full-body doctor visual, lighter movement, no low-fidelity SVG. */
.yd-guideAvatar{width:clamp(148px,16vw,245px)!important;height:auto!important;max-height:56vh!important;object-fit:contain;object-position:bottom;transform-origin:bottom!important;filter:drop-shadow(0 20px 30px rgba(0,0,0,.35));animation:ydGuideBob 4.5s ease-in-out infinite!important}
.yd-guideShell{left:clamp(10px,2.1vw,32px);bottom:clamp(12px,2.3vw,32px);align-items:flex-end}
.yd-guideSpeech{margin-left:-12px;margin-bottom:46px;max-width:min(480px,55vw)}
.yd-page.yd-touring.yd-dark .yd-scene{filter:brightness(.88) saturate(.97) contrast(1.03)!important}
.yd-contactEmail{display:inline-block;color:var(--yd-strong)!important;font-weight:800;font-size:clamp(14px,1.2vw,18px);text-decoration:underline!important;text-underline-offset:5px;overflow-wrap:anywhere}
.yd-emailFallback{display:inline-flex;align-items:center;margin-top:11px;padding:7px 12px;border-radius:12px;background:var(--yd-bg2);border:1px solid var(--yd-border);font-size:12px;font-weight:750;color:var(--yd-strong)}
.yd-formStatus{color:var(--yd-text);padding:9px 11px;border:1px solid var(--yd-border);border-radius:10px;background:var(--yd-bg2);margin-top:12px;font-size:12px;line-height:1.5}
.yd-formStatus.ok{color:#51d9b9;border-color:#43bb9a}
.yd-honey{position:absolute!important;left:-10000px!important;opacity:0!important;pointer-events:none!important}
@media(max-width:800px){.yd-guideAvatar{width:clamp(100px,18vw,155px)!important;max-height:30vh!important}.yd-guideSpeech{margin-bottom:13px;max-width:76vw}}
`;

export default function LandingLabPage() {
  const [locale, setLocale] = useState<Locale>("en");
  const [theme, setTheme] = useState<Theme>("dark");
  const [active, setActive] = useState<NavId>("home");
  const [flip, setFlip] = useState(false);
  const [themeAnimation, setThemeAnimation] = useState<"sun" | "moon" | null>(null);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [pill, setPill] = useState({ x: 0, width: 90 });
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [contactStatus, setContactStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [contactError, setContactError] = useState("");
  const [honeypot, setHoneypot] = useState("");
  const [tour, setTour] = useState<TourStep>("closed");
  const [authMode, setAuthMode] = useState<AuthMode | null>(null);
  const navRef = useRef<HTMLElement>(null);
  const timers = useRef<number[]>([]);
  const t = dictionary[locale];

  const schedule = (handler: () => void, delay: number) => { timers.current.push(window.setTimeout(handler, delay)); };

  useEffect(() => () => { timers.current.forEach(clearTimeout); }, []);

  useEffect(() => {
    const nodes = document.querySelectorAll<HTMLElement>(".yd-reveal, .yd-teamDeck");
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        // Remove when leaving, allowing every new scroll through the section to replay.
        entry.target.classList.toggle("yd-visible", entry.isIntersecting);
      });
    }, { threshold: 0.12, rootMargin: "-88px 0px -45px 0px" });
    nodes.forEach(node => observer.observe(node));
    return () => observer.disconnect();
  }, [locale]);

  useEffect(() => {
    const nodes = ["home", "about", "team", "contact"].map(id => document.getElementById(id)).filter(Boolean) as HTMLElement[];
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => { if (entry.isIntersecting) setActive(entry.target.id as NavId); });
    }, { rootMargin: "-20% 0px -48% 0px", threshold: 0 });
    nodes.forEach(node => observer.observe(node));
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const update = () => {
      const nav = navRef.current;
      const btn = nav?.querySelector<HTMLButtonElement>(`[data-nav="${active}"]`);
      if (nav && btn) setPill({ x: btn.offsetLeft, width: btn.offsetWidth });
    };
    update();
    const observer = new ResizeObserver(update);
    if (navRef.current) observer.observe(navRef.current);
    window.addEventListener("resize", update);
    return () => { observer.disconnect(); window.removeEventListener("resize", update); };
  }, [active, locale]);

  const startTour = () => {
    setAuthMode(null);
    setTour("welcome");
    window.scrollTo({ top: 0, behavior: "auto" });
  };
  const openAuth = (mode: Exclude<AuthMode, null>) => {
    setTour("closed");
    setAuthMode(mode);
    window.scrollTo({ top: 0, behavior: "auto" });
  };
  const closeTour = () => { setTour("closed"); setAuthMode(null); };
  // Deep links used by /login and /sign-up: open the same glass form on the Landing.
  // Run only in the browser, and preserve unrelated query parameters.
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const requested = params.get("auth");
    if (requested !== "login" && requested !== "signup") return;
    const timer = window.setTimeout(() => {
      setTour("closed");
      setAuthMode(requested);
      window.scrollTo({ top: 0, behavior: "auto" });
      params.delete("auth");
      const suffix = params.toString();
      const nextUrl = `${window.location.pathname}${suffix ? `?${suffix}` : ""}${window.location.hash}`;
      window.history.replaceState(window.history.state, "", nextUrl);
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (tour === "closed" && !authMode) return;
    const before = document.documentElement.style.overflow;
    document.documentElement.style.overflow = "hidden";
    return () => { document.documentElement.style.overflow = before; };
  }, [tour, authMode]);
  const navigate = (id: NavId) => {
    if (id === "discover") { setMobileOpen(false); startTour(); return; }
    setMobileOpen(false);
    setActive(id);
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    document.getElementById(id)?.scrollIntoView({ behavior: reduced ? "auto" : "smooth", block: "start" });
  };

  const toggleLanguage = () => {
    if (flip) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) { setLocale(v => v === "ar" ? "en" : "ar"); return; }
    setFlip(true);
    schedule(() => setLocale(v => v === "ar" ? "en" : "ar"), 150);
    schedule(() => setFlip(false), 490);
  };

  const toggleTheme = () => {
    if (themeAnimation) return;
    const next: Theme = theme === "light" ? "dark" : "light";
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) { setTheme(next); return; }
    setThemeAnimation(next === "light" ? "sun" : "moon");
    schedule(() => setTheme(next), 210);
    schedule(() => setThemeAnimation(null), 780);
  };

  const sendContact = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (contactStatus === "sending") return;
    setContactStatus("sending");
    setContactError("");
    try {
      const response = await fetch("/api/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, message, website: honeypot }),
      });
      const result: { error?: string; ok?: boolean } = await response.json();
      if (!response.ok || !result.ok) throw new Error(result.error || "Could not send message.");
      setContactStatus("sent");
      setName(""); setEmail(""); setMessage("");
    } catch (error) {
      setContactStatus("error");
      setContactError(error instanceof Error ? error.message : "Could not send message.");
    }
  };
  const contactMailto = `mailto:yaadok.2027@gmail.com?subject=${encodeURIComponent(`YA-DOK Contact from ${name.trim()}`)}&body=${encodeURIComponent(`Name: ${name.trim()}\nEmail: ${email.trim()}\n\n${message.trim()}`)}`;

  return (
    <main className={`yd-page${theme === "dark" ? " yd-dark" : ""}${tour !== "closed" || authMode ? " yd-touring" : ""}`} dir="ltr" lang={locale}>
      <style>{CSS}</style>
      <header className="yd-topbar">
        <a className="yd-brand" href="#home" onClick={event => { event.preventDefault(); navigate("home"); }} aria-label="YA-DOK Home">
          {/* Existing asset already used by the current Authentication page. */}
          <img src="/brand/yadok-logo.png" alt="YA-DOK" width={94} height={42} />
        </a>
        <nav className="yd-nav" ref={navRef} aria-label="Primary navigation">
          <span className="yd-navPill" aria-hidden="true" style={{ width: pill.width, transform: `translateX(${pill.x}px)` }} />
          {navIds.map(id => <button key={id} type="button" data-nav={id} className={`yd-navButton${active === id ? " yd-selected" : ""}`} onClick={() => navigate(id)} aria-current={active === id ? "page" : undefined}><Glyph name={id} size={16}/><span>{t[id]}</span></button>)}
        </nav>
        <div className="yd-actions">
          <button type="button" className="yd-langSwitch" onClick={toggleLanguage} disabled={flip} aria-label={locale === "ar" ? "Switch to English" : "التبديل إلى العربية"}><span className="yd-langThumb" style={{transform:locale === "ar" ? "translateX(0)" : "translateX(100%)"}} aria-hidden="true"/><span className={locale === "ar" ? "yd-langActive" : ""}>ع</span><span className={locale === "en" ? "yd-langActive" : ""}>EN</span></button>
          <button type="button" className="yd-iconButton" onClick={toggleTheme} disabled={themeAnimation !== null} title={t.mode} aria-label={t.mode}><Glyph name={theme === "light" ? "moon" : "sun"} size={20}/></button>
          <button className="yd-authButton yd-login" type="button" onClick={() => openAuth("login")}>{t.login}</button>
          <button className="yd-authButton yd-primary" type="button" onClick={() => openAuth("signup")}>{t.signup}</button>
          <button type="button" className="yd-iconButton yd-mobileButton" onClick={() => setMobileOpen(v => !v)} aria-label={t.menu}><Glyph name={mobileOpen ? "close" : "menu"} size={19}/></button>
        </div>
      </header>

      {mobileOpen && <nav className="yd-mobileMenu" aria-label="Mobile navigation">{navIds.map(id => <button key={id} className={active === id ? "yd-selected" : ""} type="button" onClick={() => navigate(id)}>{t[id]}</button>)}</nav>}

      <section className="yd-hero" id="home" aria-label="YA-DOK 3D Clinic">
        <div className="yd-scene"><ClinicalWorld focus={authMode ? "reception" : tour === "doctor" ? "doctor" : tour === "paper" ? "paper" : "overview"} onSceneClick={tour === "closed" && !authMode ? startTour : undefined}/></div>
        <div className="yd-heroOverlay" dir={locale === "ar" ? "rtl" : "ltr"}>
          <span className="yd-heroTag"><span className="yd-heroDot"/>{t.heroTag}</span>
          <h1>{t.heroTitle}</h1>
          <p>{t.heroText}</p>
          <button className="yd-heroScroll" type="button" onClick={() => navigate("about")}>{t.heroScroll}<Glyph name="down" size={15}/></button>
        </div>
      </section>

      <section className="yd-mainSection" id="about">
        <div className="yd-sectionInner">
          <div className="yd-aboutTop">
            <div className="yd-reveal" dir={locale === "ar" ? "rtl" : "ltr"}><span className="yd-sectionEyebrow">{t.section01}</span><h2 className="yd-sectionTitle">{t.aboutTitle}</h2><p className="yd-sectionLead">{t.aboutText}</p><p className="yd-sectionSmall">{t.aboutSecondary}</p></div>
            <div className="yd-aboutAccent yd-reveal">
              <div className="yd-simImageWrap"><img src="/brand/clinical-simulation.webp" alt={locale === "ar" ? "تصور بصري لطالب طب يتدرب على مريض افتراضي باستخدام منصة محاكاة" : "Illustration of a medical student interacting with an AI virtual patient"} loading="lazy" />
                <span className="yd-simLive"><span className="yd-liveDot"/>{locale === "ar" ? "محاكاة تفاعلية" : "Virtual simulation"}</span>
              </div>
              <div className="yd-simCaption">AI PATIENT SIMULATION <Glyph name="spark" size={16}/></div>
            </div>
          </div>
          <div className="yd-metrics yd-reveal">
            <div className="yd-metricsHead" dir={locale === "ar" ? "rtl" : "ltr"}><h3>{t.progressTitle}</h3><span className="yd-demoTag">{t.sample}</span></div>
            <div className="yd-progressRows" dir={locale === "ar" ? "rtl" : "ltr"}>
              {[85, 72, 93].map((value, i) => <div key={value}><div className="yd-progressLabel"><span>{t.progress[i]}</span><span>{value}%</span></div><div className="yd-progressTrack"><span className="yd-progressFill" style={{ width: `${value}%`, "--yd-delay": `${i * 120}ms` } as CSSProperties}/></div></div>)}
            </div>
            <div className="yd-statGrid" dir={locale === "ar" ? "rtl" : "ltr"}>{[1200, 2400, 48].map((n, i) => <div className="yd-statBox" key={n}><DemoCounter target={n}/><p>{t.counts[i]}</p></div>)}</div>
          </div>
        </div>
      </section>

      <section className="yd-mainSection yd-teamSection" id="team">
        <div className="yd-sectionInner">
          <div className="yd-teamHeader yd-reveal"><div dir={locale === "ar" ? "rtl" : "ltr"}><span className="yd-sectionEyebrow">{t.section02}</span><h2 className="yd-sectionTitle">{t.teamTitle}</h2><p className="yd-sectionLead">{t.teamText}</p></div><span className="yd-demoTag">8 {locale === "ar" ? "أعضاء" : "members"}</span></div>
          <TeamDeck locale={locale}/>
        </div>
      </section>

      <section className="yd-mainSection" id="contact">
        <div className="yd-sectionInner yd-contactLayout">
          <div className="yd-reveal" dir={locale === "ar" ? "rtl" : "ltr"}>
            <span className="yd-sectionEyebrow">{t.section03}</span><h2 className="yd-sectionTitle">{t.contactTitle}</h2><p className="yd-sectionLead">{t.contactText}</p>
            <div className="yd-contactInfo"><h3><Glyph name="mail" size={19}/> {t.contactInfo}</h3><a className="yd-contactEmail" href="mailto:yaadok.2027@gmail.com">yaadok.2027@gmail.com</a></div>
          </div>
          <form className="yd-contactForm yd-reveal" dir={locale === "ar" ? "rtl" : "ltr"} onSubmit={sendContact}>
            <h3>{locale === "ar" ? "ابعت رسالتك" : "Send a message"}</h3>
            <label className="yd-field"><span>{t.name}</span><input required minLength={2} maxLength={120} autoComplete="name" value={name} onChange={e => setName(e.target.value)} placeholder={t.namePlaceholder}/></label>
            <label className="yd-field"><span>{t.email}</span><input required type="email" autoComplete="email" value={email} onChange={e => setEmail(e.target.value)} placeholder={t.emailPlaceholder}/></label>
            <label className="yd-field"><span>{t.message}</span><textarea required minLength={10} maxLength={3000} value={message} onChange={e => setMessage(e.target.value)} placeholder={t.messagePlaceholder}/></label>
            <label className="yd-honey" aria-hidden="true">Website<input tabIndex={-1} value={honeypot} onChange={e=>setHoneypot(e.target.value)} autoComplete="off"/></label>
            <button className="yd-copyButton" type="submit" disabled={contactStatus === "sending"}>{contactStatus === "sending" ? (locale === "ar" ? "جاري الإرسال..." : "Sending...") : (locale === "ar" ? "إرسال الرسالة" : "Send message")} <Glyph name="arrow" size={16}/></button>
            <p className="yd-contactHint">{locale === "ar" ? "عند تفعيل خدمة البريد، الرسالة هتتبعت لإيميل الفريق؛ مش بتتخزن في لوحة أدمن." : "Email delivery goes to the team's inbox once configured; it is not saved to an admin dashboard."}</p>
            {contactStatus === "sent" && <p className="yd-formStatus ok" role="status">{locale === "ar" ? "تم إرسال الرسالة بنجاح." : "Your message was sent successfully."}</p>}
            {contactStatus === "error" && <p className="yd-formStatus" role="alert">{contactError} <a className="yd-emailFallback" href={contactMailto}>{locale === "ar" ? "افتح برنامج الإيميل لإرسالها" : "Open email app instead"}</a></p>}
          </form>
        </div>
      </section>
      {tour !== "closed" && !authMode && <>
        <div className="yd-tourShade" aria-hidden="true" />
        <button type="button" className="yd-tourExit" onClick={closeTour}>{tourText[locale].close} ✕</button>
        {tour === "doctor" && <figure className="yd-tourScreenshot"><img src="/brand/clinical-simulation.webp" alt="Concept image of student talking to a virtual patient"/><figcaption>{locale === "ar" ? "تصور بصري للمحاكاة — مش لقطة من السيستم" : "Simulation concept — illustrative preview"}</figcaption></figure>}
        <div className="yd-guideShell" dir={locale === "ar" ? "rtl" : "ltr"}>
          <GuideAvatar/>
          <div key={tour} className="yd-guideSpeech" role="status" aria-live="polite">
            <span className="yd-step">YA-DOK 3D EXPERIENCE · {tour === "welcome" ? "01" : tour === "doctor" ? "02" : tour === "paper" ? "03" : "04"}/04</span>
            <h2>{tour === "welcome" ? tourText[locale].introTitle : tour === "doctor" ? tourText[locale].doctorTitle : tour === "paper" ? tourText[locale].paperTitle : tourText[locale].finishTitle}</h2>
            <p>{tour === "welcome" ? tourText[locale].intro : tour === "doctor" ? tourText[locale].doctor : tour === "paper" ? tourText[locale].paper : tourText[locale].finish}</p>
            <div className="yd-guideActions">
              {tour === "welcome" && <><button className="yd-guidePrimary" onClick={() => setTour("doctor")}>{tourText[locale].tour3d} →</button><button disabled title={tourText[locale].soon}>{tourText[locale].demo} · {tourText[locale].soon}</button></>}
              {tour === "doctor" && <><button onClick={() => setTour("welcome")}>{tourText[locale].back}</button><button className="yd-guidePrimary" onClick={() => setTour("paper")}>{tourText[locale].next} →</button></>}
              {tour === "paper" && <><button onClick={() => setTour("doctor")}>{tourText[locale].back}</button><button className="yd-guidePrimary" onClick={() => setTour("finish")}>{tourText[locale].next} →</button></>}
              {tour === "finish" && <><button className="yd-guidePrimary" onClick={() => openAuth("signup")}>{tourText[locale].start} →</button><button onClick={() => openAuth("login")}>{tourText[locale].login}</button></>}
            </div>
          </div>
        </div>
      </>}
      {authMode && <GlassAuthPortal mode={authMode} locale={locale} onModeChange={setAuthMode} onClose={closeTour} />}
      <footer className="yd-footer" dir={locale === "ar" ? "rtl" : "ltr"}>© YA-DOK · {t.footer}</footer>
      {flip && <div className="yd-languageWave" aria-hidden="true"><span>{locale === "ar" ? "عربي  /  English" : "English  /  عربي"}</span></div>}
      {themeAnimation && <div className={`yd-themeCurtain${themeAnimation === "moon" ? " yd-showMoon" : ""}`} aria-hidden="true"><span className="yd-themeSymbol"><Glyph name={themeAnimation} size={68}/></span></div>}
    </main>
  );
}
