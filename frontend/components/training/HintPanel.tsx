
"use client";

import type { SessionMode } from "./ModeSelector";

type HintPanelProps = {
  mode: SessionMode;
  hintLevel: number;
  hintText: string | null;
  onRequestHint: () => void;
  onDismiss: () => void;
  loading?: boolean;
};

const MAX_HINTS = 3;

export default function HintPanel({
  mode,
  hintLevel,
  hintText,
  onRequestHint,
  onDismiss,
  loading = false,
}: HintPanelProps) {
  const isTestMode = mode === "assessment";
  const limitReached = hintLevel >= MAX_HINTS;

  return (
    <section
      style={{
        backgroundColor: "#FFF9F2",
        color: "#30251F",
        padding: 24,
        borderRadius: 16,
        width: "100%",
        maxWidth: 520,
      }}
    >
      <h2 style={{ fontSize: 22, fontWeight: 700 }}>
        Hints & Guidance
      </h2>

      {isTestMode ? (
        <div style={{ marginTop: 20 }}>
          <p>
            Hints are disabled in Test Mode.
          </p>
          <p>
            Complete your session independently.
          </p>
        </div>
      ) : (
        <div style={{ marginTop: 20 }}>
          <p>
            Hints Used: {hintLevel} / {MAX_HINTS}
          </p>

          <p style={{ fontSize: 13, marginTop: 8 }}>
            Hint usage may affect your Score and XP.
          </p>

          {hintText && (
            <div
              role="status"
              style={{
                marginTop: 16,
                padding: 16,
                borderRadius: 12,
                backgroundColor: "#F4E8D9",
                border: "1px solid #B88B68",
              }}
            >
              <strong>Hint Level {hintLevel}</strong>

              <p style={{ marginTop: 10 }}>
                {hintText}
              </p>

              <button
                type="button"
                onClick={onDismiss}
                style={{ marginTop: 12 }}
              >
                Dismiss
              </button>
            </div>
          )}

          <button
            type="button"
            onClick={onRequestHint}
            disabled={limitReached || loading}
            style={{
              marginTop: 20,
              width: "100%",
              padding: 14,
              backgroundColor:
                limitReached ? "#B88B68" : "#49372E",
              color: "#FFFFFF",
              border: "none",
              borderRadius: 10,
              cursor: limitReached ? "not-allowed" : "pointer",
              opacity: loading ? 0.6 : 1,
            }}
          >
            {loading
              ? "Loading..."
              : limitReached
                ? "Hint Limit Reached"
                : "Request Hint"}
          </button>

          <p style={{ marginTop: 12, fontSize: 13 }}>
            Remaining Hints: {Math.max(
              0,
              MAX_HINTS - hintLevel
            )}
          </p>
        </div>
      )}
    </section>
  );
}
