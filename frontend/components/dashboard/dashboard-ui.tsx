"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

export type DashboardLocale = "ar" | "en";
export type DashboardTheme = "light" | "dark";
export type SessionMode = "training" | "test";

type UIContext = {
  locale: DashboardLocale;
  theme: DashboardTheme;
  setLocale: (value: DashboardLocale) => void;
  setTheme: (value: DashboardTheme) => void;
  modalOpen: boolean;
  openSession: () => void;
  closeSession: () => void;
  name: string;
  email: string;
};

const DashboardContext = createContext<UIContext | null>(null);

export function DashboardUIProvider({ children, name, email }: {children: ReactNode; name: string; email: string}) {
  const [locale, setLocaleState] = useState<DashboardLocale>("ar");
  const [theme, setThemeState] = useState<DashboardTheme>("light");
  const [modalOpen, setModalOpen] = useState(false);

  useEffect(() => {
    const frame = requestAnimationFrame(() => {
      try {
        if (localStorage.getItem("yadok-dashboard-locale") === "en") setLocaleState("en");
        if (localStorage.getItem("yadok-dashboard-theme") === "dark") setThemeState("dark");
      } catch { /* Incognito or restricted storage: use defaults */ }
    });
    return () => cancelAnimationFrame(frame);
  }, []);

  const setLocale = (value: DashboardLocale) => {
    setLocaleState(value);
    try { localStorage.setItem("yadok-dashboard-locale", value); } catch { /* optional */ }
  };
  const setTheme = (value: DashboardTheme) => {
    setThemeState(value);
    try { localStorage.setItem("yadok-dashboard-theme", value); } catch { /* optional */ }
  };

  return (
    <DashboardContext.Provider value={{ locale, theme, setLocale, setTheme, modalOpen, openSession: () => setModalOpen(true), closeSession: () => setModalOpen(false), name, email }}>
      {children}
    </DashboardContext.Provider>
  );
}
export function useDashboardUI() {
  const ctx = useContext(DashboardContext);
  if (!ctx) throw new Error("DashboardUIProvider missing");
  return ctx;
}
export function translated(locale: DashboardLocale, ar: string, en: string) {
  return locale === "ar" ? ar : en;
}
