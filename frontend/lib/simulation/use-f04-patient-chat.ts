"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { createClient } from "@/lib/supabase/client";

export type F04Message = {
  role: "student" | "patient";
  content: string;
};

type F04PatientReply = {
  reply: string;
  client_message_id: string;
};

const apiBase = (
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"
).replace(/\/+$/, "");

function describeApiError(body: unknown, status: number): string {
  if (status === 401) return "Your login has expired. Please sign in again.";
  if (body && typeof body === "object") {
    const data = body as Record<string, unknown>;
    if (typeof data.detail === "string") return data.detail;
    if (data.detail && typeof data.detail === "object") {
      const detail = data.detail as Record<string, unknown>;
      if (typeof detail.message === "string") {
        return typeof detail.code === "string"
          ? `${detail.code}: ${detail.message}`
          : detail.message;
      }
    }
  }
  return `Patient chat request failed (HTTP ${status}).`;
}

async function patientChatApi<T>(
  sessionId: string,
  method: "GET" | "POST",
  body?: { client_message_id: string; content: string },
): Promise<T> {
  const supabase = createClient();
  const { data, error: authError } = await supabase.auth.getSession();
  if (authError || !data.session?.access_token) {
    throw new Error("Sign in again to use patient chat.");
  }

  const response = await fetch(
    `${apiBase}/api/v1/simulation/sessions/${encodeURIComponent(sessionId)}/messages`,
    {
      method,
      headers: {
        Authorization: `Bearer ${data.session.access_token}`,
        ...(body ? { "Content-Type": "application/json" } : {}),
      },
      ...(body ? { body: JSON.stringify(body) } : {}),
      cache: "no-store",
    },
  );

  const raw = await response.text();
  let parsed: unknown = null;
  try {
    parsed = raw ? JSON.parse(raw) : null;
  } catch {
    // Never display an HTML error page containing arbitrary server data.
  }
  if (!response.ok) throw new Error(describeApiError(parsed, response.status));
  return parsed as T;
}

// F04 reads and writes the *same pinned F03 session*; no parallel session is created.
export function useF04PatientChat(sessionId: string | undefined) {
  const [messages, setMessages] = useState<F04Message[]>([]);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const sendingLock = useRef(false);
  // Reuse a message ID after an uncertain network failure to avoid double writes.
  const pending = useRef<{ sessionId: string; content: string; id: string } | null>(null);
  const currentSessionId = useRef(sessionId);
  currentSessionId.current = sessionId;

  const refresh = useCallback(async () => {
    if (!sessionId) return;
    const saved = await patientChatApi<F04Message[]>(sessionId, "GET");
    if (!Array.isArray(saved)) throw new Error("Invalid saved chat response.");
    if (currentSessionId.current === sessionId) {
      setMessages(saved);
      setError("");
    }
  }, [sessionId]);

  useEffect(() => {
    if (!sessionId) {
      setMessages([]);
      setDraft("");
      setError("");
      setLoading(false);
      pending.current = null;
      return;
    }
    let alive = true;
    // GET history on first load and after F03 restores the session on refresh.
    void (async () => {
      setMessages([]);
      setError("");
      setLoading(true);
      try {
        const saved = await patientChatApi<F04Message[]>(sessionId, "GET");
        if (!Array.isArray(saved)) throw new Error("Invalid saved chat response.");
        if (alive && currentSessionId.current === sessionId) setMessages(saved);
      } catch (cause) {
        if (alive && currentSessionId.current === sessionId) {
          setError(cause instanceof Error ? cause.message : "Could not load the saved chat.");
        }
      } finally {
        if (alive && currentSessionId.current === sessionId) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, [sessionId]);

  const send = useCallback(async (canSend: boolean): Promise<boolean> => {
    const content = draft.trim();
    if (!sessionId || !content || sendingLock.current) return false;
    if (!canSend) {
      setError("Patient chat requires an active, unpaused session.");
      return false;
    }
    sendingLock.current = true;
    setSending(true);
    setError("");
    if (!pending.current || pending.current.content !== content || pending.current.sessionId !== sessionId) {
      pending.current = { id: crypto.randomUUID(), content, sessionId };
    }
    const messageId = pending.current.id;
    try {
      const result = await patientChatApi<F04PatientReply>(sessionId, "POST", {
        client_message_id: messageId,
        content,
      });
      if (typeof result?.reply !== "string") throw new Error("Invalid patient reply.");
      if (currentSessionId.current !== sessionId) return false;

      pending.current = null;
      setDraft("");
      // Show the confirmed answer immediately; refresh then reconciles with DB.
      setMessages((current) => [...current,
        { role: "student", content },
        { role: "patient", content: result.reply },
      ]);
      try {
        const saved = await patientChatApi<F04Message[]>(sessionId, "GET");
        if (Array.isArray(saved) && currentSessionId.current === sessionId) setMessages(saved);
      } catch {
        // POST already succeeded. Do not retry it just because history refresh failed.
        setError("Reply saved, but refreshing the chat failed. Reopen Chat History to retry.");
      }
      return true;
    } catch (cause) {
      if (currentSessionId.current === sessionId) {
        setError(cause instanceof Error ? cause.message : "Could not send the message.");
      }
      return false;
    } finally {
      sendingLock.current = false;
      if (currentSessionId.current === sessionId) setSending(false);
    }
  }, [draft, sessionId]);

  const retryRefresh = useCallback(async () => {
    try {
      setLoading(true);
      await refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not load messages.");
    } finally {
      setLoading(false);
    }
  }, [refresh]);

  return { messages, draft, setDraft, loading, sending, error, send, retryRefresh };
}
