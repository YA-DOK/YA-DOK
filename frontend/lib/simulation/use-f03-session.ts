"use client";

import { useEffect, useRef, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import {
  f03Live,
  F03HttpError,
  type F03Mode,
  type F03Phase,
  type F03Session,
} from "./f03-live";

type Action = "phase" | "pause" | "resume" | "diagnosis" | "complete";

const phases: F03Phase[] = [
  "introduction",
  "history_taking",
  "examination",
  "investigations",
  "diagnosis_and_plan",
  "completed",
];

function sessionSeconds(session: F03Session): number {
  const created = session.events.find(
    (event) => event.event_type === "session_created"
  );

  if (!created) return 0;

  const start = Date.parse(created.timestamp);
  if (!Number.isFinite(start)) return 0;

  const completed = session.events.find(
    (event) => event.event_type === "session_completed"
  );

  const end = completed
    ? Date.parse(completed.timestamp)
    : Date.now();

  let pausedAt: number | null = null;
  let pausedTime = 0;

  for (const event of session.events) {
    const time = Date.parse(event.timestamp);
    if (!Number.isFinite(time)) continue;

    if (event.event_type === "session_paused") {
      pausedAt = time;
    } else if (
      event.event_type === "session_resumed" &&
      pausedAt !== null
    ) {
      pausedTime += time - pausedAt;
      pausedAt = null;
    }
  }

  if (pausedAt !== null) pausedTime += end - pausedAt;

  // Test attempts use an uninterrupted wall-clock limit, including pause.
  const duration = session.mode === "test" ? end - start : end - start - pausedTime;
  return Math.max(0, Math.floor(duration / 1000));
}

export function useF03Session() {
  const [session, setSession] = useState<F03Session | null>(null);
  const [mode, setMode] = useState<F03Mode>("training");
  const [elapsed, setElapsed] = useState(0);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const [caseCode, setCaseCode] = useState("");

  const booted = useRef(false);
  const storageKey = useRef("");
  const pending = useRef(new Map<string, string>());
  const inFlight = useRef(false);
  const timeoutCheckedAt = useRef(0);

  useEffect(() => {
    if (booted.current) return;
    booted.current = true;

    async function bootstrap() {
      try {
        const params = new URLSearchParams(window.location.search);
        const selected: F03Mode =
          params.get("mode") === "test" ? "test" : "training";
        // Starting from the Case Library is a NEW attempt. Refresh is a resume.
        const newAttempt = params.get("new") === "1";
        const requestedResumeId = params.get("resume");
        if (
          requestedResumeId !== null &&
          (newAttempt || !/^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$/i.test(requestedResumeId))
        ) {
          throw new Error("Invalid Resume link. Open Session History and try again.");
        }

        const caseCode = params.get("case") ?? "";
        if (!/^[A-Za-z0-9_-]{3,120}$/.test(caseCode)) {
          throw new Error("Select a valid case from the Case Library.");
        }
        setCaseCode(caseCode);


        const { data: { user } } = await createClient().auth.getUser();

        if (!user) throw new Error("Please log in first.");


        const key =
          `yadok:f03:${user.id}:${caseCode}:${selected}`;

        storageKey.current = key;

        let loaded: F03Session | null = null;
        // Explicit Resume overrides the browser's last-session cache.
        const savedId = requestedResumeId ?? (newAttempt ? null : sessionStorage.getItem(key));

        if (savedId) {
          try {
            loaded = await f03Live.get(savedId);
            if (
              loaded.case_code !== caseCode ||
              loaded.mode !== selected ||
              loaded.is_completed ||
              !loaded.case_version_id
            ) {
              if (requestedResumeId !== null) {
                throw new Error(
                  loaded.is_completed
                    ? "This attempt has ended. Start a new attempt from the Case Library."
                    : "This Resume link does not match the saved case or mode."
                );
              }
              loaded = null;
              sessionStorage.removeItem(key);
            }
          } catch (err) {
            if (
              requestedResumeId !== null ||
              !(err instanceof F03HttpError) || err.status !== 404
            ) {
              throw err;
            }
            sessionStorage.removeItem(key);
          }
        }

        const current = loaded ?? await f03Live.startPublished(caseCode, selected);

        // Cache the explicit Resume ID as the latest active attempt in this tab.
        sessionStorage.setItem(key, current.session_id);

        // Do not create another attempt when the student refreshes this URL.
        if (newAttempt) {
          const url = new URL(window.location.href);
          url.searchParams.delete("new");
          window.history.replaceState(window.history.state, "", url.toString());
        }

        setSession(current);
        setMode(current.mode ?? selected);
        setError("");
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Could not start session."
        );
      } finally {
        setBusy(false);
      }
    }

    void bootstrap();
  }, []);

  useEffect(() => {
    if (!session) return;

    const tick = () => {
      const seconds = sessionSeconds(session);
      setElapsed(seconds);
      const duration = session.duration_minutes;
      if (
        session.mode === "test" && !session.is_completed &&
        typeof duration === "number" && duration > 0 &&
        seconds >= duration * 60 && !inFlight.current &&
        Date.now() - timeoutCheckedAt.current >= 5000
      ) {
        timeoutCheckedAt.current = Date.now();
        void f03Live.get(session.session_id).then((fresh) => {
          setSession(fresh);
          if (fresh.is_completed && storageKey.current) {
            sessionStorage.removeItem(storageKey.current);
          }
        }).catch((err: unknown) => {
          setError(err instanceof Error ? err.message : "Could not confirm time limit.");
        });
      }
    };
    tick();

    const timer = window.setInterval(tick, 1000);
    return () => window.clearInterval(timer);
  }, [session]);

  async function runAction(
    action: Action,
    body: Record<string, unknown> = {}
  ): Promise<boolean> {
    if (!session || inFlight.current) return false;

    const identity = `${action}:${JSON.stringify(body)}`;
    let requestId = pending.current.get(identity);

    if (!requestId) {
      requestId = crypto.randomUUID();
      pending.current.set(identity, requestId);
    }

    inFlight.current = true;
    setBusy(true);

    try {
      await f03Live.action(session.session_id, action, body, requestId);

      const updated = await f03Live.get(session.session_id);
      setSession(updated);
      if (updated.is_completed && storageKey.current) {
        sessionStorage.removeItem(storageKey.current);
      }
      pending.current.delete(identity);
      setError("");
      return true;
    } catch (err) {
      if (err instanceof F03HttpError && err.status < 500) {
        pending.current.delete(identity);
      }

      setError(err instanceof Error ? err.message : "Action failed.");
      return false;
    } finally {
      inFlight.current = false;
      setBusy(false);
    }
  }

  async function finish(diagnosis: string, plan: string): Promise<boolean> {
    if (!session || session.is_completed || session.is_paused) {
      setError("Resume an active session before ending it.");
      return false;
    }

    if (!session.diagnosis) {
      if (!diagnosis.trim()) {
        setError("A diagnosis is required to complete the session.");
        return false;
      }

      if (diagnosis.trim().length > 3000 || plan.trim().length > 5000) {
        setError("Diagnosis must be at most 3000 characters; treatment at most 5000.");
        return false;
      }

      const saved = await runAction("diagnosis", {
        diagnosis: diagnosis.trim(),
        treatment_plan: plan.trim(),
      });

      if (!saved) return false;
    }

    return runAction("complete");
  }

  function restart() {
    if (storageKey.current) {
      sessionStorage.removeItem(storageKey.current);
    }
    // "Try Again" must not reopen the same pinned Resume ID.
    const url = new URL(window.location.href);
    url.searchParams.delete("resume");
    url.searchParams.set("new", "1");
    window.location.assign(url.toString());
  }

  const currentPhase = session?.current_phase ?? "introduction";
  const nextPhase = phases[phases.indexOf(currentPhase) + 1];

  return {
    session,
    caseCode,
    mode,
    elapsed,
    busy,
    error,
    paused: session?.is_paused ?? false,
    ended: session?.is_completed ?? false,
    currentPhase,
    nextPhase,
    runAction,
    finish,
    restart,
  };
}
