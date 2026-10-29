import type { ReactNode } from "react";

type IconName = "home" | "play" | "compass" | "history" | "chart" | "trophy" | "zap" | "user" | "settings" | "globe" | "sun" | "moon" | "arrow" | "chevron" | "spark" | "menu" | "close" | "clock" | "target" | "book" | "activity" | "stethoscope" | "lock" | "check" | "bell" | "message" | "send" | "shield";

const paths: Record<IconName, ReactNode> = {
  home: <><path d="m3 10 9-7 9 7v10H3z"/><path d="M9 20v-7h6v7"/></>,
  play: <><circle cx="12" cy="12" r="9"/><path d="m10 8 6 4-6 4z"/></>,
  compass: <><circle cx="12" cy="12" r="9"/><path d="m15.9 8.1-2.3 5.5-5.5 2.3 2.3-5.5z"/></>,
  history: <><path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5M12 7v5l3 2"/></>,
  chart: <><path d="M4 20V5m0 15h16M8 16l4-5 3 2 5-7"/></>,
  trophy: <><path d="M7 3h10v7a5 5 0 0 1-10 0zM7 5H4v3a4 4 0 0 0 4 4m9-7h3v3a4 4 0 0 1-4 4M12 15v5m-4 0h8"/></>,
  zap: <path d="m13 2-9 12h7l-1 8 10-13h-7z"/>,
  user: <><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></>,
  settings: <><circle cx="12" cy="12" r="3"/><path d="M19.5 12a7.5 7.5 0 0 0-.1-1.2l2-1.5-2-3.5-2.3.9a8.3 8.3 0 0 0-2-1.2L14.7 3h-4l-.4 2.5a8.3 8.3 0 0 0-2 1.2L6 5.8 4 9.3l2 1.5a8.3 8.3 0 0 0 0 2.4l-2 1.5 2 3.5 2.3-.9a8.3 8.3 0 0 0 2 1.2l.4 2.5h4l.4-2.5a8.3 8.3 0 0 0 2-1.2l2.3.9 2-3.5-2-1.5c.1-.4.1-.8.1-1.2z"/></>,
  globe: <><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c-4 5-4 13 0 18M12 3c4 5 4 13 0 18"/></>,
  sun: <><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M4.9 4.9l1.4 1.4m11.4 11.4 1.4 1.4M2 12h2m16 0h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></>,
  moon: <path d="M20.5 13.2A9 9 0 0 1 10.8 3.5 9 9 0 1 0 20.5 13.2Z"/>,
  arrow: <path d="M5 12h14m-6-6 6 6-6 6"/>,
  chevron: <path d="m9 18 6-6-6-6"/>,
  spark: <><path d="m12 2 2.1 7.9L22 12l-7.9 2.1L12 22l-2.1-7.9L2 12l7.9-2.1z"/></>,
  menu: <path d="M4 7h16M4 12h16M4 17h16"/>,
  close: <path d="m5 5 14 14M19 5 5 19"/>,
  clock: <><circle cx="12" cy="12" r="9"/><path d="M12 7v5l4 2"/></>,
  target: <><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/></>,
  book: <><path d="M12 6c-3-2-6-2-9-1v14c3-1 6-1 9 1m0-14c3-2 6-2 9-1v14c-3-1-6-1-9 1zM12 6v14"/></>,
  activity: <path d="M2 12h5l3-7 4 14 3-7h5"/>,
  stethoscope: <><path d="M6 3v5a6 6 0 0 0 12 0V3M4 3h4m8 0h4M12 14v4a4 4 0 0 0 8 0v-2"/><circle cx="20" cy="14" r="2"/></>,
  lock: <><rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/></>,
  check: <path d="m5 12 5 5L20 7"/>,
  bell: <><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"/><path d="M10 21h4"/></>,
  message: <><path d="M20 11.5A8.5 8.5 0 0 1 11.5 20H4l1.6-4A8.5 8.5 0 1 1 20 11.5Z"/><path d="M8 11.5h8M8 15h4"/></>,
  send: <><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></>,
  shield: <><path d="M12 2 20 5v6c0 5-3.2 8-8 11-4.8-3-8-6-8-11V5z"/><path d="m9 12 2 2 4-4"/></>,
};
export function DashboardIcon({ name, size = 20, className }: { name: IconName; size?: number; className?: string }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" className={className}>{paths[name]}</svg>;
}
export type { IconName };
