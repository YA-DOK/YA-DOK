
"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, type ReactNode } from "react";

import { LogoutButton } from "@/components/auth/logout-button";

type DashboardShellProps = {
  name: string;
  email: string;
  children: ReactNode;
};

export function DashboardShell({
  name,
  email,
  children,
}: DashboardShellProps) {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);

  const initial = Array.from(name)[0] || "ي";
  const dashboardActive = pathname === "/dashboard";

  return (
    <div
      dir="rtl"
      className="min-h-dvh bg-[#F5F7F4] text-[#183B32]"
    >
      {/* Mobile overlay */}
      {menuOpen && (
        <button
          type="button"
          aria-label="إغلاق القائمة"
          onClick={() => setMenuOpen(false)}
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 right-0 z-50 flex w-[260px] flex-col bg-[#123A31] text-white shadow-xl transition-transform duration-300 lg:translate-x-0 ${
          menuOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        <div className="border-b border-white/10 px-5 py-5">
          <div className="flex items-center justify-between gap-2">
            <div className="rounded-xl bg-[#F8F6ED] p-2">
              <Image
                src="/brand/yadok-logo.png"
                alt="يادوك"
                width={165}
                height={65}
                priority
                className="h-[58px] w-[165px] object-contain"
              />
            </div>

            <button
              type="button"
              onClick={() => setMenuOpen(false)}
              aria-label="إغلاق القائمة"
              className="rounded-lg p-2 hover:bg-white/10 lg:hidden"
            >
              ✕
            </button>
          </div>

          <p className="mt-4 text-xs text-[#BDD5C8]">
            منصة التدريب الطبي الذكي
          </p>
        </div>

        {/* Navigation */}
        <nav
          aria-label="التنقل الرئيسي"
          className="flex-1 space-y-2 px-4 py-6"
        >
          <Link
            href="/dashboard"
            onClick={() => setMenuOpen(false)}
            aria-current={dashboardActive ? "page" : undefined}
            className={`flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition ${
              dashboardActive
                ? "bg-[#D1E7D8] text-[#173D32]"
                : "text-[#D0E2D7] hover:bg-white/10"
            }`}
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              aria-hidden="true"
            >
              <rect x="3" y="3" width="7" height="7" rx="1.5" />
              <rect x="14" y="3" width="7" height="7" rx="1.5" />
              <rect x="3" y="14" width="7" height="7" rx="1.5" />
              <rect x="14" y="14" width="7" height="7" rx="1.5" />
            </svg>

            لوحة التحكم
          </Link>

          {/* Future navigation */}
          <div
            aria-disabled="true"
            className="flex items-center justify-between gap-2 rounded-xl px-4 py-3 text-sm text-white/40"
          >
            <span className="flex items-center gap-3">
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <path d="M6 3v5a6 6 0 0 0 12 0V3" />
                <path d="M6 3H4v5a8 8 0 0 0 16 0V3h-2" />
                <path d="M12 16v2a4 4 0 0 0 8 0v-2" />
                <circle cx="20" cy="14" r="2" />
              </svg>
              الحالات الطبية
            </span>

            <span className="text-[10px]">قريبًا</span>
          </div>
        </nav>

        {/* User footer */}
        <div className="border-t border-white/10 p-4">
          <div className="mb-4 flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#D1E7D8] font-bold text-[#173D32]">
              {initial}
            </div>

            <div className="min-w-0">
              <p className="truncate text-sm font-semibold">
                {name}
              </p>
              <p
                dir="ltr"
                className="truncate text-left text-xs text-[#B9CEC1]"
              >
                {email}
              </p>
            </div>
          </div>

          <div className="rounded-xl bg-white p-1 text-[#173D32] [&_button]:w-full">
            <LogoutButton />
          </div>
        </div>
      </aside>

      {/* Main area */}
      <div className="min-h-dvh lg:pr-[260px]">
        <header className="sticky top-0 z-30 border-b border-[#E1E8E1] bg-white/95 backdrop-blur-lg">
          <div className="flex h-[74px] items-center justify-between gap-4 px-4 sm:px-8">
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => setMenuOpen(true)}
                aria-label="فتح القائمة"
                aria-expanded={menuOpen}
                className="rounded-xl border border-[#DAE5DC] p-2.5 hover:bg-[#F1F5F0] lg:hidden"
              >
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  aria-hidden="true"
                >
                  <path d="M4 7h16M4 12h16M4 17h16" />
                </svg>
              </button>

              <div>
                <p className="text-xs text-[#83988A]">
                  يادوك
                </p>
                <p className="font-bold">
                  لوحة التحكم
                </p>
              </div>
            </div>

            <div className="flex min-w-0 items-center gap-3">
              <span className="hidden max-w-[180px] truncate text-sm font-medium sm:block">
                {name}
              </span>

              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-[#CFE0D1] bg-[#E9F1E9] font-semibold text-[#285745]">
                {initial}
              </span>
            </div>
          </div>
        </header>

        <main className="mx-auto w-full max-w-[1320px] px-4 py-7 sm:px-8 lg:py-9">
          {children}
        </main>
      </div>
    </div>
  );
}
