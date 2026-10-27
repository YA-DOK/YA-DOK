
import { Alexandria } from "next/font/google";
import Image from "next/image";
import type { ReactNode } from "react";

const alexandria = Alexandria({
  subsets: ["arabic", "latin"],
  display: "swap",
});

type AuthShellProps = {
  title: string;
  description: string;
  children: ReactNode;
};

export function AuthShell({
  title,
  description,
  children,
}: AuthShellProps) {
  return (
    <div
      dir="rtl"
      className={`${alexandria.className} relative isolate min-h-dvh overflow-x-clip bg-[#0B2420] text-[#F4F1E8]`}
    >
      <style>{`
        @keyframes yd3-orb-one {
          0%, 100% { transform: translate(0, 0) scale(1); }
          50% { transform: translate(-100px, 55px) scale(1.15); }
        }

        @keyframes yd3-orb-two {
          0%, 100% { transform: translate(0, 0) scale(1); }
          50% { transform: translate(90px, -70px) scale(1.2); }
        }

        @keyframes yd3-grid {
          from { background-position: 0 0; }
          to { background-position: 48px 48px; }
        }

        @keyframes yd3-wave {
          from { stroke-dashoffset: 0; }
          to { stroke-dashoffset: -150; }
        }

        @keyframes yd3-signal {
          from { stroke-dashoffset: 700; }
          to { stroke-dashoffset: -700; }
        }

        @keyframes yd3-glow {
          0%, 100% { opacity: 0.35; transform: scale(1); }
          50% { opacity: 1; transform: scale(1.3); }
        }

        @keyframes yd3-enter {
          from { opacity: 0; transform: translateY(12px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .yd3-orb-one {
          animation: yd3-orb-one 16s ease-in-out infinite;
        }

        .yd3-orb-two {
          animation: yd3-orb-two 20s ease-in-out infinite;
        }

        .yd3-grid {
          animation: yd3-grid 12s linear infinite;
        }

        .yd3-wave {
          animation: yd3-wave 8s linear infinite;
        }

        .yd3-signal {
          stroke-dasharray: 90 700;
          animation: yd3-signal 4s linear infinite;
        }

        .yd3-glow {
          animation: yd3-glow 2.5s ease-in-out infinite;
        }

        .yd3-enter {
          animation: yd3-enter 0.55s ease-out both;
        }

        @media (prefers-reduced-motion: reduce) {
          .yd3-orb-one,
          .yd3-orb-two,
          .yd3-grid,
          .yd3-wave,
          .yd3-signal,
          .yd3-glow,
          .yd3-enter {
            animation: none !important;
          }
        }
      `}</style>

      {/* Background */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 overflow-hidden"
      >
        <div
          className="absolute inset-0"
          style={{
            background:
              "linear-gradient(125deg, #0A201D 0%, #12362F 55%, #0B2420 100%)",
          }}
        />

        <div className="yd3-orb-one absolute -right-36 -top-36 h-[500px] w-[500px] rounded-full bg-[#5AAE89]/25 blur-[100px]" />

        <div className="yd3-orb-two absolute -bottom-40 -left-36 h-[480px] w-[480px] rounded-full bg-[#C5A16C]/20 blur-[100px]" />

        <div
          className="yd3-grid absolute inset-0 opacity-20"
          style={{
            backgroundImage:
              "linear-gradient(#A0D2BB12 1px, transparent 1px), linear-gradient(90deg, #A0D2BB12 1px, transparent 1px)",
            backgroundSize: "48px 48px",
          }}
        />

        <svg
          viewBox="0 0 1200 250"
          preserveAspectRatio="none"
          className="absolute bottom-[4%] left-0 h-44 w-full opacity-35"
          fill="none"
        >
          <path
            className="yd3-wave"
            d="M-100 135 C120 25 260 220 470 135 S850 35 1300 135"
            stroke="#A7D8BA"
            strokeWidth="1.5"
            strokeDasharray="9 15"
          />
          <path
            className="yd3-wave"
            d="M-100 170 C120 60 260 255 470 170 S850 70 1300 170"
            stroke="#C5A16C"
            strokeWidth="1"
            strokeDasharray="9 15"
          />
        </svg>
      </div>

      {/* Main layout */}
      <main className="relative z-10 mx-auto grid min-h-dvh w-full max-w-[1180px] grid-cols-1 items-center gap-8 px-4 py-5 sm:px-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,450px)] lg:gap-12 lg:px-8 lg:py-4">

        {/* Brand / Hero */}
        <section className="yd3-enter hidden lg:block">
          <div className="max-w-[510px]">

            <div className="mb-6 flex items-center gap-3 text-sm text-[#D6B886]">
              <span className="h-px w-9 bg-[#D6B886]" />
              <span>يادوك | محاكاة طبية ذكية</span>
            </div>

            <h2 className="text-[clamp(2.5rem,3.5vw,3.4rem)] font-bold leading-[1.4] tracking-tight">
              فكّر كطبيب.
              <span className="mt-1 block text-[#A7D8BA]">
                واتدرّب بذكاء.
              </span>
            </h2>

            <p className="mt-5 max-w-[430px] text-base leading-9 text-[#C6D9CF]">
              خوض تجارب طبية تفاعلية، حلّل الحالات،
              واتعلّم من قراراتك في بيئة تدريب
              مدعومة بالذكاء الاصطناعي.
            </p>

            {/* Compact animated clinical element */}
            <div className="mt-8 max-w-[430px] rounded-2xl border border-white/15 bg-white/[0.06] p-5 shadow-xl backdrop-blur-xl">

              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">
                  التفكير السريري
                </span>

                <span className="flex items-center gap-2 text-xs text-[#A7D8BA]">
                  <span className="yd3-glow h-2 w-2 rounded-full bg-[#A7D8BA]" />
                  محاكاة تفاعلية
                </span>
              </div>

              <svg
                viewBox="0 0 700 100"
                className="mt-3 h-[66px] w-full"
                fill="none"
                aria-hidden="true"
              >
                <path
                  id="yd3-heartbeat"
                  d="M0 55 H125 L155 55 L180 34 L205 79 L240 12 L274 55 H410 L435 46 L455 55 H530 L555 55 L580 30 L603 78 L635 20 L663 55 H700"
                  stroke="#A7D8BA"
                  strokeWidth="2.5"
                  opacity="0.35"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />

                <path
                  className="yd3-signal"
                  d="M0 55 H125 L155 55 L180 34 L205 79 L240 12 L274 55 H410 L435 46 L455 55 H530 L555 55 L580 30 L603 78 L635 20 L663 55 H700"
                  stroke="#E1BB7B"
                  strokeWidth="3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>

              <div className="flex items-center justify-between text-xs text-[#BED3C7]">
                <span>لاحظ</span>
                <span>حلّل</span>
                <span>قرّر</span>
              </div>
            </div>

            <div className="mt-7 flex items-center gap-3 text-sm text-[#D6B886]">
              <span className="h-px w-10 bg-[#D6B886]/60" />
              من الفهم إلى الممارسة
            </div>
          </div>
        </section>

        {/* Authentication Card */}
        <section className="yd3-enter mx-auto w-full max-w-[450px] rounded-[24px] border border-white/40 bg-[#F3F2EB]/[0.94] px-6 py-5 text-[#18352F] shadow-[0_24px_70px_rgba(0,0,0,0.22)] backdrop-blur-2xl sm:px-8">

          <div className="mb-4 flex flex-col items-center text-center">

            {/* Main Logo */}
            <div className="mb-3 flex h-[82px] w-[235px] items-center justify-center rounded-2xl bg-white shadow-sm">
              <Image
                src="/brand/yadok-logo.png"
                alt="شعار يادوك"
                width={205}
                height={77}
                priority
                className="h-auto max-h-[72px] w-[205px] object-contain"
              />
            </div>

            <h1 className="text-[26px] font-bold leading-tight">
              {title}
            </h1>

            <p className="mt-2 text-sm leading-6 text-[#60766D]">
              {description}
            </p>
          </div>

          {children}
        </section>
      </main>
    </div>
  );
}
