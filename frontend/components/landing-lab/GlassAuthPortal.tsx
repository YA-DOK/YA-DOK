"use client";

import { createBrowserClient } from "@supabase/ssr";
import Image from "next/image";
import { AuthOutcome } from "./AuthOutcome";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";

export type AuthMode = "login" | "signup";
type Locale = "en" | "ar";
type PageMode = AuthMode | "recover";
type Notice = { kind: "success" | "error"; message: string } | null;

const text = {
  en: {
    tagline: "YOUR CLINICAL JOURNEY STARTS HERE",
    login: "Log in", signup: "Sign up", hello: "Welcome back.", join: "Your journey starts here.",
    helloSub: "Return to your clinical training space.",
    joinSub: "Create your account and start practicing with YA-DOK.",
    name: "Full name", namePh: "Your full name", email: "Email address", emailPh: "you@example.com",
    password: "Password", passwordPh: "At least 8 characters", confirm: "Confirm password",
    forgot: "Forgot password?", recoverTitle: "Reset your password.",
    recoverSub: "We'll email you a secure link to reset your password.", sendLink: "Send reset link",
    back: "Back to login", create: "Create account", enter: "Log in to YA-DOK", loading: "Please wait...",
    or: "or continue with", google: "Continue with Google", have: "Already have an account?",
    new: "New here?", secure: "Protected by secure authentication", show: "Show password", hide: "Hide password",
    minimum: "Use at least 8 characters.", mismatch: "Passwords don't match.", enterName: "Please enter your full name.",
    missing: "Supabase public settings are missing.", generic: "Something went wrong. Please try again.",
    mailSent: "If this email can receive a recovery message, a reset link will be sent.",
    confirmMail: "Account request received. Check your email for confirmation, then log in.",
    signedIn: "Welcome back!", signedUp: "Account created!", busyGoogle: "Connecting to Google...",
    passwordStrength: "Password length", cross: "Close", cannotGoogle: "Google sign-in could not be started.",
    closeNotice: "Dismiss notice",
  },
  ar: {
    tagline: "رحلتك الإكلينيكية بتبدأ من هنا",
    login: "تسجيل الدخول", signup: "إنشاء حساب", hello: "أهلًا برجوعك.", join: "رحلتك بتبدأ هنا.",
    helloSub: "كمّل تدريبك في مساحة يادوك الإكلينيكية.",
    joinSub: "أنشئ حساب وابدأ التدريب على الحالات مع YA-DOK.",
    name: "الاسم الكامل", namePh: "اكتب اسمك بالكامل", email: "البريد الإلكتروني", emailPh: "you@example.com",
    password: "كلمة المرور", passwordPh: "8 أحرف على الأقل", confirm: "تأكيد كلمة المرور",
    forgot: "نسيت كلمة المرور؟", recoverTitle: "استعادة كلمة المرور.",
    recoverSub: "هنبعتلك رابط آمن على الإيميل علشان تغيّر كلمة المرور.", sendLink: "إرسال رابط الاستعادة",
    back: "الرجوع لتسجيل الدخول", create: "إنشاء حساب", enter: "دخول إلى YA-DOK", loading: "لحظة واحدة...",
    or: "أو استخدم", google: "المتابعة باستخدام Google", have: "عندك حساب بالفعل؟",
    new: "معندكش حساب؟", secure: "تسجيل الدخول محمي وآمن", show: "إظهار كلمة المرور", hide: "إخفاء كلمة المرور",
    minimum: "استخدم 8 أحرف على الأقل.", mismatch: "كلمتا المرور مش متطابقتين.", enterName: "اكتب اسمك الكامل.",
    missing: "إعدادات Supabase العامة غير موجودة.", generic: "حصلت مشكلة. حاول تاني.",
    mailSent: "لو الإيميل متاح للاستعادة، هيوصلك رابط تغيير كلمة المرور.",
    confirmMail: "تم استقبال طلب التسجيل. راجع إيميلك للتأكيد وبعدها سجل دخول.",
    signedIn: "أهلًا برجوعك!", signedUp: "تم إنشاء الحساب!", busyGoogle: "جاري التوصيل بجوجل...",
    passwordStrength: "طول كلمة المرور", cross: "إغلاق", cannotGoogle: "تعذّر بدء تسجيل الدخول بجوجل.",
    closeNotice: "إغلاق التنبيه",
  },
} as const;

