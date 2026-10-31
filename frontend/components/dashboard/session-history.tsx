"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getAccessToken } from "@/lib/supabase/client";
import { translated, useDashboardUI } from "./dashboard-ui";

type HistoryItem = {
  session_id: string;
  case_code: string | null;
  mode: "training" | "test";
  current_phase: string;
  is_completed: boolean;
  is_paused: boolean;
  diagnosis: string | null;
  created_at: string | null;
  updated_at: string | null;
};

function dateText(value: string | null): string {
  if (!value) return "—";
  const time = new Date(value);
  return Number.isNaN(time.getTime()) ? "—" : time.toLocaleString();
}

export function SessionHistory() {
  const { locale } = useDashboardUI();
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function load() {
      try {
        const base = process.env.NEXT_PUBLIC_API_URL;
        if (!base) throw new Error("NEXT_PUBLIC_API_URL is missing");
        const token = await getAccessToken();
        if (controller.signal.aborted) return;

        const response = await fetch(
          `${base.replace(/\/$/, "")}/api/v1/simulation/sessions?limit=50`,
          {
            headers: { Authorization: `Bearer ${token}`, Accept: "application/json" },
            cache: "no-store",
            signal: controller.signal,
          }
        );
        if (!response.ok) throw new Error(`Could not load sessions (${response.status})`);
        const data = (await response.json()) as { items: HistoryItem[] };
        if (!controller.signal.aborted) setItems(Array.isArray(data.items) ? data.items : []);
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(err instanceof Error ? err.message : "Unable to load history");
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }

    void load();
    return () => controller.abort();
  }, []);

  if (loading) return <div className="ydash-glass ydash-placeholder" role="status">{translated(locale, "جاري تحميل جلساتك...", "Loading your sessions...")}</div>;
  if (error) return <div className="ydash-glass ydash-placeholder" role="alert">{translated(locale, "تعذر تحميل سجل الجلسات", "Could not load session history")}: {error}</div>;
  if (!items.length) return <div className="ydash-glass ydash-placeholder">{translated(locale, "لسه مفيش جلسات محفوظة.", "No sessions saved yet.")}</div>;

  return <section className="ydash-subpage" aria-label="Session history">
    <div style={{ display: "grid", gap: 12 }}>
      {items.map((item) => <article key={item.session_id} className="ydash-glass" style={{ padding: 20, display: "grid", gap: 10 }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
          <strong>{item.case_code || translated(locale, "حالة تدريب", "Clinical case")}</strong>
          <span>{item.is_completed ? translated(locale, "مكتملة", "Completed") : item.is_paused ? translated(locale, "متوقفة", "Paused") : translated(locale, "قيد التنفيذ", "In progress")}</span>
        </div>
        <p style={{ margin: 0 }}>{item.mode === "test" ? "Assessment" : "Training"} · {dateText(item.created_at)}</p>
        {item.diagnosis && <p style={{ margin: 0, overflowWrap: "anywhere" }}>{translated(locale, "التشخيص", "Diagnosis")}: {item.diagnosis}</p>}
        {!item.is_completed && item.case_code && (
          <Link
            href={`/simulation/preview?case=${encodeURIComponent(item.case_code)}&mode=${item.mode === "test" ? "test" : "training"}&resume=${encodeURIComponent(item.session_id)}`}
            className="ydash-outline-action"
            style={{ justifySelf: "start", display: "inline-flex" }}
          >
            {translated(locale, "استكمال الجلسة", "Resume session")}
          </Link>
        )}
        <small style={{ opacity: 0.7 }}>Session: {item.session_id}</small>
      </article>)}
    </div>
  </section>;
}
