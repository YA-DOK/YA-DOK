
export const instant = false;

export default function DashboardPage() {
  const steps = [
    {
      number: "01",
      title: "اختار حالة طبية",
      description:
        "استكشف الحالات المتاحة وابدأ سيناريو تدريبي مناسب.",
    },
    {
      number: "02",
      title: "ابدأ المحاكاة",
      description:
        "اسأل المريض، اجمع المعلومات، وحاول توصل للتشخيص.",
    },
    {
      number: "03",
      title: "راجع أداءك",
      description:
        "افهم قراراتك واعرف نقاط القوة والتحسين بعد المحاكاة.",
    },
  ];

  return (
    <div className="space-y-8">
      {/* Welcome */}
      <section>
        <p className="text-sm font-medium text-[#6A8A76]">
          الصفحة الرئيسية
        </p>

        <h1 className="mt-2 text-2xl font-bold tracking-tight sm:text-3xl">
          أهلاً بيك في مساحة تدريبك
        </h1>

        <p className="mt-3 max-w-2xl text-sm leading-7 text-[#6B8073]">
          هنا هتتابع رحلتك في التدريب الطبي، وتوصل
          للحالات والمحاكاة والتقييمات لما نجهزها.
        </p>
      </section>

      {/* Main feature */}
      <section className="relative overflow-hidden rounded-[24px] bg-[#153E32] p-6 text-white sm:p-9">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -left-20 -top-24 h-72 w-72 rounded-full border-[45px] border-[#A5CDB0]/10"
        />

        <div
          aria-hidden="true"
          className="pointer-events-none absolute bottom-0 left-0 h-44 w-64 rounded-full bg-[#8ABC94]/10 blur-3xl"
        />

        <div className="relative z-10 max-w-[570px]">
          <span className="inline-flex rounded-full border border-[#C5DFBF]/30 bg-white/10 px-3 py-1.5 text-xs text-[#D5E8D2]">
            التدريب السريري الذكي
          </span>

          <h2 className="mt-5 text-[27px] font-bold leading-[1.55] sm:text-4xl">
            كل حالة جديدة،
            <span className="block text-[#B6D6A8]">
              خبرة أقرب للواقع.
            </span>
          </h2>

          <p className="mt-4 max-w-[490px] text-sm leading-8 text-[#D5E2D8]">
            يادوك هيساعدك تتعامل مع حالات طبية تفاعلية،
            وتتمرن على التفكير السريري واتخاذ القرار
            في بيئة تعليمية آمنة.
          </p>

          <div className="mt-7 inline-flex items-center gap-2 rounded-xl border border-[#E1C89B]/30 bg-[#D5B77F]/10 px-4 py-3 text-sm text-[#F0D6A6]">
            <span className="h-2 w-2 rounded-full bg-[#D5B77F]" />
            مكتبة الحالات قيد التجهيز
          </div>
        </div>
      </section>

      {/* Training flow */}
      <section className="space-y-5">
        <div>
          <h2 className="text-xl font-bold">
            إزاي هتشتغل المحاكاة؟
          </h2>

          <p className="mt-2 text-sm text-[#718777]">
            دي المراحل الأساسية لتجربة التدريب اللي بنجهزها.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          {steps.map((step) => (
            <article
              key={step.number}
              className="rounded-2xl border border-[#E0E8E0] bg-white p-6 shadow-sm"
            >
              <span className="inline-flex h-11 w-11 items-center justify-center rounded-xl bg-[#ECF3EB] text-sm font-bold text-[#397253]">
                {step.number}
              </span>

              <h3 className="mt-5 text-base font-bold">
                {step.title}
              </h3>

              <p className="mt-3 text-sm leading-7 text-[#708376]">
                {step.description}
              </p>
            </article>
          ))}
        </div>
      </section>

      {/* Current status */}
      <section className="flex flex-col gap-4 rounded-2xl border border-[#E3E7DD] bg-[#EEEEE5] p-5 sm:flex-row sm:items-center sm:justify-between sm:p-6">
        <div>
          <h2 className="font-bold text-[#294D3C]">
            حسابك جاهز
          </h2>

          <p className="mt-2 text-sm leading-7 text-[#718174]">
            تقدر تدخل إلى المنصة بأمان. الخطوة التالية
            هي تجهيز مكتبة الحالات وربطها بالمحاكاة.
          </p>
        </div>

        <span className="shrink-0 self-start rounded-full bg-[#DAE8D9] px-4 py-2 text-xs font-semibold text-[#356B47]">
          المرحلة الحالية
        </span>
      </section>
    </div>
  );
}
