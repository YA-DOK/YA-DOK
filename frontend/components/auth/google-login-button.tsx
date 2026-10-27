
"use client";

import { createClient } from "@/lib/supabase/client";
import { useState } from "react";

export function GoogleLoginButton() {
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function handleGoogleLogin() {
    if (loading) return;

    setLoading(true);
    setErrorMessage(null);

    try {
      const supabase = createClient();

      const { error } = await supabase.auth.signInWithOAuth({
        provider: "google",
        options: {
          redirectTo: `${window.location.origin}/auth/callback`,
        },
      });

      if (error) {
        setErrorMessage("تعذّر تسجيل الدخول بجوجل. حاول مرة تانية.");
        setLoading(false);
      }
    } catch {
      setErrorMessage("حصلت مشكلة في الاتصال. حاول مرة تانية.");
      setLoading(false);
    }
  }

  return (
    <div className="space-y-3">
      <button
        type="button"
        onClick={handleGoogleLogin}
        disabled={loading}
        className="flex w-full items-center justify-center gap-3 rounded-xl border border-[#D4D9CF] bg-white px-5 py-3.5 font-semibold text-[#19302B] transition hover:border-[#406C5A] hover:bg-[#EDF1EB] disabled:cursor-not-allowed disabled:opacity-60"
      >
        <span
          aria-hidden="true"
          className="text-lg font-bold text-[#4285F4]"
        >
          G
        </span>
        {loading ? "جارٍ التحويل إلى جوجل..." : "المتابعة باستخدام Google"}
      </button>

      {errorMessage && (
        <p role="alert" className="text-sm text-red-600">
          {errorMessage}
        </p>
      )}
    </div>
  );
}
