
import { createClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";

function invalidRecoveryLink(origin: string) {
  const response = NextResponse.redirect(
    new URL("/reset-password?error=invalid", origin)
  );

  response.cookies.set("yadok-recovery", "", {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/reset-password",
    maxAge: 0,
  });

  response.headers.set("Cache-Control", "no-store");

  return response;
}

export async function GET(request: Request) {
  const url = new URL(request.url);

  const code = url.searchParams.get("code");
  const flowId = url.searchParams.get("sb_flow_id");

  if (!code) {
    return invalidRecoveryLink(url.origin);
  }

  const supabase = await createClient();

  const { data, error } =
    await supabase.auth.exchangeCodeForSession(
      code,
      flowId ? { flowId } : undefined
    );

  if (error || !data.user) {
    return invalidRecoveryLink(url.origin);
  }

  const response = NextResponse.redirect(
    new URL("/reset-password", url.origin)
  );

  // This is a short-lived UI marker tied to the
  // recovered account, not an authentication token.
  response.cookies.set(
    "yadok-recovery",
    data.user.id,
    {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      path: "/reset-password",
      maxAge: 15 * 60,
    }
  );

  response.headers.set("Cache-Control", "no-store");

  return response;
}
