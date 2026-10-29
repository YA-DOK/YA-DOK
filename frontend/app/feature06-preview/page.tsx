
"use client";

import { useState } from "react";

import ModeSelector, {
  type SessionMode,
} from "../../components/training/ModeSelector";

import HintPanel from "../../components/training/HintPanel";

import { requestHint } from "../../lib/feature06/hintsApi";

type HintSource = "demo" | "api";
type HintEvent = {
  level: number;
  source: HintSource;
  reason: "manual_request";
  timestamp: string;
};

const DEMO_HINTS = [
  "Review the information you have collected.",
  "Focus on important missing information.",
  "Compare your findings before making a decision.",
];

export default function Feature06Preview() {
  const [mode, setMode] = useState<SessionMode | null>(null);
  const [source, setSource] = useState<HintSource>("demo");
  const [sessionId, setSessionId] = useState("");

  const [hintLevel, setHintLevel] = useState(0);
  const [hintText, setHintText] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hintEvents, setHintEvents] = useState<HintEvent[]>([]);

const logHint = (level: number) => {
  setHintEvents((previous) => [
    ...previous,
    {
      level,
      source,
      reason: "manual_request",
      timestamp: new Date().toISOString(),
    },
  ]);
};

  const resetHints = () => {
    setHintEvents([]);
    setHintLevel(0);
    setHintText(null);
    setError(null);
  };

  const handleModeChange = (newMode: SessionMode) => {
    setMode(newMode);
    resetHints();
  };

  const handleSourceChange = (newSource: HintSource) => {
    setSource(newSource);
    resetHints();
  };

  const handleRequestHint = async () => {
    if (mode !== "training" || loading || hintLevel >= 3) {
      return;
    }

    setError(null);

    if (source === "demo") {
      const nextLevel = hintLevel + 1;

      setHintLevel(nextLevel);
      setHintText(DEMO_HINTS[nextLevel - 1]);
      logHint(nextLevel);
      return;
    }

    if (!sessionId.trim()) {
      setError("Please enter a Session ID.");
      return;
    }

    setLoading(true);

    try {
      const result = await requestHint(sessionId);

      if (!result.allowed) {
        setError(result.reason || "Hint request denied.");
        return;
      }

      if (
        result.hint_level === null ||
        !result.hint
      ) {
        throw new Error("Incomplete API response.");
      }

      setHintLevel(result.hint_level);
      setHintText(result.hint);
      logHint(result.hint_level);

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to request hint."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <main
      style={{
        minHeight: "100vh",
        backgroundColor: "#F4E8D9",
        padding: "40px 20px",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 24,
        color: "#30251F",
      }}
    >
      <h1 style={{ fontSize: 30, fontWeight: 700 }}>
        YA-DOK | Training & Test
      </h1>

      <ModeSelector onModeChange={handleModeChange} />

      <section
        style={{
          backgroundColor: "#FFF9F2",
          padding: 24,
          borderRadius: 16,
          width: "100%",
          maxWidth: 520,
        }}
      >
        <h2 style={{ fontSize: 20, fontWeight: 700 }}>
          Hint Source
        </h2>

        <select
          value={source}
          onChange={(e) =>
            handleSourceChange(e.target.value as HintSource)
          }
          disabled={loading}
          style={{
            width: "100%",
            padding: 12,
            marginTop: 12,
            border: "1px solid #B88B68",
            borderRadius: 8,
          }}
        >
          <option value="demo">Demo Mode</option>
          <option value="api">API Mode</option>
        </select>

        {source === "api" && (
          <div style={{ marginTop: 16 }}>
            <label htmlFor="session-id">
              Session ID
            </label>

            <input
              id="session-id"
              value={sessionId}
              onChange={(e) => setSessionId(e.target.value)}
              placeholder="Enter Session ID"
              disabled={loading}
              style={{
                width: "100%",
                padding: 12,
                marginTop: 8,
                border: "1px solid #B88B68",
                borderRadius: 8,
              }}
            />
          </div>
        )}
      </section>

      {mode && (
        <HintPanel
          mode={mode}
          hintLevel={hintLevel}
          hintText={hintText}
          onRequestHint={handleRequestHint}
          onDismiss={() => setHintText(null)}
          loading={loading}
        />
      )}

{hintEvents.length > 0 && (
  <section
    style={{
      backgroundColor: "#FFF9F2",
      padding: 24,
      borderRadius: 16,
      width: "100%",
      maxWidth: 520,
      color: "#30251F",
    }}
  >
    <h2 style={{ fontSize: 20, fontWeight: 700 }}>
      Hint Usage History
    </h2>

    <p style={{ marginTop: 8, fontSize: 14 }}>
      Total Hints Used: {hintEvents.length}
    </p>

    <ul style={{ marginTop: 16, paddingLeft: 20 }}>
      {hintEvents.map((event, index) => (
        <li key={index} style={{ marginBottom: 12 }}>
          <strong>Hint Level {event.level}</strong>

          <p>Source: {event.source}</p>

          <p>
            Time:{" "}
            {new Date(event.timestamp).toLocaleTimeString()}
          </p>

          <p>Reason: {event.reason}</p>
        </li>
      ))}
    </ul>
  </section>
)}

      {error && (
        <p
          role="alert"
          style={{
            color: "#B95D50",
            backgroundColor: "#FFF9F2",
            padding: 16,
            borderRadius: 10,
            maxWidth: 520,
            width: "100%",
          }}
        >
          {error}
        </p>
      )}

      <p style={{ fontSize: 13, color: "#75533E" }}>
        Development Preview — Feature 06
      </p>
    </main>
  );
}
