
import { cookies } from "next/headers";
import Link from "next/link";
import { connection } from "next/server";

import { AuthShell } from "@/components/auth/auth-shell";
import { ResetPasswordForm } from "@/components/auth/reset-password-form";
import { createClient } from "@/lib/supabase/server";

export const instant = false;

export default async function ResetPasswordPage() {
  await connection();

  const cookieStore = await cookies();

  const recoveryUserId =
    cookieStore.get("yadok-recovery")?.value;

  const supabase = await createClient();

  const {
    data: { user },
    error,
  } = await supabase.auth.getUser();

  const isValidRecovery =
    !error &&
    !!user &&
    !!recoveryUserId &&
    recoveryUserId === user.id;

  return (
    <AuthShell
      title="تعيين كلمة مرور جديدة"
      description="اختار كلمة مرور قوية عشان تحافظ على أمان حسابك."
    >
      {isValidRecovery ? (
        <ResetPasswordForm />
      ) : (
        <div className="space-y-5 text-center">
          <p
            role="alert"
            className="rounded-xl border border-[#E6C7AD] bg-[#FFF3E8] p-5 text-sm leading-7 text-[#81542B]"
          >
            رابط الاسترجاع غير صالح أو انتهت
            صلاحيته. اطلب رابط جديد وحاول مرة تانية.
          </p>

          <Link
            href="/forgot-password"
            className="block rounded-xl bg-[#18352F] px-5 py-3 font-semibold text-white hover:bg-[#285247]"
          >
            طلب رابط استرجاع جديد
          </Link>
        </div>
      )}
    </AuthShell>
  );
}
