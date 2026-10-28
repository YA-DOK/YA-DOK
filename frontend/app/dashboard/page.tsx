
type DashboardIconName =
  | "activity"
  | "check"
  | "chart"
  | "clock"
  | "target"
  | "arrow"
  | "book"
  | "sparkles";

function DashboardIcon({
  name,
  className = "h-5 w-5",
}: {
  name: DashboardIconName;
  className?: string;
}) {
  const paths: Record<DashboardIconName, React.ReactNode> = {
    activity: <path d="M3 12h4l3-8 4 16 3-8h4" />,
    check: <path d="m5 12 4 4L19 6" />,
    chart: (
      <>
        <path d="M4 20V10M10 20V4M16 20v-8M22 20v-5" />
      </>
    ),
    clock: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v5l3 2" />
      </>
    ),
    target: (
      <>
        <circle cx="12" cy="12" r="9" />
        <circle cx="12" cy="12" r="5" />
        <circle cx="12" cy="12" r="1" />
      </>
    ),
    arrow: <path d="M5 12h14m-6-6 6 6-6 6" />,
    book: (
      <>
        <path d="M12 6c-3-2-7-2-10-1v14c4-1 7-1 10 1" />
        <path d="M12 6c3-2 7-2 10-1v14c-4-1-7-1-10 1" />
        <path d="M12 6v14" />
      </>
    ),
    sparkles: (
      <>
        <path d="m12 3 1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3Z" />
        <path d="m19 17 .7 2.3L22 20l-2.3.7L19 23l-.7-2.3L16 20l2.3-.7L19 17Z" />
      </>
    ),
  };

  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className={className}
    >
      {paths[name]}
    </svg>
  );
}

type StatCardProps = {
  title: string;
  description: string;
  icon: DashboardIconName;
};

function StatCard({ title, description, icon }: StatCardProps) {
  return (
    <article className="rounded-[22px] border border-[#E2EAE3] bg-white p-5 shadow-sm transition-shadow hover:shadow-md sm:p-6">
      <div className="flex items-start justify-between gap-3">
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#EAF3E9] text-[#24664F]">
          <DashboardIcon name={icon} className="h-6 w-6" />
        </div>
        <span className="rounded-full bg-[#F2F5F0] px-3 py-1 text-[11px] font-medium text-[#738779]">
          بانتظار البيانات
        </span>
      </div>

      <h3 className="mt-5 text-sm font-semibold text-[#6F8275]">
        {title}
      </h3>
      <p className="mt-3 text-2xl font-bold text-[#153F35]">
        —
      </p>
      <p className="mt-2 text-xs leading-6 text-[#829388]">
        {description}
      </p>
    </article>
  );
}

function EmptyState({
  icon,
  title,
  description,
}: {
  icon: DashboardIconName;
  title: string;
  description: string;
}) {
  return (
    <div className="flex min-h-[230px] flex-col items-center justify-center px-5 py-9 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-[#EDF4EC] text-[#397253]">
        <DashboardIcon name={icon} className="h-8 w-8" />
      </div>
      <h3 className="mt-5 text-base font-bold text-[#254B3D]">
        {title}
      </h3>
      <p className="mt-2 max-w-sm text-sm leading-7 text-[#819185]">
        {description}
      </p>
    </div>
  );
}

const statistics: StatCardProps[] = [
  {
    title: "الجلسات المكتملة",
    description: "عدد جلسات المحاكاة التي أنهيتها.",
    icon: "check",
  },
  {
    title: "إجمالي الجلسات",
    description: "إجمالي جلسات التدريب المسجلة.",
    icon: "activity",
  },
  {
    title: "متوسط التقييم",
    description: "متوسط درجاتك في جلسات التدريب المقيمة.",
    icon: "chart",
  },
  {
    title: "مستوى التقدم",
    description: "نسبة التقدم بناءً على جلساتك التدريبية.",
    icon: "target",
  },
];

const learningSteps = [
  {
    number: "01",
    title: "استكشف الحالات",
    description: "اختار حالة طبية مناسبة لمستواك.",
  },
  {
    number: "02",
    title: "ابدأ التدريب",
    description: "تفاعل مع المريض واجمع المعلومات.",
  },
  {
    number: "03",
    title: "راجع تقييمك",
    description: "تعرف على نقاط القوة وفرص التحسين.",
  },
];

export const instant = false;