const styles = `
.ya9-shade{position:fixed;inset:0;z-index:180;display:flex;justify-content:flex-end;align-items:center;padding:clamp(14px,5.4vw,82px);background:linear-gradient(90deg,rgba(2,20,27,.02) 4%,rgba(1,20,28,.10) 43%,rgba(2,18,29,.42));animation:ya9-in .38s ease-out both}
@keyframes ya9-in{from{opacity:0}to{opacity:1}}
.ya9-card{position:relative;isolation:isolate;width:min(485px,100%);max-height:calc(100dvh - 32px);overflow-x:hidden;overflow-y:auto;overscroll-behavior:contain;scrollbar-width:thin;scrollbar-color:#73b7ad transparent;border:1px solid rgba(191,250,236,.40);border-radius:28px;padding:clamp(22px,2.6vw,34px);color:#f4fffc;background:linear-gradient(135deg,rgba(6,34,44,.89),rgba(13,51,61,.76) 60%,rgba(15,53,52,.80));box-shadow:0 35px 100px rgba(3,22,28,.38),inset 0 1px rgba(255,255,255,.22);backdrop-filter:blur(23px) saturate(165%);-webkit-backdrop-filter:blur(23px) saturate(165%);animation:ya9-enter .62s cubic-bezier(.2,1,.25,1) both}
@keyframes ya9-enter{from{opacity:0;transform:translateX(65px) scale(.97)}to{opacity:1;transform:translateX(0) scale(1)}}
.ya9-card:before{content:"";z-index:-1;pointer-events:none;position:absolute;inset:0;background:radial-gradient(ellipse at 95% 3%,rgba(135,255,223,.18),transparent 48%)}
.ya9-top{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:24px}
.ya9-brand{display:flex;align-items:center;gap:12px;font-weight:850;font-size:15px;letter-spacing:.08em}
.ya9-logo{display:grid;place-items:center;width:51px;height:43px;padding:6px;border-radius:13px;background:#f7fffaf3;box-shadow:0 6px 28px #0004}
.ya9-close{width:35px;height:35px;border-radius:12px;display:grid;place-items:center;border:1px solid #e7ffff4b;color:#edfdf9;background:#ffffff0b;cursor:pointer;font-size:22px;transition:background .2s,transform .2s}
.ya9-close:hover{background:#ffffff24;transform:rotate(90deg)}
.ya9-eyebrow{font-size:10px;font-weight:800;letter-spacing:.21em;color:#9bfce4;margin:0 0 10px}
.ya9-title{font-size:clamp(29px,3.2vw,38px);font-weight:850;letter-spacing:-.035em;line-height:1.16;color:white;margin:0 0 9px}
.ya9-sub{font-size:13px;line-height:1.55;color:#cce5df;margin:0 0 24px}
.ya9-switch{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:5px;padding:5px;border:1px solid #d4ffef38;background:#031e287a;border-radius:15px;margin-bottom:23px;direction:ltr}
.ya9-switch button{position:relative;isolation:isolate;border:none;border-radius:11px;background:transparent;color:#cae2df;cursor:pointer;font:inherit;font-size:13px;font-weight:750;padding:11px 8px;transition:color .25s}
.ya9-switch button[aria-selected=true]{color:#07332e}
.ya9-switch button[aria-selected=true]:before{content:"";position:absolute;inset:0;z-index:-1;border-radius:11px;background:linear-gradient(120deg,#91f5d9,#6ce1d1);box-shadow:0 3px 14px #49d8bb4a;animation:ya9-pill .32s cubic-bezier(.2,1.1,.22,1) both}
@keyframes ya9-pill{from{opacity:.6;transform:scaleX(.72)}to{opacity:1;transform:scaleX(1)}}
.ya9-stage{position:relative;animation:ya9-stage .42s cubic-bezier(.22,1,.25,1) both}
@keyframes ya9-stage{from{opacity:0;transform:perspective(900px) rotateY(-11deg) translateY(9px)}to{opacity:1;transform:perspective(900px) rotateY(0deg) translateY(0)}}
.ya9-mask{position:absolute;inset:4px 0 0;z-index:20;pointer-events:none;display:grid;place-items:center;border:1px solid #a4ffe244;border-radius:18px;background:linear-gradient(140deg,#0b4448,#0b7471);animation:ya9-transform .50s ease both}
.ya9-mask span{font-size:26px;font-weight:900;letter-spacing:.12em;color:#d9fff2;text-shadow:0 0 24px #b4ffdf80}
@keyframes ya9-transform{0%{opacity:0;transform:perspective(700px) rotateY(-80deg) scale(.94)}35%{opacity:1;transform:perspective(700px) rotateY(0) scale(1)}65%{opacity:1;transform:perspective(700px) rotateY(0)}100%{opacity:0;transform:perspective(700px) rotateY(80deg) scale(.94)}}
.ya9-label{display:block;margin-bottom:15px;color:#ddf4ed;text-align:start}
.ya9-labelText{display:block;font-size:12px;font-weight:700;margin-bottom:7px}
.ya9-inputWrap{position:relative}
.ya9-input{box-sizing:border-box;width:100%;height:47px;min-width:0;border:1px solid #d0ffef4b;border-radius:13px;outline:none;background:#ffffff12;color:white;font:inherit;font-size:13px;padding:0 15px;transition:background .2s,border .2s,box-shadow .2s}
.ya9-input:focus{border-color:#93f9de;background:#ffffff22;box-shadow:0 0 0 3px #66ddc71f}
.ya9-input::placeholder{color:#d8eee0a0}
.ya9-withEye{padding-inline-end:58px}
.ya9-eye{position:absolute;inset-inline-end:4px;top:4px;height:39px;min-width:45px;display:grid;place-items:center;background:none;color:#cfe7e2;border:none;cursor:pointer}
.ya9-eye:hover{color:#93f9de}
.ya9-strength{display:flex;gap:5px;margin-top:7px;direction:ltr}
.ya9-strength span{height:3px;border-radius:9px;flex:1;background:#ffffff2b;transition:background .2s}
.ya9-strength span.strong{background:#86f6dc}
.ya9-tools{display:flex;justify-content:flex-end;margin:-1px 0 17px}
.ya9-link{background:none;border:none;padding:0;color:#9cf9df;font:inherit;font-size:12px;cursor:pointer;text-decoration:none}
.ya9-submit{width:100%;min-height:49px;display:flex;align-items:center;justify-content:center;gap:10px;background:linear-gradient(105deg,#9df9e3,#69e1c9);color:#0c3834;border:0;border-radius:13px;cursor:pointer;font:inherit;font-size:14px;font-weight:850;box-shadow:0 9px 22px #30dab13b;transition:transform .2s,filter .2s}
.ya9-submit:hover:not(:disabled){transform:translateY(-2px);filter:brightness(1.06)}.ya9-submit:disabled{opacity:.65;cursor:wait}
.ya9-spinner{width:15px;height:15px;border:2px solid #0a534c66;border-top-color:#05342b;border-radius:50%;animation:ya9-spin .7s linear infinite}
@keyframes ya9-spin{to{transform:rotate(360deg)}}
.ya9-or{display:flex;align-items:center;gap:12px;margin:18px 0 16px;color:#c3ddd4;font-size:11px}
.ya9-or:before,.ya9-or:after{content:"";height:1px;background:#e7fffc38;flex:1}
.ya9-google{width:100%;border:1px solid #ddfcf64d;background:#f8fffeeb;min-height:48px;border-radius:13px;display:flex;align-items:center;justify-content:center;gap:12px;color:#183c40;cursor:pointer;font:inherit;font-size:13px;font-weight:750;transition:transform .2s,background .2s}
.ya9-google:hover:not(:disabled){transform:translateY(-2px);background:white}.ya9-google:disabled{opacity:.65;cursor:wait}
.ya9-foot{text-align:center;margin:18px 0 0;font-size:12px;color:#d0e6e0}.ya9-foot button{border:0;background:transparent;color:#a2fce3;font-weight:800;font:inherit;cursor:pointer;padding:0 5px}
.ya9-secure{margin-top:19px;display:flex;align-items:center;gap:8px;justify-content:center;color:#b9dcd3;font-size:11px}
.ya9-notice{border:1px solid #ffb8b880;border-radius:11px;background:#8d24244a;color:#fff1f1;font-size:12px;padding:11px 12px;margin-bottom:15px;line-height:1.6}
.ya9-notice[data-kind=success]{color:#e7fff8;background:#0e785044;border-color:#8eeeca99}
.ya9-toast{position:fixed;inset:0;z-index:200;pointer-events:none;display:grid;place-items:center;background:#031b2263;animation:ya9-in .18s both}
.ya9-toastPanel{border:1px solid #9bf5db;border-radius:24px;background:#073932ef;color:white;box-shadow:0 25px 90px #0008;text-align:center;padding:27px 42px;animation:ya9-pop .35s both;font-weight:800}
.ya9-toastPanel[data-kind=error]{background:#51232aee;border-color:#ff9fa5}
.ya9-toastSymbol{display:block;font-size:52px;line-height:1.1;color:#a5ffe1;margin-bottom:9px}
.ya9-toastPanel[data-kind=error] .ya9-toastSymbol{color:#ffbdc2}
@keyframes ya9-pop{from{opacity:0;transform:translateY(18px) scale(.8)}to{opacity:1;transform:translateY(0) scale(1)}}
.ya9-card :focus-visible{outline:2px solid #9bffdc;outline-offset:3px}
@media(max-width:650px){.ya9-shade{padding:9px;justify-content:center;background:rgba(2,20,27,.55)}.ya9-card{max-height:94dvh;padding:22px;border-radius:22px}.ya9-top{margin-bottom:16px}.ya9-sub{margin-bottom:18px}}
@media(prefers-reduced-motion:reduce){.ya9-card,.ya9-stage,.ya9-mask,.ya9-toast,.ya9-toastPanel,.ya9-switch button[aria-selected=true]:before{animation:none!important;transition:none!important}}
`;

