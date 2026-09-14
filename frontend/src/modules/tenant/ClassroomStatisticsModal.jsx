import { useEffect, useMemo, useState } from "react";
import {
  BarChart3,
  BookOpenCheck,
  CheckCircle2,
  ClipboardCheck,
  GraduationCap,
  Loader2,
  TrendingUp,
  UserRoundCog,
  Users,
  WalletCards,
  X,
} from "lucide-react";

import { useI18n } from "../../i18n";
import { notifyError } from "../../lib/toast";
import api from "../../services/api";


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

function ProgressBar({ value, muted = false }) {
  return (
    <div className="h-2 overflow-hidden rounded-full bg-slate-100">
      <div
        className={`h-full rounded-full transition-all ${
          muted ? "bg-slate-400" : "tenant-primary-bg"
        }`}
        style={{ width: `${clamp(value)}%` }}
      />
    </div>
  );
}

function Metric({ label, value, detail, icon: Icon, emphasis = false }) {
  return (
    <div
      className={`rounded-2xl border p-4 ${
        emphasis
          ? "tenant-primary-border tenant-primary-soft"
          : "border-slate-200 bg-white"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-xs text-slate-500">{label}</div>
          <div className="mt-2 break-words text-xl font-semibold sm:text-2xl">
            {value}
          </div>
          {detail && (
            <div className="mt-1 text-[11px] leading-5 text-slate-400">
              {detail}
            </div>
          )}
        </div>
        <div className="tenant-primary-soft tenant-primary-text grid h-9 w-9 shrink-0 place-items-center rounded-xl">
          <Icon size={16} />
        </div>
      </div>
    </div>
  );
}

function Panel({ title, subtitle, icon: Icon, children }) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-4 sm:p-5">
      <div className="flex items-start gap-3">
        {Icon && (
          <div className="tenant-primary-soft tenant-primary-text grid h-9 w-9 shrink-0 place-items-center rounded-xl">
            <Icon size={16} />
          </div>
        )}
        <div className="min-w-0">
          <h3 className="font-semibold">{title}</h3>
          {subtitle && (
            <p className="mt-1 text-xs leading-5 text-slate-500">
              {subtitle}
            </p>
          )}
        </div>
      </div>
      <div className="mt-4">{children}</div>
    </section>
  );
}

function GenderChart({ rows, total, t, language }) {
  const ordered = genderOrder
    .map((key) => rows?.find((item) => item.key === key))
    .filter(Boolean);

  const male = ordered.find((item) => item.key === "MALE");
  const female = ordered.find((item) => item.key === "FEMALE");
  const malePct = clamp(male?.percentage || 0);
  const femalePct = clamp(female?.percentage || 0);
  const otherStart = Math.min(100, malePct + femalePct);

  const background = `conic-gradient(
    var(--school-primary) 0% ${malePct}%,
    var(--school-secondary) ${malePct}% ${otherStart}%,
    rgb(148 163 184) ${otherStart}% 100%
  )`;

  if (!ordered.length) {
    return (
      <div className="rounded-2xl bg-slate-50 px-4 py-7 text-center text-sm text-slate-500">
        {t("dashboard.classDetail.noGender")}
      </div>
    );
  }

  return (
    <div className="grid items-center gap-5 sm:grid-cols-[135px_1fr]">
      <div className="mx-auto grid place-items-center">
        <div
          className="grid h-32 w-32 place-items-center rounded-full"
          style={{ background }}
        >
          <div className="grid h-20 w-20 place-items-center rounded-full bg-white text-center shadow-inner">
            <div>
              <div className="text-xl font-semibold">
                {formatNumber(total, language)}
              </div>
              <div className="text-[9px] uppercase tracking-wide text-slate-400">
                {t("dashboard.stats.students")}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-2.5">
        {ordered.map((item) => (
          <div
            key={item.key}
            className="flex items-center justify-between gap-3 rounded-xl bg-slate-50 px-3 py-2.5"
          >
            <div className="flex items-center gap-2">
              <span
                className="h-2.5 w-2.5 rounded-full"
                style={{
                  background:
                    item.key === "MALE"
                      ? "var(--school-primary)"
                      : item.key === "FEMALE"
                      ? "var(--school-secondary)"
                      : "rgb(148 163 184)",
                }}
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
  );
}

export default function ClassroomStatisticsModal({
  classroom,
  onClose,
}) {
  const { t, language } = useI18n();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    if (!classroom?.id) return undefined;

    let active = true;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const onKeyDown = (event) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKeyDown);

    const load = async () => {
      setLoading(true);

      try {
        const { data } = await api.get(
          `/tenant/dashboard/classrooms/${classroom.id}/statistics/`
        );
        if (active) setStats(data);
      } catch (error) {
        notifyError(
          error?.response?.data?.detail ||
            t("dashboard.classDetail.loadError")
        );
        if (active) onClose();
      } finally {
        if (active) setLoading(false);
      }
    };

    load();

    return () => {
      active = false;
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [classroom?.id, onClose, t]);

  const academics = stats?.academics;
  const finance = stats?.finance;
  const population = stats?.population;
  const teaching = stats?.teaching;

  const subjects = academics?.subjects || [];
  const maxSubjectAverage = Math.max(
    20,
    ...subjects.map((item) => Number(item.average_on_20 || 0))
  );

  const title = stats?.classroom?.name || classroom?.name || "";
  const subtitle = useMemo(() => {
    if (!stats?.classroom) return classroom?.level_name || "";

    return [
      stats.classroom.level?.name,
      stats.classroom.cycle?.name,
      stats.classroom.section?.name,
      stats.classroom.academic_year?.name,
    ]
      .filter(Boolean)
      .join(" • ");
  }, [stats, classroom]);

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/60 p-2 backdrop-blur-sm sm:p-4"
      role="dialog"
      aria-modal="true"
      aria-label={t("dashboard.classDetail.title", {
        name: title,
      })}
    >
      <button
        type="button"
        className="absolute inset-0"
        aria-label={t("dashboard.classDetail.close")}
        onClick={onClose}
      />

      <div className="relative flex h-[calc(100dvh-1rem)] w-full max-w-6xl flex-col overflow-hidden rounded-2xl bg-slate-50 shadow-2xl sm:h-[calc(100dvh-2rem)] sm:rounded-3xl">
        <div
          className="tenant-primary-border shrink-0 border-b bg-white px-4 py-4 sm:px-6"
          style={{
            background:
              "linear-gradient(135deg, rgb(var(--school-primary-rgb) / 0.10), rgb(var(--school-secondary-rgb) / 0.05), white)",
          }}
        >
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0">
              <div className="tenant-primary-text text-[10px] font-semibold uppercase tracking-[0.18em]">
                {t("dashboard.classDetail.eyebrow")}
              </div>
              <h2 className="mt-1 truncate text-xl font-semibold sm:text-2xl">
                {title}
              </h2>
              <p className="mt-1 text-xs leading-5 text-slate-500 sm:text-sm">
                {subtitle}
              </p>

              {stats?.active_period?.name && (
                <div className="mt-2 inline-flex rounded-full border border-slate-200 bg-white/80 px-2.5 py-1 text-[10px] font-medium text-slate-600">
                  {t("dashboard.classDetail.currentPeriod", {
                    name: stats.active_period.name,
                  })}
                </div>
              )}
            </div>

            <button
              type="button"
              onClick={onClose}
              className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-white text-slate-500 shadow-sm ring-1 ring-slate-200 hover:bg-slate-50"
              aria-label={t("dashboard.classDetail.close")}
            >
              <X size={18} />
            </button>
          </div>
        </div>

        <div className="tenant-scrollbar min-h-0 flex-1 overflow-y-auto p-3 sm:p-5">
          {loading ? (
            <div className="grid min-h-[420px] place-items-center">
              <div className="flex flex-col items-center gap-3 text-sm text-slate-500">
                <Loader2
                  size={24}
                  className="tenant-primary-text animate-spin"
                />
                {t("dashboard.classDetail.loading")}
              </div>
            </div>
          ) : stats ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
                <Metric
                  label={t("dashboard.classDetail.students")}
                  value={formatNumber(
                    population?.students,
                    language
                  )}
                  detail={
                    population?.capacity
                      ? t("dashboard.classDetail.capacity", {
                          count: formatNumber(
                            population.capacity,
                            language
                          ),
                        })
                      : t("dashboard.classDetail.capacityUnset")
                  }
                  icon={Users}
                />
                <Metric
                  label={t("dashboard.classDetail.occupancy")}
                  value={
                    population?.occupancy_rate != null
                      ? `${population.occupancy_rate}%`
                      : "—"
                  }
                  detail={t("dashboard.classDetail.activeEnrollments")}
                  icon={TrendingUp}
                  emphasis
                />
                <Metric
                  label={t("dashboard.classDetail.teachers")}
                  value={formatNumber(
                    teaching?.teachers_count,
                    language
                  )}
                  detail={t("dashboard.classDetail.teachingTeam")}
                  icon={UserRoundCog}
                />
                <Metric
                  label={t("dashboard.classDetail.subjects")}
                  value={formatNumber(
                    teaching?.subjects_count,
                    language
                  )}
                  detail={t("dashboard.classDetail.activeSubjects")}
                  icon={BookOpenCheck}
                />
              </div>

              <div className="grid gap-4 xl:grid-cols-[.8fr_1.2fr]">
                <Panel
                  title={t("dashboard.classDetail.gender")}
                  subtitle={t("dashboard.classDetail.genderHelp")}
                  icon={Users}
                >
                  <GenderChart
                    rows={population?.gender || []}
                    total={population?.students || 0}
                    t={t}
                    language={language}
                  />
                </Panel>

                <Panel
                  title={t("dashboard.classDetail.teaching")}
                  subtitle={t("dashboard.classDetail.teachingHelp")}
                  icon={GraduationCap}
                >
                  {teaching?.teachers?.length ? (
                    <div className="grid gap-3 sm:grid-cols-2">
                      {teaching.teachers.map((teacher) => (
                        <div
                          key={teacher.id}
                          className="rounded-2xl border border-slate-100 bg-slate-50/80 p-3.5"
                        >
                          <div className="font-medium">
                            {teacher.name}
                          </div>
                          <div className="mt-1 text-[10px] text-slate-400">
                            {teacher.employee_number}
                          </div>

                          {!!teacher.leadership_roles?.length && (
                            <div className="mt-2 flex flex-wrap gap-1.5">
                              {teacher.leadership_roles.map((role) => (
                                <span
                                  key={role.key}
                                  className="tenant-primary-soft tenant-primary-text rounded-full px-2 py-1 text-[10px] font-medium"
                                >
                                  {role.label}
                                </span>
                              ))}
                            </div>
                          )}

                          {!!teacher.subjects?.length && (
                            <div className="mt-2 flex flex-wrap gap-1.5">
                              {teacher.subjects.map((subject) => (
                                <span
                                  key={subject.id}
                                  className="rounded-full bg-white px-2 py-1 text-[10px] text-slate-600 ring-1 ring-slate-200"
                                >
                                  {subject.name}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="rounded-2xl bg-slate-50 px-4 py-7 text-center text-sm text-slate-500">
                      {t("dashboard.classDetail.noTeaching")}
                    </div>
                  )}
                </Panel>
              </div>

              {academics && (
                <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
                  <Panel
                    title={t("dashboard.classDetail.academics")}
                    subtitle={t("dashboard.classDetail.academicsHelp")}
                    icon={ClipboardCheck}
                  >
                    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                      <div className="rounded-2xl bg-slate-50 p-3.5">
                        <div className="text-[10px] text-slate-400">
                          {t("dashboard.classDetail.assessments")}
                        </div>
                        <div className="mt-1.5 text-xl font-semibold">
                          {formatNumber(
                            academics.assessments_total,
                            language
                          )}
                        </div>
                      </div>
                      <div className="tenant-primary-soft rounded-2xl p-3.5">
                        <div className="tenant-primary-text text-[10px]">
                          {t(
                            "dashboard.classDetail.publicationRate"
                          )}
                        </div>
                        <div className="mt-1.5 text-xl font-semibold">
                          {academics.publication_rate}%
                        </div>
                      </div>
                      <div className="rounded-2xl bg-slate-50 p-3.5">
                        <div className="text-[10px] text-slate-400">
                          {t("dashboard.classDetail.reportCards")}
                        </div>
                        <div className="mt-1.5 text-xl font-semibold">
                          {formatNumber(
                            academics.published_report_cards,
                            language
                          )}
                        </div>
                      </div>
                      <div className="rounded-2xl bg-slate-50 p-3.5">
                        <div className="text-[10px] text-slate-400">
                          {t("dashboard.classDetail.annualAverage")}
                        </div>
                        <div className="mt-1.5 text-xl font-semibold">
                          {academics.annual_average ?? "—"}
                        </div>
                      </div>
                    </div>

                    <div className="mt-4 space-y-2.5">
                      {assessmentStatusOrder.map((status) => {
                        const item =
                          academics.statuses?.find(
                            (row) => row.key === status
                          ) || {
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
                                {formatNumber(
                                  item.count,
                                  language
                                )}
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
                  </Panel>

                  <Panel
                    title={t("dashboard.classDetail.subjectPerformance")}
                    subtitle={t(
                      "dashboard.classDetail.subjectPerformanceHelp"
                    )}
                    icon={BarChart3}
                  >
                    {subjects.length ? (
                      <div className="space-y-3">
                        {subjects.map((subject) => (
                          <div key={subject.id}>
                            <div className="flex items-center justify-between gap-3 text-xs">
                              <span className="min-w-0 truncate font-medium text-slate-600">
                                {subject.name}
                              </span>
                              <span className="shrink-0 font-semibold">
                                {subject.average_on_20}/20
                              </span>
                            </div>
                            <div className="mt-1.5">
                              <ProgressBar
                                value={
                                  (Number(
                                    subject.average_on_20 || 0
                                  ) /
                                    maxSubjectAverage) *
                                  100
                                }
                              />
                            </div>
                            <div className="mt-1 text-[10px] text-slate-400">
                              {t(
                                "dashboard.classDetail.scoresCount",
                                {
                                  count: formatNumber(
                                    subject.scores_count,
                                    language
                                  ),
                                }
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="rounded-2xl bg-slate-50 px-4 py-7 text-center text-sm text-slate-500">
                        {t("dashboard.classDetail.noSubjectPerformance")}
                      </div>
                    )}
                  </Panel>
                </div>
              )}

              {academics?.promotion_decisions?.length > 0 && (
                <Panel
                  title={t("dashboard.classDetail.promotion")}
                  subtitle={t("dashboard.classDetail.promotionHelp")}
                  icon={CheckCircle2}
                >
                  <div className="grid gap-2 sm:grid-cols-3 xl:grid-cols-6">
                    {academics.promotion_decisions.map((item) => (
                      <div
                        key={item.key}
                        className="rounded-2xl bg-slate-50 p-3 text-center"
                      >
                        <div className="text-lg font-semibold">
                          {formatNumber(item.count, language)}
                        </div>
                        <div className="mt-1 text-[10px] leading-4 text-slate-500">
                          {t(
                            `dashboard.classDetail.promotionDecision.${item.key.toLowerCase()}`
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </Panel>
              )}

              {finance && (
                <Panel
                  title={t("dashboard.classDetail.finance")}
                  subtitle={t("dashboard.classDetail.financeHelp")}
                  icon={WalletCards}
                >
                  <div className="grid gap-3 sm:grid-cols-3">
                    <div className="rounded-2xl bg-slate-50 p-4">
                      <div className="text-xs text-slate-400">
                        {t("dashboard.stats.expected")}
                      </div>
                      <div className="mt-2 text-lg font-semibold">
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
                      <div className="mt-2 text-lg font-semibold">
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
                      <div className="mt-2 text-lg font-semibold">
                        {formatMoney(
                          finance.outstanding_total,
                          finance.currency,
                          language
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 rounded-2xl border border-slate-100 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="text-sm font-medium">
                          {t(
                            "dashboard.classDetail.collectionRate"
                          )}
                        </div>
                        <div className="mt-1 text-xs text-slate-400">
                          {t(
                            "dashboard.classDetail.tuitionAccounts",
                            {
                              count: formatNumber(
                                finance.accounts_count,
                                language
                              ),
                            }
                          )}
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
                          {formatNumber(
                            finance.paid_count,
                            language
                          )}
                        </div>
                        <div className="text-[10px] text-emerald-600">
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
                        <div className="text-[10px] text-amber-600">
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
                        <div className="text-[10px] text-rose-600">
                          {t("dashboard.stats.unpaid")}
                        </div>
                      </div>
                    </div>
                  </div>
                </Panel>
              )}

              {!academics && !finance && (
                <div className="rounded-3xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-500">
                  {t("dashboard.classDetail.noRoleData")}
                </div>
              )}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
