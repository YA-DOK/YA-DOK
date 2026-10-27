
"use client";

import { createClient } from "@/lib/supabase/client";
import { useState, type FormEvent } from "react";

type CompleteResponse = {
  ok?: boolean;
  signedOut?: boolean;
  error?: string;
};

export function ResetPasswordForm() {
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] =
    useState("");

  const [showPassword, setShowPassword] =
    useState(false);

  const [showConfirm, setShowConfirm] =
    useState(false);

  const [loading, setLoading] = useState(false);
  const [updated, setUpdated] = useState(false);
  const [error, setError] = useState("");

  async function finishSignOut() {
    if (loading) return;

    setLoading(true);
    setError("");

    try {
      const supabase = createClient();

      const { error: signOutError } =
        await supabase.auth.signOut();

      if (signOutError) {
        setError(
          "كلمة المرور اتغيرت، لكن تعذّر تسجيل الخروج. حاول تاني."
        );
        return;
      }

      window.location.replace("/");
    } catch {
      setError(
        "تعذّر تسجيل الخروج. حاول مرة تانية."
      );
    } finally {
      setLoading(false);
    }
  }

  async function handleReset(
    e: FormEvent<HTMLFormElement>
  ) {
    e.preventDefault();

    if (loading) return;

    setError("");

    if (password.length < 8) {
      setError(
        "كلمة المرور لازم تكون 8 أحرف على الأقل."
      );
      return;
    }

    if (password !== confirmPassword) {
      setError("كلمتا المرور غير متطابقتين.");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(
        "/reset-password/complete",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ password }),
          cache: "no-store",
        }
      );

      const result =
        (await response.json()) as CompleteResponse;

      if (!response.ok || !result.ok) {
        setError(
          result.error ||
            "تعذّر تغيير كلمة المرور. حاول مرة تانية."
        );
        return;
      }

      setUpdated(true);
      setPassword("");
      setConfirmPassword("");

      if (result.signedOut) {
        window.location.replace("/");
        return;
      }

      setError(
        "تم تغيير كلمة المرور بنجاح، لكن تسجيل الخروج لم يكتمل."
      );
    } catch {
      setError(
        "حصلت مشكلة في الاتصال. لو كلمة المرور اتغيرت بالفعل، جرّب تسجيل الدخول بالكلمة الجديدة."
      );
    } finally {
      setLoading(false);
    }
  }

  const inputClass =
    "w-full rounded-xl border border-[#D7C7A8] bg-[#FFFCF5] px-4 py-3 text-sm text-[#18352F] outline-none focus:border-[#6A937A] focus:ring-2 focus:ring-[#6A937A]/20";

  if (updated) {
    return (
      <div
        role="status"
        className="space-y-4 text-center"
      >
        <p className="rounded-xl bg-[#E5F3E8] p-5 text-[#24513D]">
          تم تغيير كلمة المرور بنجاح.
        </p>

        {error && (
          <p
            role="alert"
            className="text-sm text-red-700"
          >
            {error}
          </p>
        )}

        <button
          type="button"
          onClick={finishSignOut}
          disabled={loading}
          className="w-full rounded-xl bg-[#18352F] px-5 py-3 font-semibold text-white disabled:opacity-60"
        >
          {loading
            ? "جارٍ تسجيل الخروج..."
            : "العودة لتسجيل الدخول"}
        </button>
      </div>
    );
  }

  return (
    <form
      onSubmit={handleReset}
      className="space-y-5"
    >
      <div>
        <label
          htmlFor="new-password"
          className="mb-2 block text-sm font-semibold"
        >
          كلمة المرور الجديدة
        </label>

        <div className="relative">
          <input
            id="new-password"
            type={
              showPassword ? "text" : "password"
            }
            autoComplete="new-password"
            minLength={8}
            required
            dir="ltr"
            value={password}
            onChange={(e) =>
              setPassword(e.target.value)
            }
            disabled={loading}
            className={`${inputClass} pl-20`}
            placeholder="8 أحرف على الأقل"
          />

          <button
            type="button"
            onClick={() =>
              setShowPassword(!showPassword)
            }
            aria-label={
              showPassword
                ? "إخفاء كلمة المرور"
                : "إظهار كلمة المرور"
            }
            aria-pressed={showPassword}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-xs font-semibold text-[#805B27]"
          >
            {showPassword ? "إخفاء" : "إظهار"}
          </button>
        </div>
      </div>

      <div>
        <label
          htmlFor="confirm-new-password"
          className="mb-2 block text-sm font-semibold"
        >
          تأكيد كلمة المرور
        </label>

        <div className="relative">
          <input
            id="confirm-new-password"
            type={
              showConfirm ? "text" : "password"
            }
            autoComplete="new-password"
            minLength={8}
            required
            dir="ltr"
            value={confirmPassword}
            onChange={(e) =>
              setConfirmPassword(e.target.value)
            }
            disabled={loading}
            className={`${inputClass} pl-20`}
            placeholder="أعد كتابة كلمة المرور"
          />

          <button
            type="button"
            onClick={() =>
              setShowConfirm(!showConfirm)
            }
            aria-label={
              showConfirm
                ? "إخفاء تأكيد كلمة المرور"
                : "إظهار تأكيد كلمة المرور"
            }
            aria-pressed={showConfirm}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-xs font-semibold text-[#805B27]"
          >
            {showConfirm ? "إخفاء" : "إظهار"}
          </button>
        </div>
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
        className="w-full rounded-xl bg-[#18352F] px-5 py-3 font-semibold text-white transition hover:bg-[#285247] disabled:opacity-60"
      >
        {loading
          ? "جارٍ تغيير كلمة المرور..."
          : "تغيير كلمة المرور"}
      </button>
    </form>
  );
}
