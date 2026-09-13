import { useEffect, useMemo, useState } from "react";
import {
  BookOpenText,
  Download,
  FileCheck2,
  FileText,
  Loader2,
  RefreshCw,
  Search,
  ShieldCheck,
  Users,
  LayoutTemplate,
  Eye,
  ExternalLink,
  X,
} from "lucide-react";

import { useI18n } from "../../i18n";
import api from "../../services/api";
import {
  notifyError,
  notifyInfo,
  notifySuccess,
} from "../../lib/toast";
import ReportCardTemplatesPanel from "./ReportCardTemplatesPanel";


const inputClass =
  "w-full rounded-xl border border-slate-200 bg-white px-3.5 py-3 text-sm outline-none focus:border-slate-400 focus:ring-4 focus:ring-slate-100";

const primaryButton =
  "inline-flex items-center justify-center gap-2 rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-medium text-white disabled:opacity-40";

function parseError(error, fallback) {
  return (
    error?.response?.data?.detail ||
    error?.response?.data?.non_field_errors?.[0] ||
    fallback
  );
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

function averageLabel(value) {
  if (value === null || value === undefined || value === "") return "—";
  const numeric = Number(value);
  if (Number.isNaN(numeric)) return String(value);
  return numeric.toFixed(2).replace(/\.00$/, "");
}

function rankLabel(rank) {
  return rank ? `#${rank}` : "—";
}

function ResultCard({ label, value, help }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4">
      <div className="text-xs font-medium uppercase tracking-[0.12em] text-slate-400">
        {label}
      </div>
      <div className="mt-2 text-2xl font-semibold">{value ?? "—"}</div>
      {help && <div className="mt-1 text-xs text-slate-500">{help}</div>}
    </div>
  );
}

