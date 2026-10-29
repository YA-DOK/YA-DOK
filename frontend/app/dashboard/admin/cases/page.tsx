import { connection } from "next/server";
import Link from "next/link";
import { createClient } from "@/lib/supabase/server";
import { AdminCasesManager } from "@/components/dashboard/admin-cases-manager";
import "@/components/dashboard/admin-cases.css";

export const instant = false;
const apiBase = process.env.API_INTERNAL_URL || process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export default async function AdminCasesPage() {
  await connection();
  const supabase = await createClient();
  const { data: { user }, error } = await supabase.auth.getUser();
  if (error || !user) return <div className="yd-admin-message">Please sign in.</div>;
  const { data: { session } } = await supabase.auth.getSession();
  const token = session?.access_token;
  if (!token) return <div className="yd-admin-message">Session expired. Please sign in again.</div>;
  let allowed = false;
  try {
    const response = await fetch(new URL("/api/v1/admin/cases?limit=1", apiBase), {
      cache: "no-store", headers: { Authorization: `Bearer ${token}` }, signal: AbortSignal.timeout(8000),
    });
    allowed = response.ok;
  } catch { /* Give clear unavailability, never disclose admin content */ }
  if (!allowed) return <div className="yd-admin-message"><h1>Admin access required</h1><p>Only authorized case administrators can open this page. Check that FastAPI is running.</p><Link href="/dashboard">Back to dashboard</Link></div>;
  return <AdminCasesManager />;
}
