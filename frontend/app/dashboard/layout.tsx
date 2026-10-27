
import { Alexandria } from "next/font/google";
import { redirect } from "next/navigation";
import { connection } from "next/server";
import type { ReactNode } from "react";

import { DashboardShell } from "@/components/dashboard/dashboard-shell";
import { createClient } from "@/lib/supabase/server";

const alexandria = Alexandria({
  subsets: ["arabic", "latin"],
  display: "swap",
});

export const instant = false;

export default async function DashboardLayout({
  children,
}: {
  children: ReactNode;
}) {
  await connection();

  const supabase = await createClient();

  const {
    data: { user },
    error,
  } = await supabase.auth.getUser();

  if (error || !user) {
    redirect("/");
  }

  const metadataName = user.user_metadata?.full_name;

  const name =
    typeof metadataName === "string" && metadataName.trim()
      ? metadataName.trim()
      : user.email?.split("@")[0] || "الطالب";

  return (
    <div className={alexandria.className}>
      <DashboardShell
        name={name}
        email={user.email || ""}
      >
        {children}
      </DashboardShell>
    </div>
  );
}