function GoogleMark() {
  return <svg width="21" height="21" viewBox="0 0 48 48" aria-hidden="true" focusable="false">
    <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.37 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5Z"/>
    <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6C44.4 38.03 46.98 31.88 46.98 24.55Z"/>
    <path fill="#FBBC05" d="M10.53 28.59A14.4 14.4 0 0 1 9.75 24c0-1.6.28-3.15.77-4.59l-7.98-6.2A23.9 23.9 0 0 0 0 24c0 3.87.93 7.52 2.56 10.78l7.97-6.19Z"/>
    <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.8l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.23-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48Z"/>
  </svg>;
}

function PasswordField({ label, placeholder, value, onChange, visible, setVisible, complete, t }: {
  label: string; placeholder: string; value: string; onChange: (v: string) => void;
  visible: boolean; setVisible: (v: boolean) => void; complete?: string;
  t: typeof text.en | typeof text.ar;
}) {
  return <label className="ya9-label">
    <span className="ya9-labelText">{label}</span>
    <span className="ya9-inputWrap" style={{ display: "block" }}>
      <input className="ya9-input ya9-withEye" type={visible ? "text" : "password"} placeholder={placeholder}
        autoComplete={complete} required minLength={8} value={value} onChange={e => onChange(e.target.value)} />
      <button type="button" className="ya9-eye" onClick={() => setVisible(!visible)} aria-label={visible ? t.hide : t.show} aria-pressed={visible}>
        {visible ? "◉" : "◎"}
      </button>
    </span>
  </label>;
}

