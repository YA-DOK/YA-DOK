
import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

import { createClient } from "@/lib/supabase/server";

export async function POST(request: NextRequest) {
  // Reject cross-origin requests.
  const origin = request.headers.get("origin");

  if (origin !== request.nextUrl.origin) {
    return NextResponse.json(
      { error: "طلب غير مسموح به." },
      { status: 403 }
    );
  }

  if (
    !request.headers
      .get("content-type")
      ?.includes("application/json")
  ) {
    return NextResponse.json(
      { error: "صيغة الطلب غير صحيحة." },
      { status: 415 }
    );
  }

  let password: unknown;

  try {
    const body = await request.json();
    password = body?.password;
  } catch {
    return NextResponse.json(
      { error: "بيانات الطلب غير صحيحة." },
      { status: 400 }
    );
  }

  if (
    typeof password !== "string" ||
    password.length < 8
  ) {
    return NextResponse.json(
      { error: "كلمة المرور لازم تكون 8 أحرف على الأقل." },
      { status: 400 }
    );
  }

  const cookieStore = await cookies();

  const recoveryUserId =
    cookieStore.get("yadok-recovery")?.value;

  const supabase = await createClient();

  const {
    data: { user },
    error: authError,
  } = await supabase.auth.getUser();

  if (
    authError ||
    !user ||
    !recoveryUserId ||
    recoveryUserId !== user.id
  ) {
    return NextResponse.json(
      {
        error:
          "جلسة الاسترجاع غير صالحة. اطلب رابط جديد.",
      },
      { status: 401 }
    );
  }

  // Change the password only after validating
  // both the authenticated user and recovery marker.
  const { error: updateError } =
    await supabase.auth.updateUser({
      password,
    });

  if (updateError) {
    return NextResponse.json(
      {
        error:
          "تعذّر تغيير كلمة المرور. اختار كلمة مرور قوية ومختلفة وحاول تاني.",
      },
      { status: 400 }
    );
  }

  // Password was successfully changed.
  // Attempt to end the Supabase session.
  let signedOut = false;

  try {
    const { error: signOutError } =
      await supabase.auth.signOut();

    signedOut = !signOutError;
  } catch {
    signedOut = false;
  }

  // Always expire the recovery marker after
  // a successful password update.
  cookieStore.set("yadok-recovery", "", {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/reset-password",
    maxAge: 0,
  });

  return NextResponse.json(
    {
      ok: true,
      signedOut,
    },
    {
      headers: {
        "Cache-Control": "no-store",
      },
    }
  );
}
