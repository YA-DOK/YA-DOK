"use client";

import { useEffect, useState } from "react";
import { getAccessToken } from "@/lib/supabase/client";

export function SecureImagingPreview({ sessionId, imageId }: { sessionId: string; imageId: string }) {
  const [objectUrl, setObjectUrl] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  useEffect(() => () => { if (objectUrl) URL.revokeObjectURL(objectUrl); }, [objectUrl]);

  async function viewImage() {
    if (loading || objectUrl) return;
    setLoading(true);
    setError("");
    try {
      const token = await getAccessToken();
      const base = process.env.NEXT_PUBLIC_API_URL;
      if (!base || !token) throw new Error("Sign in to view this image.");
      const endpoint = `${base.replace(/\/$/, "")}/api/v1/simulation/sessions/${encodeURIComponent(sessionId)}/imaging/${encodeURIComponent(imageId)}/asset`;
      const res = await fetch(endpoint, { headers: { Authorization: `Bearer ${token}` }, cache: "no-store" });
      if (!res.ok) throw new Error(res.status === 503 ? "Image storage is not configured yet." : `Image unavailable (HTTP ${res.status}).`);
      const type = res.headers.get("content-type") || "";
      if (!/^image\/(png|jpeg|webp)$/i.test(type)) throw new Error("Unsupported image format.");
      const blob = await res.blob();
      if (blob.size > 8 * 1024 * 1024) throw new Error("Image exceeds the viewing size limit.");
      setObjectUrl(URL.createObjectURL(blob));
    } catch (err) { setError(err instanceof Error ? err.message : "Image could not be loaded."); }
    finally { setLoading(false); }
  }
  return <>
    <button type="button" onClick={() => void viewImage()} disabled={loading} className="f05ui_showMore">
      {loading ? "Opening image…" : "View case image"}
    </button>
    {error && <p role="alert" className="f05ui_error">{error}</p>}
    {objectUrl && <div role="dialog" aria-modal="true" aria-label="Clinical image viewer" className="f05ui_imageBackdrop">
      <div className="f05ui_imageModal">
        <button type="button" onClick={() => setObjectUrl(null)} aria-label="Close image viewer">Close ✕</button>
        {/* The object URL is from the authorized image response, not case-data text. */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={objectUrl} alt="Case-defined medical investigation" className="f05ui_imageFull" />
      </div>
    </div>}
  </>;
}