export function GlassAuthPortal({ mode, locale, onModeChange, onClose }: {
  mode: AuthMode;
  locale: Locale;
  onModeChange: (mode: AuthMode) => void;
  onClose: () => void;
}) {
  const router = useRouter();
  const t = text[locale];
  const [view, setView] = useState<PageMode>(mode);
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [busy, setBusy] = useState(false);
  const [flip, setFlip] = useState(false);
  const [notice, setNotice] = useState<Notice>(null);
  const [toast, setToast] = useState<Notice>(null);
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);

  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  const supabase = useMemo(() => url && key ? createBrowserClient(url, key) : null, [url, key]);

  useEffect(() => {
    function onEsc(event: KeyboardEvent) { if (event.key === "Escape" && !busy) onClose(); }
    window.addEventListener("keydown", onEsc);
    return () => window.removeEventListener("keydown", onEsc);
  }, [busy, onClose]);
  useEffect(() => () => { timers.current.forEach(clearTimeout); }, []);

  const later = (fn: () => void, delay: number) => { timers.current.push(setTimeout(fn, delay)); };
  const flash = (kind: "success" | "error", message: string) => {
    setNotice({ kind, message });
    setToast({ kind, message });
    later(() => setToast(null), 1700);
  };

  function changeMode(next: AuthMode) {
    if (busy || flip || (view === next && mode === next)) return;
    setNotice(null);
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) { setView(next); onModeChange(next); return; }
    setFlip(true);
    later(() => { setView(next); onModeChange(next); }, 225);
    later(() => setFlip(false), 510);
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setNotice(null);
    if (!supabase) { flash("error", t.missing); return; }
    if (view !== "recover" && password.length < 8) { flash("error", t.minimum); return; }
    if (view === "signup" && password !== confirmation) { flash("error", t.mismatch); return; }
    if (view === "signup" && fullName.trim().length < 2) { flash("error", t.enterName); return; }
    setBusy(true);
    try {
      if (view === "recover") {
        const { error } = await supabase.auth.resetPasswordForEmail(email.trim(), {
          redirectTo: `${window.location.origin}/auth/recovery`,
        });
        if (error) throw error;
        flash("success", t.mailSent);
      } else if (view === "login") {
        const { data, error } = await supabase.auth.signInWithPassword({ email: email.trim(), password });
        if (error) throw error;
        if (!data.session) throw new Error(t.generic);
        flash("success", t.signedIn);
        later(() => { router.replace("/dashboard"); router.refresh(); }, 1850);
      } else {
        const { data, error } = await supabase.auth.signUp({
          email: email.trim(), password,
          options: {
            data: { full_name: fullName.trim() },
            emailRedirectTo: `${window.location.origin}/auth/callback?next=/dashboard`,
          },
        });
        if (error) throw error;
        if (data.session) {
          flash("success", t.signedUp);
          later(() => { router.replace("/dashboard"); router.refresh(); }, 1850);
        } else {
          flash("success", t.confirmMail);
        }
      }
    } catch (error) {
      flash("error", error instanceof Error ? error.message : t.generic);
    } finally { setBusy(false); }
  }

  async function google() {
    if (busy) return;
    if (!supabase) { flash("error", t.missing); return; }
    setBusy(true);
    setNotice(null);
    try {
      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: "google",
        options: { redirectTo: `${window.location.origin}/auth/callback?next=/dashboard`, skipBrowserRedirect: true },
      });
      if (error) throw error;
      if (!data.url) throw new Error(t.cannotGoogle);
      // Supabase SSR stores the PKCE verifier in browser cookies before this redirect.
      // A short-lived, non-secret marker: only display the welcome animation
      // when the authenticated user actually returns to /dashboard.
      window.sessionStorage.setItem("yadok:google-auth-pending", String(Date.now()));
      window.location.assign(data.url);
    } catch (error) {
      window.sessionStorage.removeItem("yadok:google-auth-pending");
      flash("error", error instanceof Error ? error.message : t.cannotGoogle);
      setBusy(false);
    }
  }

  const isRecover = view === "recover";
  const active: AuthMode = view === "signup" ? "signup" : "login";
  const title = isRecover ? t.recoverTitle : view === "signup" ? t.join : t.hello;
  const subtitle = isRecover ? t.recoverSub : view === "signup" ? t.joinSub : t.helloSub;

  return <div className="ya9-shade" onPointerDown={e => { if (e.target === e.currentTarget && !busy) onClose(); }}>
    <style>{styles}</style>
    <section className="ya9-card" role="dialog" aria-modal="true" aria-label={title} dir={locale === "ar" ? "rtl" : "ltr"}>
      <header className="ya9-top">
        <div className="ya9-brand"><span className="ya9-logo"><Image src="/brand/yadok-logo.png" alt="YA-DOK" width={41} height={33} style={{ objectFit: "contain" }} /></span><span>YA-DOK</span></div>
        <button type="button" className="ya9-close" aria-label={t.cross} onClick={onClose} disabled={busy}>×</button>
      </header>
      <p className="ya9-eyebrow">{t.tagline}</p>
      <h2 className="ya9-title">{title}</h2>
      <p className="ya9-sub">{subtitle}</p>
      {!isRecover && <div className="ya9-switch" role="tablist" aria-label="Authentication">
        <button type="button" role="tab" aria-selected={active === "login"} onClick={() => changeMode("login")}>{t.login}</button>
        <button type="button" role="tab" aria-selected={active === "signup"} onClick={() => changeMode("signup")}>{t.signup}</button>
      </div>}
      {flip && <div className="ya9-mask" aria-hidden="true"><span>YA-DOK ✦</span></div>}
      <div className="ya9-stage" key={view}>
        <form onSubmit={submit}>
          {view === "signup" && <label className="ya9-label"><span className="ya9-labelText">{t.name}</span>
            <input className="ya9-input" type="text" required minLength={2} maxLength={120} autoComplete="name" placeholder={t.namePh} value={fullName} onChange={e => setFullName(e.target.value)}/>
          </label>}
          <label className="ya9-label"><span className="ya9-labelText">{t.email}</span>
            <input className="ya9-input" type="email" inputMode="email" dir="ltr" required autoComplete="email" placeholder={t.emailPh} value={email} onChange={e => setEmail(e.target.value)}/>
          </label>
          {!isRecover && <PasswordField label={t.password} placeholder={t.passwordPh} value={password} onChange={setPassword} visible={showPassword} setVisible={setShowPassword} complete={view === "login" ? "current-password" : "new-password"} t={t} />}
          {view === "signup" && <>
            <div className="ya9-strength" role="meter" aria-label={t.passwordStrength} aria-valuemin={0} aria-valuemax={4} aria-valuenow={Math.min(4, Math.floor(password.length / 3))}>
              {[1,2,3,4].map(n => <span key={n} className={password.length >= n * 3 ? "strong" : ""}/>) }
            </div>
            <div style={{height:15}}/>
            <PasswordField label={t.confirm} placeholder={t.confirm} value={confirmation} onChange={setConfirmation} visible={showConfirmation} setVisible={setShowConfirmation} complete="new-password" t={t} />
          </>}
          {view === "login" && <div className="ya9-tools"><button type="button" className="ya9-link" onClick={() => { setNotice(null); setView("recover"); }}>{t.forgot}</button></div>}
          {notice && <div className="ya9-notice" data-kind={notice.kind} role="status">{notice.message}</div>}
          <button className="ya9-submit" disabled={busy || flip} type="submit">{busy ? <><span className="ya9-spinner"/>{t.loading}</> : <>{isRecover ? t.sendLink : view === "login" ? t.enter : t.create} <span aria-hidden="true">→</span></>}</button>
        </form>
        {isRecover ? <p className="ya9-foot"><button type="button" onClick={() => setView("login")}>{t.back}</button></p> : <>
          <div className="ya9-or">{t.or}</div>
          <button type="button" className="ya9-google" disabled={busy || flip} onClick={google}><GoogleMark/><span>{busy ? t.busyGoogle : t.google}</span></button>
          <p className="ya9-foot">{view === "login" ? t.new : t.have}
            <button type="button" onClick={() => changeMode(view === "login" ? "signup" : "login")}>{view === "login" ? t.signup : t.login}</button>
          </p>
        </>}
      </div>
      <p className="ya9-secure"><span aria-hidden="true">✧</span>{t.secure}</p>
    </section>
    {toast && <AuthOutcome key={`${toast.kind}-${toast.message}`} kind={toast.kind} message={toast.message} />}
  </div>;
}