export default function DashboardPage() {
  return (
    <div dir="rtl" className="space-y-8 pb-8">
      {/* Welcome section */}
      <section className="relative overflow-hidden rounded-[26px] bg-[#153F35] px-6 py-8 text-white sm:px-9 sm:py-10 lg:px-12">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -left-16 -top-24 h-72 w-72 rounded-full border-[45px] border-[#B9D9C1]/10"
        />
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -bottom-24 left-24 h-64 w-64 rounded-full bg-[#80B891]/10 blur-3xl"
        />

        <div className="relative z-10 max-w-2xl">
          <span className="inline-flex items-center gap-2 rounded-full border border-[#BBD7C3]/25 bg-white/10 px-4 py-2 text-xs font-semibold text-[#D5EAD7]">
            <DashboardIcon name="sparkles" className="h-4 w-4" />
            مساحة التدريب الخاصة بك
          </span>

          <h1 className="mt-6 text-2xl font-bold leading-relaxed sm:text-3xl lg:text-4xl">
            أهلاً بيك في رحلتك الطبية
            <span className="mt-1 block text-[#B8DDAF]">
              كل خطوة تدريب بتفرق.
            </span>
          </h1>

          <p className="mt-5 max-w-xl text-sm leading-8 text-[#DBE8DF] sm:text-base">
            هنا هتقدر تتابع تقدمك في المحاكاة السريرية،
            وتراجع تقييماتك، وتكتشف المهارات اللي محتاج
            تطورها علشان تكون أكثر استعدادًا للتعامل
            مع الحالات الطبية.
          </p>

          <div className="mt-7 inline-flex items-center gap-2 rounded-xl border border-white/15 bg-white/10 px-4 py-3 text-xs font-medium text-[#E5F0E6]">
            <span className="h-2 w-2 rounded-full bg-[#BDD9A8]" />
            إحصائيات التدريب هتظهر عند توفر بيانات الجلسات
          </div>
        </div>
      </section>

      {/* Progress overview */}
      <section aria-labelledby="progress-heading">
        <div className="mb-5">
          <h2
            id="progress-heading"
            className="text-xl font-bold text-[#183F33] sm:text-2xl"
          >
            نظرة عامة على تقدمك
          </h2>
          <p className="mt-2 text-sm text-[#75897A]">
            مؤشرات أدائك خلال رحلتك التدريبية.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {statistics.map((stat) => (
            <StatCard key={stat.title} {...stat} />
          ))}
        </div>
      </section>

      {/* Training history and evaluation */}
      <div className="grid gap-6 xl:grid-cols-2">
        <section
          aria-labelledby="sessions-heading"
          className="overflow-hidden rounded-[22px] border border-[#E2EAE3] bg-white shadow-sm"
        >
          <div className="border-b border-[#EDF0EB] px-6 py-5">
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-[#EDF4EC] p-2.5 text-[#397253]">
                <DashboardIcon name="clock" />
              </div>
              <div>
                <h2
                  id="sessions-heading"
                  className="text-lg font-bold text-[#214A39]"
                >
                  أحدث جلسات التدريب
                </h2>
                <p className="mt-1 text-xs text-[#87978A]">
                  آخر الحالات الطبية التي تدربت عليها
                </p>
              </div>
            </div>
          </div>

          <EmptyState
            icon="book"
            title="سجل الجلسات غير متاح حاليًا"
            description="هنعرض هنا آخر جلسات المحاكاة بمجرد ربط بيانات التدريب بالداشبورد."
          />
        </section>

        <section
          aria-labelledby="evaluation-heading"
          className="overflow-hidden rounded-[22px] border border-[#E2EAE3] bg-white shadow-sm"
        >
          <div className="border-b border-[#EDF0EB] px-6 py-5">
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-[#EDF4EC] p-2.5 text-[#397253]">
                <DashboardIcon name="chart" />
              </div>
              <div>
                <h2
                  id="evaluation-heading"
                  className="text-lg font-bold text-[#214A39]"
                >
                  الأداء والتقييم
                </h2>
                <p className="mt-1 text-xs text-[#87978A]">
                  نتائجك ونقاط القوة وفرص التحسين
                </p>
              </div>
            </div>
          </div>

          <EmptyState
            icon="chart"
            title="التقييمات غير متاحة حاليًا"
            description="نتائج التقييم وتحليل مهاراتك هتظهر هنا بعد ربط نظام التقييم."
          />
        </section>
      </div>

      {/* Personalized challenges */}
      <section
        aria-labelledby="challenges-heading"
        className="overflow-hidden rounded-[22px] border border-[#E2EAE3] bg-white shadow-sm"
      >
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#EDF0EB] px-6 py-5">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-[#EDF4EC] p-2.5 text-[#397253]">
              <DashboardIcon name="target" />
            </div>
            <div>
              <h2
                id="challenges-heading"
                className="text-lg font-bold text-[#214A39]"
              >
                تدريبات مقترحة ليك
              </h2>
              <p className="mt-1 text-xs text-[#87978A]">
                تدريبات مخصصة بناءً على أدائك
              </p>
            </div>
          </div>

          <span className="rounded-full bg-[#EFF5ED] px-3 py-1.5 text-xs font-semibold text-[#578067]">
            قيد التجهيز
          </span>
        </div>

        <EmptyState
          icon="sparkles"
          title="توصياتك الشخصية هتظهر هنا"
          description="عند توفر نتائج التقييم ونظام التوصيات، هتقدر تشوف تدريبات مناسبة للمهارات اللي محتاج تطورها."
        />
      </section>

      {/* Getting started */}
      <section className="rounded-[22px] border border-[#DCE8DC] bg-[#EAF3E9] p-6 sm:p-8">
        <div className="flex items-center gap-3">
          <DashboardIcon
            name="book"
            className="h-6 w-6 text-[#31704E]"
          />
          <h2 className="text-xl font-bold text-[#194333]">
            رحلتك التدريبية مع يادوك
          </h2>
        </div>

        <p className="mt-3 text-sm leading-7 text-[#66816B]">
          دي الخطوات الأساسية لتجربة التدريب السريري
          اللي بنجهزها ليك.
        </p>

        <div className="mt-7 grid gap-4 md:grid-cols-3">
          {learningSteps.map((step) => (
            <div
              key={step.number}
              className="rounded-2xl border border-[#DCE8DC] bg-white p-5"
            >
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#E6F1E4] text-sm font-bold text-[#34734F]">
                {step.number}
              </span>

              <h3 className="mt-4 font-bold text-[#214B39]">
                {step.title}
              </h3>
              <p className="mt-2 text-sm leading-7 text-[#789080]">
                {step.description}
              </p>
            </div>
          ))}
        </div>
      </section>

      <footer className="pt-2 text-center text-xs text-[#91A095]">
        YA-DOK — منصة المحاكاة والتدريب الطبي الذكي
      </footer>
    </div>
  );
}
