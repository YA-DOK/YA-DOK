
"use client";

import { useState } from "react";

export type SessionMode = "training" | "assessment";

type ModeSelectorProps = {
  onModeChange?: (mode: SessionMode) => void;
};

const modes: {
  id: SessionMode;
  title: string;
  description: string;
}[] = [
  {
    id: "training",
    title: "Training Mode",
    description: "Practice with progressive hints and guidance.",
  },
  {
    id: "assessment",
    title: "Test Mode",
    description: "Test your knowledge without assistance.",
  },
];

export default function ModeSelector({
  onModeChange,
}: ModeSelectorProps) {
  const [selectedMode, setSelectedMode] =
    useState<SessionMode | null>(null);

  const handleSelect = (mode: SessionMode) => {
    setSelectedMode(mode);
    onModeChange?.(mode);
  };

  return (
    <section
      style={{
        maxWidth: 520,
        padding: 24,
        backgroundColor: "#FFF9F2",
        color: "#30251F",
        borderRadius: 16,
      }}
    >
      <h2>Choose Your Mode</h2>

      <p>Select how you want to start your session.</p>

      <div role="radiogroup" aria-label="Session mode">
        {modes.map((mode) => (
          <label
            key={mode.id}
            style={{
              display: "flex",
              gap: 12,
              padding: 16,
              marginTop: 12,
              border: "1px solid #B88B68",
              borderRadius: 12,
              cursor: "pointer",
            }}
          >
            <input
              type="radio"
              name="sessionMode"
              value={mode.id}
              checked={selectedMode === mode.id}
              onChange={() => handleSelect(mode.id)}
            />

            <span>
              <strong>{mode.title}</strong>
              <span style={{ display: "block", marginTop: 6 }}>
                {mode.description}
              </span>
            </span>
          </label>
        ))}
      </div>

      {selectedMode && (
        <p role="status" style={{ marginTop: 20 }}>
          Selected Mode: <strong>{selectedMode}</strong>
        </p>
      )}
    </section>
  );
}
