import { useState } from "react";
import {
  BarChart3,
  BookOpenCheck,
  CalendarDays,
  ChevronRight,
  CheckCircle2,
  CircleDollarSign,
  ClipboardCheck,
  FileCheck2,
  FileDown,
  Loader2,
  GraduationCap,
  School,
  TrendingUp,
  UserRoundCog,
  Users,
  WalletCards,
} from "lucide-react";

import { useI18n } from "../../i18n";
import { notifyError } from "../../lib/toast";
import api from "../../services/api";
import ClassroomStatisticsModal from "./ClassroomStatisticsModal";


const assessmentStatusOrder = [
  "DRAFT",
  "INPUT",
  "SUBMITTED",
  "VALIDATED",
  "PUBLISHED",
];

const genderOrder = ["MALE", "FEMALE", "OTHER", "UNKNOWN"];

function clamp(value, min = 0, max = 100) {
  return Math.min(max, Math.max(min, Number(value) || 0));
}

function formatNumber(value, language) {
  return new Intl.NumberFormat(
    language === "en" ? "en-US" : "fr-FR"
  ).format(Number(value || 0));
}

function formatMoney(value, currency, language) {
  const amount = Number(value || 0);
  try {
    return new Intl.NumberFormat(
      language === "en" ? "en-US" : "fr-FR",
      {
        style: "currency",
        currency: currency || "XAF",
        maximumFractionDigits: 0,
      }
    ).format(amount);
  } catch {
    return `${formatNumber(amount, language)} ${currency || "XAF"}`;
  }
}

function monthLabel(year, month, language) {
  return new Intl.DateTimeFormat(
    language === "en" ? "en-US" : "fr-FR",
    { month: "short" }
  ).format(new Date(year, month - 1, 1));
}

