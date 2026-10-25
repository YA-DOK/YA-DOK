"use client";

import dynamic from "next/dynamic";

// Isolated preview route: existing /, /login, /signup and auth files stay untouched.
const ClinicalWorld = dynamic(
  () => import("../../components/landing-lab/ClinicalWorld"),
  {
    ssr: false,
    loading: () => (
      <div className="absolute inset-0 flex items-center justify-center bg-[#071C22] text-[#BEF5EC]">
        Loading the clinical environment...
      </div>
    ),
  },
);

export default function LandingLabPage() {
  return (
    <main className="relative h-[100dvh] w-full overflow-hidden bg-[#071C22]">
      <ClinicalWorld />

      <header className="pointer-events-none absolute left-5 top-5 z-10 md:left-10 md:top-8">
        <span className="block text-xl font-bold tracking-[0.13em] text-white md:text-2xl">
          YA-DOK
        </span>
        <span className="mt-1 block text-[10px] font-medium tracking-[0.2em] text-[#A0E9DB] md:text-xs">
          CLINICAL WORLD / DEVELOPMENT VIEW
        </span>
      </header>

      <aside className="pointer-events-none absolute bottom-5 left-1/2 z-10 w-max max-w-[90vw] -translate-x-1/2 rounded-full border border-white/15 bg-[#092932]/65 px-4 py-2 text-center text-[11px] text-[#E9FAF7] shadow-xl backdrop-blur-xl md:text-xs">
        Drag to rotate · Scroll to zoom · This is a temporary model kit
      </aside>
    </main>
  );
}
