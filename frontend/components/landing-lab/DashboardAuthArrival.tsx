"use client";

import { useEffect, useState } from "react";
import { AuthOutcome } from "./AuthOutcome";

const MARKER = "yadok:google-auth-pending";
const MAX_AGE_MS = 10 * 60 * 1000;

/**
 * Only rendered inside the protected /dashboard route.
 * DashboardLayout verifies the Supabase user on the server and redirects
 * unauthenticated visitors before this client component can be shown.
 *
 * The OAuth flow sets this per-tab marker before going to Google. We don't
 * run a second browser getUser() check: right after PKCE callback the browser
 * client can briefly be out of sync even though the server check succeeded.
 */
export function DashboardAuthArrival() {
  const [show, setShow] = useState(false);

  useEffect(() => {
    let value: string | null;
    try {
      value = window.sessionStorage.getItem(MARKER);
    } catch {
      return;
    }

    if (!value) return;
    const issuedAt = Number(value);
    if (
      !Number.isFinite(issuedAt) ||
      issuedAt > Date.now() ||
      Date.now() - issuedAt > MAX_AGE_MS
    ) {
      window.sessionStorage.removeItem(MARKER);
      return;
    }

    setShow(true);
    // Consume the marker after the animation, not during the effect setup.
    // This works in development React Strict Mode, which re-runs effects.
    const timer = window.setTimeout(() => {
      setShow(false);
      window.sessionStorage.removeItem(MARKER);
    }, 1850);

    return () => window.clearTimeout(timer);
  }, []);

  return show ? <AuthOutcome kind="success" message="Welcome to YA-DOK!" /> : null;
}