function StatCard({
  label,
  value,
  detail,
  icon: Icon,
  emphasis = false,
}) {

  return (
    <div
      className={`tenant-card rounded-2xl border p-4 shadow-sm sm:p-5 ${
        emphasis
          ? "tenant-primary-border tenant-primary-soft"
          : "border-slate-200 bg-white"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-xs font-medium text-slate-500 sm:text-sm">
            {label}
          </div>
          <div className="mt-3 break-words text-2xl font-semibold tracking-tight sm:text-3xl">
            {value}
          </div>
          {detail && (
            <div className="mt-1.5 text-xs leading-5 text-slate-400">
              {detail}
            </div>
          )}
        </div>
        <div className="tenant-primary-soft tenant-primary-text grid h-10 w-10 shrink-0 place-items-center rounded-xl">
          <Icon size={18} />
        </div>
      </div>
    </div>
  );
}

function SectionCard({ title, subtitle, icon: Icon, children }) {
  return (
    <section className="tenant-card rounded-3xl border border-slate-200 bg-white p-4 shadow-sm sm:p-6">
      <div className="flex items-start gap-3">
        {Icon && (
          <div className="tenant-primary-soft tenant-primary-text grid h-10 w-10 shrink-0 place-items-center rounded-xl">
            <Icon size={18} />
          </div>
        )}
        <div className="min-w-0">
          <h2 className="font-semibold">{title}</h2>
          {subtitle && (
            <p className="mt-1 text-xs leading-5 text-slate-500 sm:text-sm">
              {subtitle}
            </p>
          )}
        </div>
      </div>
      <div className="mt-5">{children}</div>
    </section>
  );
}

function ProgressBar({ value, muted = false }) {
  const width = clamp(value);
  return (
    <div className="h-2 overflow-hidden rounded-full bg-slate-100">
      <div
        className={`h-full rounded-full transition-all ${
          muted ? "bg-slate-400" : "tenant-primary-bg"
        }`}
        style={{ width: `${width}%` }}
      />
    </div>
  );
}

function EmptyState({ children }) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50/70 px-4 py-8 text-center text-sm text-slate-500">
      {children}
    </div>
  );
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export default function DashboardAnalytics({
  dashboard,
  portalAddress,
}) {
  const { t, language } = useI18n();
  const [selectedClassroom, setSelectedClassroom] = useState(null);
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const analytics = dashboard.analytics || {};
  const year = analytics.academic_year;
  const population = analytics.population || {
    gender: [],
    cycles: [],
    classrooms: [],
  };
  const academics = analytics.academics;
  const finance = analytics.finance;
  const teacher = analytics.teacher;
  const overview = analytics.overview || {};
  const isTeacherScope = analytics.scope === "TEACHER";

  const gender = genderOrder
    .map((key) =>
      population.gender?.find((item) => item.key === key)
    )
    .filter(Boolean);

  const male = gender.find((item) => item.key === "MALE");
  const female = gender.find((item) => item.key === "FEMALE");
  const malePct = clamp(male?.percentage || 0);
  const femalePct = clamp(female?.percentage || 0);
  const otherStart = Math.min(100, malePct + femalePct);

  const genderBackground = `conic-gradient(
    var(--school-primary) 0% ${malePct}%,
    var(--school-secondary) ${malePct}% ${otherStart}%,
    rgb(148 163 184) ${otherStart}% 100%
  )`;

  const cycles = population.cycles || [];
  const maxCycle = Math.max(
    1,
    ...cycles.map((item) => Number(item.count || 0))
  );

  const classrooms = population.classrooms || [];
  const maxClass = Math.max(
    1,
    ...classrooms.map((item) => Number(item.count || 0))
  );

  const monthly = finance?.monthly_collections || [];
  const maxMonthly = Math.max(
    1,
    ...monthly.map((item) => Number(item.amount || 0))
  );

  const kpis = isTeacherScope
    ? [
        {
          label: t("dashboard.stats.myStudents"),
          value: formatNumber(
            teacher?.students_count ?? overview.students,
            language
          ),
          detail: t("dashboard.stats.currentYear"),
          icon: Users,
        },
        {
          label: t("dashboard.stats.myClasses"),
          value: formatNumber(
            teacher?.classes_count ?? overview.classes,
            language
          ),
          detail: year?.name || t("dashboard.stats.noActiveYear"),
          icon: GraduationCap,
        },
        {
          label: t("dashboard.stats.myAssignments"),
          value: formatNumber(
            teacher?.assignments_count || 0,
            language
          ),
          detail: t("dashboard.stats.activeAssignments"),
          icon: BookOpenCheck,
        },
        {
          label: t("dashboard.stats.assessmentsPublished"),
          value: `${academics?.publication_rate || 0}%`,
          detail: t("dashboard.stats.publishedOf", {
            published: academics?.published_assessments || 0,
            total: academics?.assessments_total || 0,
          }),
          icon: ClipboardCheck,
          emphasis: true,
        },
      ]
    : [
        {
          label: t("dashboard.stats.enrolledStudents"),
          value: formatNumber(overview.students, language),
          detail: year?.name || t("dashboard.stats.noActiveYear"),
          icon: Users,
        },
        {
          label: t("dashboard.stats.activeClasses"),
          value: formatNumber(overview.classes, language),
          detail: t("dashboard.stats.currentYear"),
          icon: GraduationCap,
        },
        {
          label: t("dashboard.stats.activeTeachers"),
          value: formatNumber(overview.teachers, language),
          detail: t("dashboard.stats.schoolWide"),
          icon: UserRoundCog,
        },
        finance
          ? {
              label: t("dashboard.stats.collectionRate"),
              value: `${finance.collection_rate || 0}%`,
              detail: t("dashboard.stats.collectedShort", {
                amount: formatMoney(
                  finance.collected_total,
                  finance.currency,
                  language
                ),
              }),
              icon: TrendingUp,
              emphasis: true,
            }
          : {
              label: t("dashboard.stats.assessmentsPublished"),
              value: `${academics?.publication_rate || 0}%`,
              detail: t("dashboard.stats.publishedOf", {
                published: academics?.published_assessments || 0,
                total: academics?.assessments_total || 0,
              }),
              icon: ClipboardCheck,
              emphasis: true,
            },
      ];


  const downloadStatisticsPdf = async () => {
    setDownloadingPdf(true);

    try {
      const { data } = await api.get(
        "/tenant/dashboard/statistics.pdf",
        {
          params: { language },
          responseType: "blob",
        }
      );

      const safeSchool = (
        dashboard.school?.slug || "school"
      ).replace(/[^a-z0-9-_]/gi, "-");

      downloadBlob(
        data,
        `statistics-${safeSchool}.pdf`
      );
    } catch (error) {
      notifyError(
        error?.response?.data?.detail ||
          t("dashboard.stats.pdfDownloadError")
      );
    } finally {
      setDownloadingPdf(false);
    }
  };

  return (
    <div>
      {selectedClassroom && (
        <ClassroomStatisticsModal
          classroom={selectedClassroom}
          onClose={() => setSelectedClassroom(null)}
        />
      )}

      <section
        className="relative overflow-hidden rounded-3xl border tenant-primary-border p-5 shadow-sm sm:p-7"
        style={{
          background:
            "linear-gradient(135deg, rgb(var(--school-primary-rgb) / 0.14), rgb(var(--school-secondary-rgb) / 0.08) 62%, white)",
        }}
      >
        <div
          className="pointer-events-none absolute -right-16 -top-20 h-48 w-48 rounded-full blur-3xl"
          style={{
            background:
              "rgb(var(--school-primary-rgb) / 0.16)",
          }}
        />
        <div className="relative flex flex-col justify-between gap-5 md:flex-row md:items-end">
          <div className="min-w-0">
            <div className="tenant-primary-text text-xs font-semibold uppercase tracking-[0.18em]">
              {dashboard.membership.role_label}
            </div>
            <h1 className="mt-2 break-words text-2xl font-semibold tracking-tight sm:text-3xl">
              {dashboard.school.name}
            </h1>
            <p className="mt-2 break-all text-xs text-slate-500 sm:text-sm">
              {portalAddress}
            </p>

            {isTeacherScope && (
              <div className="mt-4 inline-flex items-center gap-2 rounded-full border border-slate-200/80 bg-white/70 px-3 py-1.5 text-xs text-slate-600 backdrop-blur">
                <School size={13} />
                {t("dashboard.stats.teacherScope")}
              </div>
            )}
          </div>

          <div className="flex min-w-[220px] flex-col gap-2">
            <button
              type="button"
              onClick={downloadStatisticsPdf}
              disabled={downloadingPdf}
              className="tenant-primary-bg inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium text-white shadow-sm transition hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {downloadingPdf ? (
                <Loader2 size={16} className="animate-spin" />
              ) : (
                <FileDown size={16} />
              )}
              {downloadingPdf
                ? t("dashboard.stats.downloadingPdf")
                : t("dashboard.stats.downloadPdf")}
            </button>

            <div className="rounded-2xl border border-white/70 bg-white/75 p-4 backdrop-blur">
            <div className="flex items-center justify-between gap-3 text-xs">
              <span className="font-medium text-slate-600">
                {year?.name || t("dashboard.stats.noActiveYear")}
              </span>
              <span className="tenant-primary-text font-semibold">
                {year ? `${Math.round(year.progress || 0)}%` : "—"}
              </span>
            </div>
            <div className="mt-2">
              <ProgressBar value={year?.progress || 0} />
            </div>
            <div className="mt-3 flex items-center justify-between gap-3 text-[11px] text-slate-500">
              <span className="inline-flex items-center gap-1.5">
                <CalendarDays size={12} />
                {analytics.active_period?.name ||
                  t("dashboard.stats.noPeriod")}
              </span>
              <span>
                {t("dashboard.stats.yearProgress")}
              </span>
            </div>
          </div>
          </div>
        </div>
      </section>

      <div className="mt-4 grid grid-cols-2 gap-3 sm:mt-6 sm:gap-4 xl:grid-cols-4">
        {kpis.map((item) => (
          <StatCard key={item.label} {...item} />
        ))}
      </div>

      <div className="mt-4 grid gap-4 sm:mt-6 xl:grid-cols-[1.15fr_.85fr]">
        <SectionCard
          title={t("dashboard.stats.studentsByCycle")}
          subtitle={t("dashboard.stats.studentsByCycleHelp")}
          icon={BarChart3}
        >
          {cycles.length ? (
            <div className="space-y-4">
              {cycles.map((cycle) => (
                <div key={cycle.id}>
                  <div className="flex items-center justify-between gap-3 text-sm">
                    <div className="min-w-0">
                      <div className="truncate font-medium">
                        {cycle.name}
                      </div>
                      <div className="mt-0.5 truncate text-[11px] text-slate-400">
                        {cycle.section_name}
                      </div>
                    </div>
                    <div className="shrink-0 text-right">
                      <div className="font-semibold">
                        {formatNumber(cycle.count, language)}
                      </div>
                      <div className="text-[11px] text-slate-400">
                        {cycle.percentage}%
                      </div>
                    </div>
                  </div>
                  <div className="mt-2 h-2.5 overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="tenant-primary-bg h-full rounded-full"
                      style={{
                        width: `${Math.max(
                          4,
                          (Number(cycle.count || 0) / maxCycle) *
                            100
                        )}%`,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState>
              {t("dashboard.stats.noEnrollmentData")}
            </EmptyState>
          )}
        </SectionCard>

        <SectionCard
          title={t("dashboard.stats.genderDistribution")}
          subtitle={t("dashboard.stats.genderHelp")}
          icon={Users}
        >
          {gender.length ? (
            <div className="grid items-center gap-5 sm:grid-cols-[150px_1fr] xl:grid-cols-1 2xl:grid-cols-[150px_1fr]">
              <div className="mx-auto grid place-items-center">
                <div
                  className="grid h-36 w-36 place-items-center rounded-full"
                  style={{ background: genderBackground }}
                >
                  <div className="grid h-24 w-24 place-items-center rounded-full bg-white text-center shadow-inner">
                    <div>
                      <div className="text-2xl font-semibold">
                        {formatNumber(
                          population.enrollments,
                          language
                        )}
                      </div>
                      <div className="mt-0.5 text-[10px] uppercase tracking-wide text-slate-400">
                        {t("dashboard.stats.students")}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                {gender.map((item) => (
                  <div
                    key={item.key}
                    className="flex items-center justify-between gap-3 rounded-xl bg-slate-50 px-3 py-2.5"
                  >
                    <div className="flex items-center gap-2">
                      <span
                        className={`h-2.5 w-2.5 rounded-full ${
                          item.key === "MALE"
                            ? "tenant-primary-bg"
                            : item.key === "FEMALE"
                            ? "tenant-secondary-dot"
                            : "bg-slate-400"
                        }`}
                        style={
                          item.key === "FEMALE"
                            ? {
                                background:
                                  "var(--school-secondary)",
                              }
                            : undefined
                        }
                      />
                      <span className="text-sm text-slate-600">
                        {t(
                          `dashboard.stats.gender.${item.key.toLowerCase()}`
                        )}
                      </span>
                    </div>
                    <div className="text-right">
                      <span className="font-semibold">
                        {formatNumber(item.count, language)}
                      </span>
                      <span className="ml-2 text-xs text-slate-400">
                        {item.percentage}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <EmptyState>
              {t("dashboard.stats.noGenderData")}
            </EmptyState>
          )}
        </SectionCard>
      </div>

      <div className="mt-4 grid gap-4 sm:mt-6 xl:grid-cols-[1fr_1fr]">
        <SectionCard
          title={t("dashboard.stats.classLoad")}
          subtitle={t("dashboard.stats.classLoadHelp")}
          icon={GraduationCap}
        >
          {classrooms.length ? (
            <div className="tenant-scrollbar max-h-[520px] space-y-3 overflow-y-auto pr-1">
              {classrooms.map((classroom) => {
                const rate =
                  classroom.occupancy_rate ??
                  ((Number(classroom.count || 0) / maxClass) *
                    100);

                return (
                  <button
                    key={classroom.id}
                    type="button"
                    onClick={() => setSelectedClassroom(classroom)}
                    className="group w-full rounded-2xl border border-slate-100 bg-slate-50/70 p-3.5 text-left transition hover:border-[var(--school-primary)] hover:bg-white hover:shadow-sm focus:outline-none focus:ring-4 focus:ring-slate-100"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <div className="truncate text-sm font-medium">
                            {classroom.name}
                          </div>
                          <ChevronRight
                            size={14}
                            className="tenant-primary-text shrink-0 opacity-0 transition group-hover:translate-x-0.5 group-hover:opacity-100"
                          />
                        </div>
                        <div className="mt-0.5 truncate text-[11px] text-slate-400">
                          {classroom.level_name} •{" "}
                          {classroom.cycle_name}
                        </div>
                      </div>
                      <div className="shrink-0 text-right">
                        <div className="text-sm font-semibold">
                          {formatNumber(
                            classroom.count,
                            language
                          )}
                          {classroom.capacity
                            ? ` / ${formatNumber(
                                classroom.capacity,
                                language
                              )}`
                            : ""}
                        </div>
                        <div className="text-[10px] text-slate-400">
                          {classroom.occupancy_rate != null
                            ? t("dashboard.stats.occupancy", {
                                rate:
                                  classroom.occupancy_rate,
                              })
                            : t("dashboard.stats.enrolled")}
                        </div>
                      </div>
                    </div>
                    <div className="mt-2.5">
                      <ProgressBar value={rate} />
                    </div>
                    <div className="mt-2 flex items-center justify-end gap-1 text-[10px] font-medium text-slate-400 transition group-hover:text-slate-700">
                      {t("dashboard.classDetail.open")}
                      <ChevronRight size={11} />
                    </div>
                  </button>
                );
              })}
            </div>
          ) : (
            <EmptyState>
              {t("dashboard.stats.noClassData")}
            </EmptyState>
          )}
        </SectionCard>

        {academics ? (
          <SectionCard
            title={t("dashboard.stats.academicActivity")}
            subtitle={t("dashboard.stats.academicActivityHelp")}
            icon={ClipboardCheck}
          >
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-2xl bg-slate-50 p-4">
                <div className="text-xs text-slate-400">
                  {t("dashboard.stats.assessments")}
                </div>
                <div className="mt-2 text-2xl font-semibold">
                  {formatNumber(
                    academics.assessments_total,
                    language
                  )}
                </div>
              </div>
              <div className="rounded-2xl bg-slate-50 p-4">
                <div className="text-xs text-slate-400">
                  {t("dashboard.stats.reportCardsPublished")}
                </div>
                <div className="mt-2 text-2xl font-semibold">
                  {formatNumber(
                    academics.published_report_cards,
                    language
                  )}
                </div>
              </div>
              <div className="rounded-2xl bg-slate-50 p-4">
                <div className="text-xs text-slate-400">
                  {t("dashboard.stats.annualAverage")}
                </div>
                <div className="mt-2 text-2xl font-semibold">
                  {academics.annual_average ?? "—"}
                </div>
              </div>
            </div>

            <div className="mt-5 space-y-3">
              {assessmentStatusOrder.map((status) => {
                const item = academics.statuses?.find(
                  (row) => row.key === status
                ) || {
                  key: status,
                  count: 0,
                  percentage: 0,
                };

                return (
                  <div key={status}>
                    <div className="flex items-center justify-between gap-3 text-xs">
                      <span className="text-slate-500">
                        {t(
                          `dashboard.stats.assessmentStatus.${status.toLowerCase()}`
                        )}
                      </span>
                      <span className="font-medium">
                        {formatNumber(item.count, language)}
                      </span>
                    </div>
                    <div className="mt-1.5">
                      <ProgressBar
                        value={item.percentage}
                        muted={status !== "PUBLISHED"}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </SectionCard>
        ) : (
          <SectionCard
            title={t("dashboard.configuration")}
            subtitle={t("dashboard.stats.schoolConfigHelp")}
            icon={School}
          >
            <dl className="grid gap-4 text-sm sm:grid-cols-2">
              <div>
                <dt className="text-slate-400">
                  {t("dashboard.language")}
                </dt>
                <dd className="mt-1 font-medium">
                  {dashboard.school.language_mode}
                </dd>
              </div>
              <div>
                <dt className="text-slate-400">
                  {t("dashboard.cycles")}
                </dt>
                <dd className="mt-1 font-medium">
                  {dashboard.school.education_level}
                </dd>
              </div>
              <div>
                <dt className="text-slate-400">
                  {t("dashboard.activeTeam")}
                </dt>
                <dd className="mt-1 font-medium">
                  {t("dashboard.members", {
                    count: overview.members || 0,
                  })}
                </dd>
              </div>
            </dl>
          </SectionCard>
        )}
      </div>

      {finance && (
        <div className="mt-4 grid gap-4 sm:mt-6 xl:grid-cols-[1.05fr_.95fr]">
          <SectionCard
            title={t("dashboard.stats.financeOverview")}
            subtitle={t("dashboard.stats.financeHelp")}
            icon={WalletCards}
          >
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-2xl bg-slate-50 p-4">
                <div className="text-xs text-slate-400">
                  {t("dashboard.stats.expected")}
                </div>
                <div className="mt-2 text-lg font-semibold sm:text-xl">
                  {formatMoney(
                    finance.expected_total,
                    finance.currency,
                    language
                  )}
                </div>
              </div>
              <div className="tenant-primary-soft rounded-2xl p-4">
                <div className="tenant-primary-text text-xs">
                  {t("dashboard.stats.collected")}
                </div>
                <div className="mt-2 text-lg font-semibold sm:text-xl">
                  {formatMoney(
                    finance.collected_total,
                    finance.currency,
                    language
                  )}
                </div>
              </div>
              <div className="rounded-2xl bg-slate-50 p-4">
                <div className="text-xs text-slate-400">
                  {t("dashboard.stats.outstanding")}
                </div>
                <div className="mt-2 text-lg font-semibold sm:text-xl">
                  {formatMoney(
                    finance.outstanding_total,
                    finance.currency,
                    language
                  )}
                </div>
              </div>
            </div>

            <div className="mt-5 rounded-2xl border border-slate-100 p-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-sm font-medium">
                    {t("dashboard.stats.collectionProgress")}
                  </div>
                  <div className="mt-1 text-xs text-slate-400">
                    {t("dashboard.stats.thisMonth", {
                      amount: formatMoney(
                        finance.payments_this_month,
                        finance.currency,
                        language
                      ),
                    })}
                  </div>
                </div>
                <div className="tenant-primary-text text-2xl font-semibold">
                  {finance.collection_rate}%
                </div>
              </div>
              <div className="mt-3">
                <ProgressBar value={finance.collection_rate} />
              </div>

              <div className="mt-4 grid grid-cols-3 gap-2 text-center">
                <div className="rounded-xl bg-emerald-50 px-2 py-3">
                  <div className="text-lg font-semibold text-emerald-700">
                    {formatNumber(finance.paid_count, language)}
                  </div>
                  <div className="mt-0.5 text-[10px] text-emerald-600">
                    {t("dashboard.stats.paid")}
                  </div>
                </div>
                <div className="rounded-xl bg-amber-50 px-2 py-3">
                  <div className="text-lg font-semibold text-amber-700">
                    {formatNumber(
                      finance.partial_count,
                      language
                    )}
                  </div>
                  <div className="mt-0.5 text-[10px] text-amber-600">
                    {t("dashboard.stats.partial")}
                  </div>
                </div>
                <div className="rounded-xl bg-rose-50 px-2 py-3">
                  <div className="text-lg font-semibold text-rose-700">
                    {formatNumber(
                      finance.unpaid_count,
                      language
                    )}
                  </div>
                  <div className="mt-0.5 text-[10px] text-rose-600">
                    {t("dashboard.stats.unpaid")}
                  </div>
                </div>
              </div>
            </div>
          </SectionCard>

          <SectionCard
            title={t("dashboard.stats.monthlyCollections")}
            subtitle={t("dashboard.stats.monthlyCollectionsHelp")}
            icon={CircleDollarSign}
          >
            <div className="flex h-52 items-end gap-2 sm:gap-3">
              {monthly.map((item) => {
                const amount = Number(item.amount || 0);
                const height =
                  amount > 0
                    ? Math.max(8, (amount / maxMonthly) * 100)
                    : 3;

                return (
                  <div
                    key={`${item.year}-${item.month}`}
                    className="flex min-w-0 flex-1 flex-col items-center justify-end gap-2"
                  >
                    <div className="w-full text-center text-[9px] font-medium text-slate-400 sm:text-[10px]">
                      {amount > 0
                        ? formatNumber(amount, language)
                        : "0"}
                    </div>
                    <div className="flex h-36 w-full items-end justify-center rounded-xl bg-slate-50 px-1.5 pt-2">
                      <div
                        className="tenant-primary-bg w-full max-w-10 rounded-t-lg transition-all"
                        style={{ height: `${height}%` }}
                        title={formatMoney(
                          amount,
                          finance.currency,
                          language
                        )}
                      />
                    </div>
                    <div className="text-[10px] font-medium uppercase text-slate-500">
                      {monthLabel(
                        item.year,
                        item.month,
                        language
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="mt-5 grid grid-cols-2 gap-3">
              <div className="rounded-2xl bg-slate-50 p-4">
                <div className="text-xs text-slate-400">
                  {t("dashboard.stats.today")}
                </div>
                <div className="mt-1.5 font-semibold">
                  {formatMoney(
                    finance.payments_today,
                    finance.currency,
                    language
                  )}
                </div>
              </div>
              <div className="rounded-2xl bg-slate-50 p-4">
                <div className="text-xs text-slate-400">
                  {t("dashboard.stats.tuitionAccounts")}
                </div>
                <div className="mt-1.5 font-semibold">
                  {formatNumber(
                    finance.accounts_count,
                    language
                  )}
                </div>
              </div>
            </div>
          </SectionCard>
        </div>
      )}

      <div className="mt-4 grid gap-4 sm:mt-6 lg:grid-cols-[1.15fr_.85fr]">
        <section className="tenant-card rounded-3xl border border-slate-200 bg-white p-4 shadow-sm sm:p-6">
          <div className="flex items-center gap-3">
            <div className="tenant-primary-soft tenant-primary-text grid h-10 w-10 shrink-0 place-items-center rounded-xl">
              <CheckCircle2 size={18} />
            </div>
            <div>
              <h2 className="font-semibold">
                {t("dashboard.stats.snapshotTitle")}
              </h2>
              <p className="mt-0.5 text-xs text-slate-500 sm:text-sm">
                {t("dashboard.stats.snapshotHelp")}
              </p>
            </div>
          </div>

          <div className="mt-5 grid gap-3 sm:grid-cols-3">
            <div className="rounded-2xl bg-slate-50 p-4">
              <div className="text-xs text-slate-400">
                {t("dashboard.stats.academicYear")}
              </div>
              <div className="mt-1.5 font-medium">
                {year?.name || "—"}
              </div>
            </div>
            <div className="rounded-2xl bg-slate-50 p-4">
              <div className="text-xs text-slate-400">
                {t("dashboard.stats.currentPeriod")}
              </div>
              <div className="mt-1.5 font-medium">
                {analytics.active_period?.name || "—"}
              </div>
            </div>
            <div className="rounded-2xl bg-slate-50 p-4">
              <div className="text-xs text-slate-400">
                {t("dashboard.stats.teamMembers")}
              </div>
              <div className="mt-1.5 font-medium">
                {formatNumber(overview.members, language)}
              </div>
            </div>
          </div>
        </section>

        <section className="tenant-card rounded-3xl border border-slate-200 bg-white p-4 shadow-sm sm:p-6">
          <h2 className="font-semibold">
            {t("dashboard.configuration")}
          </h2>
          <dl className="mt-5 grid gap-4 text-sm sm:grid-cols-3 lg:grid-cols-1">
            <div>
              <dt className="text-slate-400">
                {t("dashboard.language")}
              </dt>
              <dd className="mt-1 font-medium">
                {dashboard.school.language_mode}
              </dd>
            </div>
            <div>
              <dt className="text-slate-400">
                {t("dashboard.cycles")}
              </dt>
              <dd className="mt-1 font-medium">
                {dashboard.school.education_level}
              </dd>
            </div>
            <div>
              <dt className="text-slate-400">
                {t("dashboard.stats.generatedAt")}
              </dt>
              <dd className="mt-1 font-medium">
                {analytics.generated_at
                  ? new Intl.DateTimeFormat(
                      language === "en" ? "en-US" : "fr-FR",
                      {
                        dateStyle: "medium",
                        timeStyle: "short",
                      }
                    ).format(
                      new Date(analytics.generated_at)
                    )
                  : "—"}
              </dd>
            </div>
          </dl>
        </section>
      </div>
    </div>
  );
}
