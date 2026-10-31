
"use client";

import VoiceControls from "@/app/components/VoiceControls";

export default function VoiceDemoPage() {
  return (
    <main className="min-h-screen bg-gray-100 p-8">
      <div className="mx-auto max-w-3xl">
        <h1 className="mb-2 text-2xl font-bold text-gray-900">
          YA-DOK Voice Demo
        </h1>

        <p className="mb-6 text-gray-600">
          Testing the voice interaction interface.
        </p>

        <VoiceControls />
      </div>
    </main>
  );
}