export default function ReportCardsWorkspace({ role, isDirection }) {
  const { t } = useI18n();

  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [saving, setSaving] = useState("");
  const [previewPdf, setPreviewPdf] = useState(null);

  const [tab, setTab] = useState("explorer");
  const [options, setOptions] = useState({
    years: [],
    periods: [],
    classrooms: [],
    subjects: [],
    full_report_class_ids: [],
    classroom_subjects: {},
    cycles: [],
  });
  const [snapshots, setSnapshots] = useState([]);

  const [mode, setMode] = useState("PERIOD");
  const [yearId, setYearId] = useState("");
  const [classroomId, setClassroomId] = useState("");
  const [periodId, setPeriodId] = useState("");
  const [subjectId, setSubjectId] = useState("");

  const [classResults, setClassResults] = useState(null);
  const [subjectResults, setSubjectResults] = useState(null);
  const [studentResult, setStudentResult] = useState(null);
  const [selectedEnrollmentId, setSelectedEnrollmentId] = useState(null);

  const [generalComment, setGeneralComment] = useState("");
  const [teacherComment, setTeacherComment] = useState("");
  const [subjectComments, setSubjectComments] = useState({});

  const teacherMode = role === "TEACHER";

  const loadSnapshots = async () => {
    const { data } = await api.get(
      "/report-cards/snapshots/?latest_only=false"
    );
    setSnapshots(data);
  };

  const load = async ({ initial = false } = {}) => {
    if (initial) setLoading(true);
    else setSyncing(true);

    try {
      const [{ data: optionData }, { data: snapshotData }] =
        await Promise.all([
          api.get("/report-cards/options/"),
          api.get("/report-cards/snapshots/?latest_only=false"),
        ]);

      setOptions(optionData);
      setSnapshots(snapshotData);

      const active =
        optionData.years.find((item) => item.is_active) ||
        optionData.years[0];

      if (active) {
        setYearId((current) => current || String(active.id));
      }
    } catch (err) {
      notifyError(parseError(err, t("reportCards.errors.load")));
    } finally {
      if (initial) setLoading(false);
      else setSyncing(false);
    }
  };

  useEffect(() => {
    load({ initial: true });
  }, [role]);

  useEffect(
    () => () => {
      if (previewPdf?.url) {
        URL.revokeObjectURL(previewPdf.url);
      }
    },
    [previewPdf?.url]
  );

  const closePreview = () => {
    setPreviewPdf((current) => {
      if (current?.url) {
        URL.revokeObjectURL(current.url);
      }
      return null;
    });
  };

  const classrooms = useMemo(
    () =>
      options.classrooms.filter(
        (item) => String(item.academic_year) === String(yearId)
      ),
    [options.classrooms, yearId]
  );

  const periods = useMemo(
    () =>
      options.periods.filter(
        (item) => String(item.academic_year) === String(yearId)
      ),
    [options.periods, yearId]
  );

  const availableSubjects = useMemo(() => {
    if (!classroomId) return options.subjects;
    const allowed =
      options.classroom_subjects?.[String(classroomId)] || [];
    const allowedSet = new Set(allowed.map(Number));
    return options.subjects.filter((item) =>
      allowedSet.has(Number(item.id))
    );
  }, [options.subjects, options.classroom_subjects, classroomId]);

  const canUseFullReports = useMemo(
    () =>
      !classroomId ||
      options.full_report_class_ids.includes(Number(classroomId)),
    [classroomId, options.full_report_class_ids]
  );

  const resetResults = () => {
    setClassResults(null);
    setSubjectResults(null);
    setStudentResult(null);
    setSelectedEnrollmentId(null);
    setGeneralComment("");
    setTeacherComment("");
    setSubjectComments({});
  };

  const chooseYear = (value) => {
    setYearId(value);
    setClassroomId("");
    setPeriodId("");
    setSubjectId("");
    resetResults();
  };

  const chooseClassroom = (value) => {
    setClassroomId(value);
    setSubjectId("");
    resetResults();
  };

  const choosePeriod = (value) => {
    setPeriodId(value);
    resetResults();
  };

  const chooseMode = (value) => {
    setMode(value);
    setSubjectId("");
    setPeriodId("");
    resetResults();
  };

  const loadExplorer = async () => {
    if (!classroomId) return;
    if (mode === "PERIOD" && !periodId) return;

    setSaving("explore");
    setStudentResult(null);
    setSelectedEnrollmentId(null);

    try {
      if (mode === "PERIOD" && subjectId) {
        const { data } = await api.get(
          `/report-cards/results/subjects/${subjectId}/periods/${periodId}/?classroom=${classroomId}`
        );
        setSubjectResults(data);
        setClassResults(null);
      } else if (mode === "PERIOD") {
        const { data } = await api.get(
          `/report-cards/results/classrooms/${classroomId}/periods/${periodId}/`
        );
        setClassResults(data);
        setSubjectResults(null);
      } else {
        const { data } = await api.get(
          `/report-cards/results/classrooms/${classroomId}/annual/`
        );
        setClassResults(data);
        setSubjectResults(null);
      }
    } catch (err) {
      notifyError(parseError(err, t("reportCards.errors.results")));
    } finally {
      setSaving("");
    }
  };

  const openStudent = async (enrollmentId) => {
    setSaving(`student-${enrollmentId}`);
    setGeneralComment("");
    setTeacherComment("");
    setSubjectComments({});

    try {
      const endpoint =
        mode === "PERIOD"
          ? `/report-cards/results/students/${enrollmentId}/periods/${periodId}/`
          : `/report-cards/results/students/${enrollmentId}/annual/`;

      const { data } = await api.get(endpoint);
      setStudentResult(data);
      setSelectedEnrollmentId(enrollmentId);
    } catch (err) {
      notifyError(parseError(err, t("reportCards.errors.student")));
    } finally {
      setSaving("");
    }
  };

  const previewStudentPdf = async () => {
    if (!selectedEnrollmentId) return;

    setSaving("preview-student");

    const payload = {
      enrollment: selectedEnrollmentId,
      report_type: mode,
      general_comment: generalComment,
      teacher_comment: teacherComment,
      subject_comments: subjectComments,
    };

    if (mode === "PERIOD") {
      payload.academic_period = Number(periodId);
    }

    try {
      const response = await api.post(
        "/report-cards/preview/",
        payload,
        { responseType: "blob" }
      );

      const blob = response.data;
      const url = URL.createObjectURL(blob);

      setPreviewPdf((current) => {
        if (current?.url) {
          URL.revokeObjectURL(current.url);
        }

        return {
          url,
          blob,
          pages:
            response.headers?.["x-report-card-pages"] || "1",
          template:
            response.headers?.["x-report-card-template"] ||
            "CLASSIC",
          orientation:
            response.headers?.["x-report-card-orientation"] ||
            "PORTRAIT",
        };
      });

      notifySuccess(
        t("reportCards.messages.previewReady", {
          pages:
            response.headers?.["x-report-card-pages"] || "1",
        })
      );
    } catch (err) {
      let detail = t("reportCards.errors.preview");

      if (err?.response?.data instanceof Blob) {
        try {
          const raw = await err.response.data.text();
          const parsed = JSON.parse(raw);
          detail = parsed.detail || detail;
        } catch {
          // Keep fallback.
        }
      } else {
        detail = parseError(err, detail);
      }

      notifyError(detail);
    } finally {
      setSaving("");
    }
  };

  const publishStudent = async () => {
    if (!selectedEnrollmentId) return;

    setSaving("publish-student");

    try {
      const payload = {
        enrollment: selectedEnrollmentId,
        report_type: mode,
        general_comment: generalComment,
        teacher_comment: teacherComment,
        subject_comments: subjectComments,
      };

      if (mode === "PERIOD") {
        payload.academic_period = Number(periodId);
      }

      const { data } = await api.post(
        "/report-cards/publish/",
        payload
      );

      if (data.created_new_version) {
        notifySuccess(
          t("reportCards.messages.published", {
            version: data.snapshot.version,
          })
        );
        await loadSnapshots();
        setTab("published");
      } else {
        notifyInfo(
          t("reportCards.messages.unchanged", {
            version: data.snapshot.version,
          })
        );
      }
    } catch (err) {
      notifyError(parseError(err, t("reportCards.errors.publish")));
    } finally {
      setSaving("");
    }
  };

  const publishClassroom = async () => {
    if (!classroomId) return;

    const confirmed = window.confirm(
      t("reportCards.publish.classConfirm")
    );
    if (!confirmed) return;

    setSaving("publish-class");

    try {
      const payload = {
        classroom: Number(classroomId),
        report_type: mode,
      };
      if (mode === "PERIOD") {
        payload.academic_period = Number(periodId);
      }

      const { data } = await api.post(
        "/report-cards/publish/classroom/",
        payload
      );

      notifySuccess(
        t("reportCards.messages.classPublished", {
          created: data.created,
          unchanged: data.unchanged,
          failed: data.failed,
        })
      );
      await loadSnapshots();
    } catch (err) {
      notifyError(parseError(err, t("reportCards.errors.publish")));
    } finally {
      setSaving("");
    }
  };

  const downloadClassZip = async () => {
    if (!classroomId) return;
    if (mode === "PERIOD" && !periodId) return;

    setSaving("zip-class");

    try {
      const params = new URLSearchParams();
      params.set("classroom", classroomId);
      params.set("report_type", mode);

      if (mode === "PERIOD") {
        params.set("academic_period", periodId);
      }

      const response = await api.get(
        `/report-cards/download/classroom-zip/?${params.toString()}`,
        { responseType: "blob" }
      );

      const classroom = classrooms.find(
        (item) => String(item.id) === String(classroomId)
      );
      const period = periods.find(
        (item) => String(item.id) === String(periodId)
      );

      const safe = (value) =>
        String(value || "bulletins")
          .toLowerCase()
          .replace(/[^a-z0-9]+/gi, "-")
          .replace(/^-|-$/g, "");

      const filename = [
        "bulletins",
        safe(classroom?.name),
        safe(classroom?.academic_year_name),
        mode === "PERIOD" ? safe(period?.name) : "annuel",
      ]
        .filter(Boolean)
        .join("-") + ".zip";

      downloadBlob(response.data, filename);

      const included =
        response.headers?.["x-report-cards-included"] || "?";
      const missing =
        response.headers?.["x-report-cards-missing"] || "0";

      notifySuccess(
        t("reportCards.messages.zipDownloaded", {
          included,
          missing,
        })
      );
    } catch (err) {
      notifyError(parseError(err, t("reportCards.errors.zip")));
    } finally {
      setSaving("");
    }
  };

  const downloadPdf = async (snapshot) => {
    setSaving(`pdf-${snapshot.id}`);

    try {
      const { data } = await api.get(
        `/report-cards/snapshots/${snapshot.id}/pdf/`,
        { responseType: "blob" }
      );

      const safeName = snapshot.student_name
        .toLowerCase()
        .replace(/[^a-z0-9]+/gi, "-")
        .replace(/^-|-$/g, "");

      downloadBlob(
        data,
        `bulletin-${safeName}-v${snapshot.version}.pdf`
      );
    } catch (err) {
      notifyError(parseError(err, t("reportCards.errors.pdf")));
    } finally {
      setSaving("");
    }
  };

  const copyVerification = async (snapshot) => {
    try {
      await navigator.clipboard.writeText(snapshot.verification_url);
      notifySuccess(t("reportCards.messages.verificationCopied"));
    } catch {
      window.open(snapshot.verification_url, "_blank", "noopener,noreferrer");
    }
  };

  const latestSnapshotIds = useMemo(() => {
    const latest = new Map();

    snapshots.forEach((item) => {
      const key = [
        item.student_id,
        item.report_type,
        item.academic_period || "annual",
        item.academic_year,
      ].join(":");

      const current = latest.get(key);
      if (!current || item.version > current.version) {
        latest.set(key, item);
      }
    });

    return new Set(Array.from(latest.values()).map((item) => item.id));
  }, [snapshots]);

  if (loading) {
    return (
      <div className="grid min-h-[300px] place-items-center rounded-3xl border border-slate-200 bg-white">
        <div className="inline-flex items-center gap-2 text-sm text-slate-500">
          <Loader2 size={18} className="animate-spin" />
          {t("reportCards.loading")}
        </div>
      </div>
    );
  }

  const tabs = [
    ["explorer", t("reportCards.tabs.explorer"), Search],
    ["published", t("reportCards.tabs.published"), FileCheck2],
    ...(isDirection
      ? [
          [
            "templates",
            t("reportCards.tabs.templates"),
            LayoutTemplate,
          ],
        ]
      : []),
  ];

  return (
    <div className="space-y-5">
      {previewPdf && (
        <div
          className="fixed inset-0 z-[95] flex items-center justify-center bg-slate-950/60 p-2 backdrop-blur-sm sm:p-4"
          role="dialog"
          aria-modal="true"
          aria-label={t("reportCards.preview.title")}
        >
          <div className="flex h-[calc(100dvh-1rem)] w-full max-w-6xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl sm:h-[calc(100dvh-2rem)] sm:rounded-3xl">
            <div className="flex shrink-0 flex-col gap-3 border-b border-slate-200 bg-white px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:px-5">
              <div className="min-w-0">
                <div className="font-semibold">
                  {t("reportCards.preview.title")}
                </div>
                <div className="mt-0.5 text-xs text-slate-500">
                  {t("reportCards.preview.meta", {
                    pages: previewPdf.pages,
                    template: previewPdf.template,
                    orientation: previewPdf.orientation,
                  })}
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  onClick={() =>
                    downloadBlob(
                      previewPdf.blob,
                      "apercu-bulletin.pdf"
                    )
                  }
                  className="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-xs font-medium hover:bg-slate-50"
                >
                  <Download size={14} />
                  {t("reportCards.preview.download")}
                </button>

                <a
                  href={previewPdf.url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-xs font-medium hover:bg-slate-50"
                >
                  <ExternalLink size={14} />
                  {t("reportCards.preview.newTab")}
                </a>

                <button
                  type="button"
                  onClick={closePreview}
                  className="grid h-9 w-9 place-items-center rounded-xl bg-slate-100 text-slate-600 hover:bg-slate-200"
                  aria-label={t("reportCards.preview.close")}
                >
                  <X size={17} />
                </button>
              </div>
            </div>

            <div className="min-h-0 flex-1 bg-slate-100 p-2 sm:p-3">
              <iframe
                title={t("reportCards.preview.title")}
                src={previewPdf.url}
                className="h-full w-full rounded-xl border border-slate-200 bg-white"
              />
            </div>

            <div className="shrink-0 border-t border-slate-200 bg-white px-4 py-2 text-center text-[11px] text-slate-500">
              {t("reportCards.preview.nonOfficial")}
            </div>
          </div>
        </div>
      )}
      <div className="flex flex-col justify-between gap-4 xl:flex-row xl:items-end">
        <div>
          <div className="text-xs font-medium uppercase tracking-[0.18em] text-slate-400">
            {t("reportCards.step")}
          </div>
          <h1 className="mt-2 text-2xl font-semibold">
            {t("reportCards.title")}
          </h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">
            {teacherMode
              ? t("reportCards.teacherDescription")
              : t("reportCards.description")}
          </p>
        </div>

        {syncing && (
          <span className="inline-flex items-center gap-2 text-xs text-slate-400">
            <RefreshCw size={13} className="animate-spin" />
            {t("reportCards.syncing")}
          </span>
        )}
      </div>


      <div className="flex gap-1 overflow-x-auto rounded-2xl border border-slate-200 bg-white p-1.5">
        {tabs.map(([id, label, Icon]) => (
          <button
            key={id}
            type="button"
            onClick={() => setTab(id)}
            className={`inline-flex shrink-0 items-center gap-2 rounded-xl px-4 py-2.5 text-sm ${
              tab === id
                ? "bg-slate-950 text-white"
                : "text-slate-600 hover:bg-slate-50"
            }`}
          >
            <Icon size={16} />
            {label}
          </button>
        ))}
      </div>

      {tab === "explorer" && (
        <>
          <section className="rounded-3xl border border-slate-200 bg-white p-6">
            <div>
              <h2 className="font-semibold">
                {t("reportCards.explorer.title")}
              </h2>
              <p className="mt-1 text-xs leading-5 text-slate-500">
                {t("reportCards.explorer.help")}
              </p>
            </div>

            <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
              <select
                className={inputClass}
                value={mode}
                onChange={(event) => chooseMode(event.target.value)}
              >
                <option value="PERIOD">
                  {t("reportCards.types.period")}
                </option>
                <option value="ANNUAL">
                  {t("reportCards.types.annual")}
                </option>
              </select>

              <select
                className={inputClass}
                value={yearId}
                onChange={(event) => chooseYear(event.target.value)}
              >
                <option value="">{t("common.choose")}</option>
                {options.years.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>

              <select
                className={inputClass}
                value={classroomId}
                onChange={(event) =>
                  chooseClassroom(event.target.value)
                }
              >
                <option value="">{t("common.choose")}</option>
                {classrooms.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name} • {item.level_name}
                  </option>
                ))}
              </select>

              {mode === "PERIOD" && (
                <select
                  className={inputClass}
                  value={periodId}
                  onChange={(event) =>
                    choosePeriod(event.target.value)
                  }
                >
                  <option value="">{t("common.choose")}</option>
                  {periods.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name}
                    </option>
                  ))}
                </select>
              )}

              {mode === "PERIOD" && (
                <select
                  className={inputClass}
                  value={subjectId}
                  onChange={(event) => {
                    setSubjectId(event.target.value);
                    resetResults();
                  }}
                >
                  <option value="">
                    {t("reportCards.explorer.allSubjects")}
                  </option>
                  {availableSubjects.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name}
                    </option>
                  ))}
                </select>
              )}
            </div>

            {teacherMode && classroomId && !canUseFullReports && !subjectId && (
              <div className="mt-4 rounded-2xl bg-amber-50 px-4 py-3 text-xs leading-5 text-amber-800">
                {t("reportCards.explorer.teacherScope")}
              </div>
            )}

            <div className="mt-4 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={loadExplorer}
                disabled={
                  !classroomId ||
                  (mode === "PERIOD" && !periodId) ||
                  (teacherMode && !canUseFullReports && !subjectId) ||
                  saving === "explore"
                }
                className={primaryButton}
              >
                {saving === "explore" ? (
                  <Loader2 size={16} className="animate-spin" />
                ) : (
                  <Search size={16} />
                )}
                {t("reportCards.explorer.show")}
              </button>

              {isDirection &&
                classroomId &&
                (mode === "ANNUAL" || periodId) &&
                canUseFullReports && (
                  <button
                    type="button"
                    onClick={publishClassroom}
                    disabled={saving === "publish-class"}
                    className="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-medium hover:bg-slate-50 disabled:opacity-40"
                  >
                    <Users size={16} />
                    {t("reportCards.publish.classroom")}
                  </button>
                )}
              {classroomId &&
                (mode === "ANNUAL" || periodId) &&
                canUseFullReports && (
                  <button
                    type="button"
                    onClick={downloadClassZip}
                    disabled={saving === "zip-class"}
                    className="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-medium hover:bg-slate-50 disabled:opacity-40"
                  >
                    {saving === "zip-class" ? (
                      <Loader2 size={16} className="animate-spin" />
                    ) : (
                      <Download size={16} />
                    )}
                    {t("reportCards.publish.downloadZip")}
                  </button>
                )}
            </div>
          </section>

          {classResults && (
            <section className="rounded-3xl border border-slate-200 bg-white p-6">
              <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
                <div>
                  <h2 className="font-semibold">
                    {classResults.classroom_name}
                  </h2>
                  <p className="mt-1 text-xs text-slate-500">
                    {mode === "PERIOD"
                      ? classResults.period_name
                      : classResults.academic_year_name}
                    {" • "}
                    {t("reportCards.explorer.studentsCount", {
                      count: classResults.class_size,
                    })}
                  </p>
                </div>
                <BookOpenText size={20} className="text-slate-400" />
              </div>

              <div className="mt-5 overflow-x-auto">
                <table className="w-full min-w-[760px] text-left text-sm">
                  <thead className="text-xs uppercase text-slate-400">
                    <tr>
                      <th className="px-3 py-3">
                        {t("reportCards.fields.rank")}
                      </th>
                      <th className="px-3 py-3">
                        {t("reportCards.fields.student")}
                      </th>
                      <th className="px-3 py-3">
                        {t("reportCards.fields.average")}
                      </th>
                      <th className="px-3 py-3">
                        {mode === "PERIOD"
                          ? t("reportCards.fields.subjects")
                          : t("reportCards.fields.periods")}
                      </th>
                      <th className="px-3 py-3" />
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {classResults.students.map((student) => (
                      <tr key={student.enrollment_id}>
                        <td className="px-3 py-3 font-semibold">
                          {rankLabel(student.rank)}
                        </td>
                        <td className="px-3 py-3">
                          <div className="font-medium">
                            {student.student_name}
                          </div>
                          <div className="text-xs text-slate-400">
                            {student.matricule}
                          </div>
                        </td>
                        <td className="px-3 py-3 font-semibold">
                          {averageLabel(student.overall_average)}
                        </td>
                        <td className="px-3 py-3">
                          <div className="flex flex-wrap gap-1.5">
                            {(mode === "PERIOD"
                              ? student.subjects || []
                              : student.periods || []
                            )
                              .slice(0, 6)
                              .map((item) => (
                                <span
                                  key={
                                    item.subject_id ||
                                    item.period_id
                                  }
                                  className="rounded-lg bg-slate-50 px-2 py-1 text-xs"
                                >
                                  {item.subject_name ||
                                    item.period_name}
                                  :{" "}
                                  {averageLabel(
                                    item.average ??
                                      item.overall_average
                                  )}
                                </span>
                              ))}
                          </div>
                        </td>
                        <td className="px-3 py-3 text-right">
                          <button
                            type="button"
                            onClick={() =>
                              openStudent(student.enrollment_id)
                            }
                            className="rounded-xl border border-slate-200 px-3 py-2 text-xs font-medium hover:bg-slate-50"
                          >
                            {t("reportCards.explorer.viewStudent")}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {subjectResults && (
            <section className="rounded-3xl border border-slate-200 bg-white p-6">
              <div>
                <h2 className="font-semibold">
                  {subjectResults.subject_name} •{" "}
                  {subjectResults.classroom_name}
                </h2>
                <p className="mt-1 text-xs text-slate-500">
                  {subjectResults.period_name}
                </p>
              </div>

              <div className="mt-5 grid gap-3 sm:grid-cols-3">
                <ResultCard
                  label={t("reportCards.subject.classAverage")}
                  value={averageLabel(subjectResults.class_average)}
                />
                <ResultCard
                  label={t("reportCards.subject.highest")}
                  value={averageLabel(subjectResults.highest)}
                />
                <ResultCard
                  label={t("reportCards.subject.lowest")}
                  value={averageLabel(subjectResults.lowest)}
                />
              </div>

              <div className="mt-5 overflow-x-auto">
                <table className="w-full min-w-[620px] text-left text-sm">
                  <thead className="text-xs uppercase text-slate-400">
                    <tr>
                      <th className="px-3 py-3">
                        {t("reportCards.fields.rank")}
                      </th>
                      <th className="px-3 py-3">
                        {t("reportCards.fields.student")}
                      </th>
                      <th className="px-3 py-3">
                        {t("reportCards.fields.average")}
                      </th>
                      <th className="px-3 py-3">
                        {t("reportCards.subject.assessments")}
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {subjectResults.students.map((student) => (
                      <tr key={student.enrollment_id}>
                        <td className="px-3 py-3 font-semibold">
                          {rankLabel(student.rank)}
                        </td>
                        <td className="px-3 py-3">
                          <div className="font-medium">
                            {student.student_name}
                          </div>
                          <div className="text-xs text-slate-400">
                            {student.matricule}
                          </div>
                        </td>
                        <td className="px-3 py-3">
                          {student.average === null
                            ? "—"
                            : `${averageLabel(
                                student.average
                              )}/${averageLabel(
                                student.max_score
                              )}`}
                        </td>
                        <td className="px-3 py-3">
                          {student.assessment_count}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {studentResult && (
            <section className="rounded-3xl border border-slate-200 bg-white p-6">
              <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
                <div>
                  <div className="text-xs font-medium uppercase tracking-[0.12em] text-slate-400">
                    {t("reportCards.student.preview")}
                  </div>
                  <h2 className="mt-2 text-xl font-semibold">
                    {studentResult.student_name}
                  </h2>
                  <p className="mt-1 text-xs text-slate-500">
                    {studentResult.classroom_name} •{" "}
                    {studentResult.academic_year_name}
                    {studentResult.period_name
                      ? ` • ${studentResult.period_name}`
                      : ""}
                  </p>
                </div>

                <div className="flex gap-2">
                  <span className="rounded-xl bg-slate-950 px-3 py-2 text-sm font-semibold text-white">
                    {rankLabel(studentResult.rank)}
                  </span>
                  <span className="rounded-xl bg-blue-50 px-3 py-2 text-sm font-semibold text-blue-700">
                    {averageLabel(studentResult.overall_average)}
                  </span>
                </div>
              </div>

              <div className="mt-5 overflow-x-auto">
                <table className="w-full min-w-[760px] text-left text-sm">
                  <thead className="text-xs uppercase text-slate-400">
                    <tr>
                      <th className="px-3 py-3">
                        {t("reportCards.fields.subject")}
                      </th>
                      <th className="px-3 py-3">
                        {t("reportCards.fields.average")}
                      </th>
                      <th className="px-3 py-3">
                        {t("reportCards.fields.coefficient")}
                      </th>
                      {mode === "PERIOD" && (
                        <>
                          <th className="px-3 py-3">
                            {t("reportCards.fields.rank")}
                          </th>
                          <th className="px-3 py-3">
                            {t("reportCards.fields.classAverage")}
                          </th>
                        </>
                      )}
                      {isDirection && (
                        <th className="px-3 py-3">
                          {t("reportCards.fields.appreciation")}
                        </th>
                      )}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {(studentResult.subjects || []).map((subject) => (
                      <tr key={subject.subject_id}>
                        <td className="px-3 py-3 font-medium">
                          {subject.subject_name}
                        </td>
                        <td className="px-3 py-3">
                          {averageLabel(subject.average)}/
                          {averageLabel(subject.max_score)}
                        </td>
                        <td className="px-3 py-3">
                          {averageLabel(subject.coefficient)}
                        </td>
                        {mode === "PERIOD" && (
                          <>
                            <td className="px-3 py-3">
                              {rankLabel(subject.rank)}
                            </td>
                            <td className="px-3 py-3">
                              {averageLabel(subject.class_average)}
                            </td>
                          </>
                        )}
                        {isDirection && (
                          <td className="px-3 py-3">
                            <input
                              className="w-full min-w-[220px] rounded-lg border border-slate-200 px-3 py-2 text-xs"
                              placeholder={t(
                                "reportCards.publish.autoIfEmpty"
                              )}
                              value={
                                subjectComments[
                                  String(subject.subject_id)
                                ] || ""
                              }
                              onChange={(event) =>
                                setSubjectComments((current) => ({
                                  ...current,
                                  [String(subject.subject_id)]:
                                    event.target.value,
                                }))
                              }
                            />
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {isDirection && (
                <div className="mt-5 grid gap-4 lg:grid-cols-2">
                  <div>
                    <label className="text-xs font-medium text-slate-500">
                      {t("reportCards.publish.teacherComment")}
                    </label>
                    <textarea
                      rows={4}
                      className={`${inputClass} mt-2 resize-y`}
                      value={teacherComment}
                      onChange={(event) =>
                        setTeacherComment(event.target.value)
                      }
                      placeholder={t(
                        "reportCards.publish.autoIfEmpty"
                      )}
                    />
                  </div>

                  <div>
                    <label className="text-xs font-medium text-slate-500">
                      {t("reportCards.publish.generalComment")}
                    </label>
                    <textarea
                      rows={4}
                      className={`${inputClass} mt-2 resize-y`}
                      value={generalComment}
                      onChange={(event) =>
                        setGeneralComment(event.target.value)
                      }
                    />
                  </div>

                  <div className="lg:col-span-2 flex flex-wrap justify-end gap-2">
                    <button
                      type="button"
                      onClick={previewStudentPdf}
                      disabled={saving === "preview-student"}
                      className="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-medium hover:bg-slate-50 disabled:opacity-40"
                    >
                      {saving === "preview-student" ? (
                        <Loader2 size={16} className="animate-spin" />
                      ) : (
                        <Eye size={16} />
                      )}
                      {t("reportCards.publish.preview")}
                    </button>

                    <button
                      type="button"
                      onClick={publishStudent}
                      disabled={saving === "publish-student"}
                      className={primaryButton}
                    >
                      <FileText size={16} />
                      {t("reportCards.publish.student")}
                    </button>
                  </div>
                </div>
              )}
            </section>
          )}
        </>
      )}

      {tab === "templates" && isDirection && (
        <ReportCardTemplatesPanel
          cycles={options.cycles || []}
          t={t}
          onMessage={notifySuccess}
          onError={notifyError}
        />
      )}

      {tab === "published" && (
        <section className="rounded-3xl border border-slate-200 bg-white p-6">
          <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
            <div>
              <h2 className="font-semibold">
                {t("reportCards.published.title")}
              </h2>
              <p className="mt-1 text-xs text-slate-500">
                {t("reportCards.published.help")}
              </p>
            </div>

            <button
              type="button"
              onClick={() => load()}
              className="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-xs font-medium hover:bg-slate-50"
            >
              <RefreshCw size={14} />
              {t("reportCards.published.refresh")}
            </button>
          </div>

          <div className="mt-5 space-y-3">
            {!snapshots.length && (
              <div className="rounded-2xl bg-slate-50 p-8 text-center text-sm text-slate-500">
                {t("reportCards.published.empty")}
              </div>
            )}

            {snapshots.map((snapshot) => (
              <div
                key={snapshot.id}
                className="grid gap-4 rounded-2xl border border-slate-200 p-4 lg:grid-cols-[1.3fr_.8fr_auto] lg:items-center"
              >
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-medium">
                      {snapshot.student_name}
                    </span>
                    <span className="rounded-full bg-slate-100 px-2 py-1 text-[10px] font-medium text-slate-600">
                      v{snapshot.version}
                    </span>
                    {latestSnapshotIds.has(snapshot.id) && (
                      <span className="rounded-full bg-emerald-50 px-2 py-1 text-[10px] font-medium text-emerald-700">
                        {t("reportCards.published.latest")}
                      </span>
                    )}
                  </div>
                  <div className="mt-1 text-xs text-slate-500">
                    {snapshot.classroom_name} •{" "}
                    {snapshot.academic_year_name}
                    {snapshot.period_name
                      ? ` • ${snapshot.period_name}`
                      : ` • ${t("reportCards.types.annual")}`}
                  </div>
                  <div className="mt-1 text-[11px] text-slate-400">
                    {new Date(snapshot.published_at).toLocaleString()}
                  </div>
                </div>

                <div className="text-xs text-slate-500">
                  <div>
                    {t("reportCards.published.fingerprint")}
                  </div>
                  <div className="mt-1 font-mono text-[11px]">
                    {snapshot.payload_sha256
                      .slice(0, 16)
                      .toUpperCase()}
                  </div>
                </div>

                <div className="flex flex-wrap justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => downloadPdf(snapshot)}
                    className="inline-flex items-center gap-1.5 rounded-xl bg-slate-950 px-3 py-2 text-xs font-medium text-white"
                  >
                    <Download size={14} />
                    PDF
                  </button>
                  <button
                    type="button"
                    onClick={() => copyVerification(snapshot)}
                    className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 px-3 py-2 text-xs font-medium hover:bg-slate-50"
                  >
                    <ShieldCheck size={14} />
                    {t("reportCards.published.verify")}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
