
"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { createClient } from "@/lib/supabase/client";
import { GoogleLoginButton } from "./google-login-button";

export function SignInForm() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSignIn(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();

    if (loading) return;

    setLoading(true);
    setError("");

    try {
      const supabase = createClient();

      const { error: signInError } =
        await supabase.auth.signInWithPassword({
          email: email.trim().toLowerCase(),
          password,
        });

      if (signInError) {
        if (signInError.code === "email_not_confirmed") {
          setError(
            "لازم تأكّد بريدك الإلكتروني قبل تسجيل الدخول."
          );
        } else {
          setError(
            "تعذّر تسجيل الدخول. تأكد من بياناتك وحاول مرة تانية."
          );
        }

        return;
      }

      router.replace("/dashboard");
      router.refresh();
    } catch {
      setError(
        "حصلت مشكلة في الاتصال. حاول مرة تانية."
      );
    } finally {
      setLoading(false);
    }
  }

  const inputClass =
    "w-full rounded-xl border border-[#D7C7A8] bg-[#FFFCF5] px-4 py-3.5 text-[#243334] outline-none transition placeholder:text-[#8E897C] focus:border-[#9B773F] focus:ring-2 focus:ring-[#C9A366]/25";

  return (
    <div className="space-y-5">
      <form
        onSubmit={handleSignIn}
        className="space-y-4"
      >
        {/* Email */}
        <div>
          <label
            htmlFor="login-email"
            className="mb-2 block text-sm font-semibold text-[#243334]"
          >
            البريد الإلكتروني
          </label>

          <input
            id="login-email"
            type="email"
            autoComplete="email"
            required
            dir="ltr"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="name@example.com"
            className={inputClass}
          />
        </div>

        {/* Password */}
        <div>
          <label
            htmlFor="login-password"
            className="mb-2 block text-sm font-semibold text-[#243334]"
          >
            كلمة المرور
          </label>

          <div className="relative">
            <input
              id="login-password"
              type={showPassword ? "text" : "password"}
              autoComplete="current-password"
              required
              dir="ltr"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className={`${inputClass} pl-20`}
            />

            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              aria-label={
                showPassword
                  ? "إخفاء كلمة المرور"
                  : "إظهار كلمة المرور"
              }
              aria-pressed={showPassword}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-xs font-semibold text-[#805B27] transition hover:text-[#533B1B]"
            >
              {showPassword ? "إخفاء" : "إظهار"}
            </button>
          </div>

          {/* Forgot Password */}
          <div className="mt-3 text-left">
            <Link
              href="/forgot-password"
              className="text-sm font-semibold text-[#805B27] transition hover:text-[#533B1B] hover:underline"
            >
              نسيت كلمة المرور؟
            </Link>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <p
            role="alert"
            className="rounded-xl border border-[#D89B91] bg-[#FFF0EB] p-3 text-sm text-[#9C4139]"
          >
            {error}
          </p>
        )}

        {/* Sign In Button */}
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-xl border border-[#C9A366]/50 bg-[#182F40] px-5 py-3.5 font-semibold text-white transition hover:bg-[#29495A] disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading
            ? "جارٍ تسجيل الدخول..."
            : "تسجيل الدخول"}
        </button>
      </form>

      {/* Divider */}
      <div className="flex items-center gap-4 text-xs text-[#8E897C]">
        <div className="h-px flex-1 bg-[#D7C7A8]" />
        <span>أو أكمل باستخدام</span>
        <div className="h-px flex-1 bg-[#D7C7A8]" />
      </div>

      {/* Google Authentication */}
      <GoogleLoginButton />

      {/* Sign Up Link */}
      <p className="text-center text-sm text-[#6C675B]">
        لسه معندكش حساب؟{" "}
        <Link
          href="/sign-up"
          className="font-bold text-[#805B27] transition hover:text-[#533B1B] hover:underline"
        >
          أنشئ حسابك
        </Link>
      </p>
    </div>
  );
}
