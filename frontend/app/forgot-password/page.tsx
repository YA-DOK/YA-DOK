
"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";

import { AuthShell } from "@/components/auth/auth-shell";
import { createClient } from "@/lib/supabase/client";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  async function handleResetRequest(
    e: FormEvent<HTMLFormElement>
  ) {
    e.preventDefault();
    if (loading) return;

    setLoading(true);
    setError("");

    try {
      const supabase = createClient();

      const { error: resetError } =
        await supabase.auth.resetPasswordForEmail(
          email.trim().toLowerCase(),
          {
            redirectTo: `${window.location.origin}/auth/recovery`,
          }
        );

      if (resetError) {
        if (resetError.code === "over_email_send_rate_limit") {
          setError(
            "تم تجاوز حد إرسال الرسائل. حاول مرة تانية لاحقًا."
          );
        } else {
          setError(
            "تعذّر إرسال الطلب حاليًا. حاول مرة تانية."
          );
        }
        return;
      }

      setSuccess(true);
    } catch {
      setError("حصلت مشكلة في الاتصال. حاول مرة تانية.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthShell
      title="نسيت كلمة المرور؟"
      description="ولا يهمك، هنساعدك تستعيد الوصول لحسابك."
    >
      {success ? (
        <div role="status" className="space-y-5 text-center">
          <div className="rounded-2xl border border-[#B8D9C4] bg-[#E5F3E8] p-5">
            <h2 className="text-lg font-bold text-[#24513D]">
              راجع بريدك الإلكتروني
            </h2>

            <p className="mt-3 text-sm leading-7 text-[#416B55]">
              لو البريد الإلكتروني مرتبط بحساب عندنا،
              هتوصلك رسالة فيها رابط لإعادة تعيين كلمة المرور.
            </p>
          </div>

          <Link
            href="/"
            className="block rounded-xl bg-[#18352F] px-5 py-3 text-center font-semibold text-white hover:bg-[#285247]"
          >
            العودة لتسجيل الدخول
          </Link>
        </div>
      ) : (
        <form
          onSubmit={handleResetRequest}
          className="space-y-5"
        >
          <div>
            <label
              htmlFor="reset-email"
              className="mb-2 block text-sm font-semibold"
            >
              البريد الإلكتروني
            </label>

            <input
              id="reset-email"
              type="email"
              dir="ltr"
              autoComplete="email"
              placeholder="name@example.com"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-xl border border-[#D7C7A8] bg-[#FFFCF5] px-4 py-3 text-[#18352F] outline-none focus:border-[#6A937A] focus:ring-2 focus:ring-[#6A937A]/20"
            />
          </div>

          {error && (
            <p
              role="alert"
              className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700"
            >
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-[#18352F] px-5 py-3 font-semibold text-white transition hover:bg-[#285247] disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading
              ? "جارٍ إرسال الطلب..."
              : "إرسال رابط الاسترجاع"}
          </button>

          <p className="text-center text-sm">
            <Link
              href="/"
              className="font-semibold text-[#805B27] hover:underline"
            >
              العودة لتسجيل الدخول
            </Link>
          </p>
        </form>
      )}
    </AuthShell>
  );
}
