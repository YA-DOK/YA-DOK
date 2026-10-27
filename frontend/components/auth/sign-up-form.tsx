
"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { createClient } from "@/lib/supabase/client";
import { GoogleLoginButton } from "./google-login-button";

export function SignUpForm() {
  const router = useRouter();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  // Password visibility
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  async function handleSignUp(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (loading) return;

    setError("");

    const cleanName = fullName.trim();
    const cleanEmail = email.trim().toLowerCase();

    if (cleanName.length < 2) {
      setError("الاسم لازم يكون حرفين على الأقل.");
      return;
    }

    if (password.length < 8) {
      setError("كلمة المرور لازم تكون 8 أحرف على الأقل.");
      return;
    }

    if (password !== confirmPassword) {
      setError("كلمتا المرور غير متطابقتين.");
      return;
    }

    setLoading(true);

    try {
      const supabase = createClient();

      const {
        data,
        error: signUpError,
      } = await supabase.auth.signUp({
        email: cleanEmail,
        password,
        options: {
          data: {
            full_name: cleanName,
          },
          emailRedirectTo: window.location.origin,
        },
      });

      if (signUpError) {
        if (signUpError.code === "over_email_send_rate_limit") {
          setError(
            "تم تجاوز حد إرسال الرسائل. حاول مرة تانية لاحقًا."
          );
        } else if (signUpError.code === "weak_password") {
          setError(
            "كلمة المرور ضعيفة. اختار كلمة مرور أقوى."
          );
        } else {
          setError(
            "تعذّر إنشاء الحساب. راجع البيانات وحاول مرة تانية."
          );
        }
        return;
      }

      if (data.session) {
        router.replace("/dashboard");
        router.refresh();
        return;
      }

      setSuccess(true);
    } catch {
      setError("حصلت مشكلة في الاتصال. حاول مرة تانية.");
    } finally {
      setLoading(false);
    }
  }

  const inputClass =
    "w-full rounded-xl border border-[#D7C7A8] bg-[#FFFCF5] px-3.5 py-2.5 text-sm text-[#18352F] outline-none transition placeholder:text-[#96978F] focus:border-[#6A937A] focus:ring-2 focus:ring-[#6A937A]/20";

  if (success) {
    return (
      <div role="status" className="space-y-5 text-center">
        <div className="rounded-2xl border border-[#B8D9C4] bg-[#E5F3E8] p-5">
          <h2 className="text-xl font-bold text-[#24513D]">
            راجع بريدك الإلكتروني
          </h2>

          <p className="mt-3 text-sm leading-7 text-[#416B55]">
            لو تم قبول طلب التسجيل، هتوصلك رسالة لتأكيد
            بريدك الإلكتروني. افتح الرابط الموجود فيها،
            وبعدها ارجع سجّل دخولك.
          </p>
        </div>

        <Link
          href="/"
          className="inline-block w-full rounded-xl bg-[#18352F] px-5 py-3 text-center font-semibold text-white hover:bg-[#285247]"
        >
          العودة لتسجيل الدخول
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <form onSubmit={handleSignUp} className="space-y-3">

        {/* Full Name */}
        <div>
          <label
            htmlFor="signup-name"
            className="mb-1 block text-sm font-semibold"
          >
            الاسم الكامل
          </label>

          <input
            id="signup-name"
            type="text"
            autoComplete="name"
            placeholder="اكتب اسمك الكامل"
            required
            minLength={2}
            maxLength={255}
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            className={inputClass}
          />
        </div>

        {/* Email */}
        <div>
          <label
            htmlFor="signup-email"
            className="mb-1 block text-sm font-semibold"
          >
            البريد الإلكتروني
          </label>

          <input
            id="signup-email"
            type="email"
            autoComplete="email"
            dir="ltr"
            placeholder="name@example.com"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={inputClass}
          />
        </div>

        {/* Password Fields */}
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">

          {/* Password */}
          <div>
            <label
              htmlFor="signup-password"
              className="mb-1 block text-sm font-semibold"
            >
              كلمة المرور
            </label>

            <div className="relative">
              <input
                id="signup-password"
                type={showPassword ? "text" : "password"}
                autoComplete="new-password"
                dir="ltr"
                placeholder="8 أحرف على الأقل"
                minLength={8}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={`${inputClass} pl-16`}
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
                className="absolute left-2 top-1/2 -translate-y-1/2 rounded px-1 py-1 text-xs font-semibold text-[#805B27] hover:text-[#533B1B] focus-visible:outline-2 focus-visible:outline-[#805B27]"
              >
                {showPassword ? "إخفاء" : "إظهار"}
              </button>
            </div>
          </div>

          {/* Confirm Password */}
          <div>
            <label
              htmlFor="signup-confirm"
              className="mb-1 block text-sm font-semibold"
            >
              تأكيد كلمة المرور
            </label>

            <div className="relative">
              <input
                id="signup-confirm"
                type={showConfirmPassword ? "text" : "password"}
                autoComplete="new-password"
                dir="ltr"
                placeholder="أعد كتابة كلمة المرور"
                minLength={8}
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className={`${inputClass} pl-16`}
              />

              <button
                type="button"
                onClick={() =>
                  setShowConfirmPassword(!showConfirmPassword)
                }
                aria-label={
                  showConfirmPassword
                    ? "إخفاء تأكيد كلمة المرور"
                    : "إظهار تأكيد كلمة المرور"
                }
                aria-pressed={showConfirmPassword}
                className="absolute left-2 top-1/2 -translate-y-1/2 rounded px-1 py-1 text-xs font-semibold text-[#805B27] hover:text-[#533B1B] focus-visible:outline-2 focus-visible:outline-[#805B27]"
              >
                {showConfirmPassword ? "إخفاء" : "إظهار"}
              </button>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <p
            role="alert"
            className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700"
          >
            {error}
          </p>
        )}

        {/* Submit */}
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-xl bg-[#18352F] px-5 py-3 font-semibold text-white transition hover:bg-[#285247] disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? "جارٍ إنشاء الحساب..." : "إنشاء الحساب"}
        </button>
      </form>

      {/* Divider */}
      <div className="flex items-center gap-3 text-xs text-[#89988F]">
        <div className="h-px flex-1 bg-[#D7C7A8]" />
        <span>أو أكمل باستخدام</span>
        <div className="h-px flex-1 bg-[#D7C7A8]" />
      </div>

      {/* Google Login */}
      <GoogleLoginButton />

      {/* Sign In Link */}
      <p className="text-center text-sm text-[#60766D]">
        عندك حساب بالفعل؟{" "}
        <Link
          href="/"
          className="font-bold text-[#805B27] hover:underline"
        >
          تسجيل الدخول
        </Link>
      </p>
    </div>
  );
}
