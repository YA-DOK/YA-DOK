
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";

export function LogoutButton() {
  const router = useRouter();

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function handleLogout() {
    setLoading(true);
    setErrorMessage(null);

    try {
      const supabase = createClient();

      const { error } = await supabase.auth.signOut();

      if (error) {
        setErrorMessage(error.message);
        setLoading(false);
        return;
      }

      router.replace("/");
      router.refresh();
    } catch {
      setErrorMessage("Something went wrong. Please try again.");
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col items-center gap-3">
      <button
        type="button"
        onClick={handleLogout}
        disabled={loading}
        className="rounded-lg bg-red-600 px-6 py-3 font-medium text-white hover:bg-red-700 disabled:opacity-50"
      >
        {loading ? "Signing out..." : "Sign Out"}
      </button>

      {errorMessage && (
        <p className="text-sm text-red-400">
          {errorMessage}
        </p>
      )}
    </div>
  );
}
