"use client";

import { useEffect, useState } from "react";
import { f03Live, type F05ClinicalReview as ClinicalReviewData } from "@/lib/simulation/f03-live";

/** Read-only debrief: not an F07 grade or fabricated score. */
export default function F05ClinicalReview({ sessionId }: { sessionId: string }) {
  const [data, setData] = useState<ClinicalReviewData | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    void f03Live.clinicalReview(sessionId).then((result) => {
      if (!cancelled) setData(result);
    }).catch((reason: unknown) => {
      if (!cancelled) setError(reason instanceof Error ? reason.message : "Clinical review unavailable.");
    });
    return () => { cancelled = true; };
  }, [sessionId]);

  return <section aria-label="Clinical activity review" style={{
    marginTop: 16, background: "rgba(18,49,42,0.88)", border: "1px solid #8cbfa94f",
    borderRadius: 14, padding: 14, color: "#f2f7f2", fontSize: 12,
  }}>
    <strong style={{ fontSize: 14 }}>Clinical Review</strong>
    <p style={{ margin: "5px 0 10px", fontSize: 11, color: "#cde0d4" }}>Educational activity summary — not a graded score.</p>
    {error && <p role="alert" style={{ color: "#ffd0ca" }}>{error}</p>}
    {!data && !error && <p role="status">Loading clinical review…</p>}
    {data && <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 9 }}>
      <span>Examinations: <strong>{data.request_counts.examination}</strong></span>
      <span>Labs / imaging: <strong>{data.request_counts.investigation_or_imaging}</strong></span>
      <span>Repeated: <strong>{data.request_counts.repeated}</strong></span>
      <span>Unavailable: <strong>{data.request_counts.unavailable}</strong></span>
      <span style={{ gridColumn: "1 / -1" }}>Essential clinical actions requested: <strong>{data.essential_actions.attempted} / {data.essential_actions.total}</strong></span>
    </div>}
  </section>;
}
