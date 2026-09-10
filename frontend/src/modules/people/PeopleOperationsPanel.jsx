import { useEffect, useMemo, useState } from "react";
import {
  ArrowRightLeft,
  CheckSquare2,
  Download,
  FileSpreadsheet,
  Loader2,
  RefreshCw,
  Upload,
} from "lucide-react";

import Field from "../../components/Field";
import { useI18n } from "../../i18n";
import api from "../../services/api";

const inputClass =
  "w-full rounded-xl border border-slate-200 bg-white px-3.5 py-3 text-sm outline-none focus:border-slate-400 focus:ring-4 focus:ring-slate-100";

const primaryButton =
  "inline-flex items-center justify-center gap-2 rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-medium text-white disabled:opacity-40";

const importEndpoints = {
  students: "/people/imports/students/",
  teachers: "/people/imports/teachers/",
  guardians: "/people/imports/guardians/",
};

const templateEndpoints = {
  students: "/people/imports/templates/students/",
  teachers: "/people/imports/templates/teachers/",
  guardians: "/people/imports/templates/guardians/",
};

const exportEndpoints = {
  students: "/people/exports/students/",
  teachers: "/people/exports/teachers/",
  guardians: "/people/exports/guardians/",
  enrollments: "/people/exports/enrollments/",
};

function parseError(error, fallback) {
  const payload = error?.response?.data;

  if (!payload) return fallback;
  if (payload.detail) return String(payload.detail);

  const first = Object.values(payload)[0];

  if (Array.isArray(first)) return String(first[0]);

  if (first && typeof first === "object") {
    const nested = Object.values(first)[0];
    if (Array.isArray(nested)) return String(nested[0]);
  }

  return fallback;
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

export default function PeopleOperationsPanel({ onChanged }) {
  const { t } = useI18n();

  const [tab, setTab] = useState("import");
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [saving, setSaving] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const [students, setStudents] = useState([]);
  const [years, setYears] = useState([]);
  const [classrooms, setClassrooms] = useState([]);
  const [enrollments, setEnrollments] = useState([]);

  const [importEntity, setImportEntity] = useState("students");
  const [importFile, setImportFile] = useState(null);
  const [importDryRun, setImportDryRun] = useState(false);
  const [importClassroom, setImportClassroom] = useState("");

  const [bulkYear, setBulkYear] = useState("");
  const [bulkClassroom, setBulkClassroom] = useState("");
  const [selectedStudentIds, setSelectedStudentIds] = useState([]);

  const [sourceYear, setSourceYear] = useState("");
  const [targetYear, setTargetYear] = useState("");
  const [promotionRows, setPromotionRows] = useState([]);

  const [prepareForm, setPrepareForm] = useState({
    source_academic_year: "",
    name: "",
    start_date: "",
    end_date: "",
    period_system: "TRIMESTER",
    is_active: false,
    clone_classrooms: true,
    clone_periods: true,
  });

  const load = async ({ initial = false } = {}) => {
    if (initial) setLoading(true);
    else setSyncing(true);

    setError("");

    try {
      const [studentsRes, yearsRes, classroomsRes, enrollmentsRes] =
        await Promise.all([
          api.get("/people/students/"),
          api.get("/academics/years/"),
          api.get("/academics/classrooms/"),
          api.get("/people/enrollments/"),
        ]);

      setStudents(studentsRes.data);
      setYears(yearsRes.data);
      setClassrooms(classroomsRes.data);
      setEnrollments(enrollmentsRes.data);

      const active =
        yearsRes.data.find((year) => year.is_active) ||
        yearsRes.data[0] ||
        null;

      if (active) {
        setBulkYear((current) => current || String(active.id));
        setSourceYear((current) => current || String(active.id));
        setPrepareForm((current) => ({
          ...current,
          source_academic_year:
            current.source_academic_year || String(active.id),
          period_system:
            current.period_system || active.period_system || "TRIMESTER",
        }));
      }
    } catch (err) {
      setError(parseError(err, t("peopleOps.errors.load")));
    } finally {
      if (initial) setLoading(false);
      else setSyncing(false);
    }
  };

  useEffect(() => {
    load({ initial: true });
  }, []);

  const activeYear = useMemo(
    () =>
      years.find((year) => year.is_active) ||
      years[0] ||
      null,
    [years]
  );

  const bulkClassrooms = useMemo(
    () =>
      classrooms.filter(
        (classroom) =>
          String(classroom.academic_year) === String(bulkYear)
      ),
    [classrooms, bulkYear]
  );

  const targetClassrooms = useMemo(
    () =>
      classrooms.filter(
        (classroom) =>
          String(classroom.academic_year) === String(targetYear)
      ),
    [classrooms, targetYear]
  );

  const selectedStudents = new Set(selectedStudentIds.map(Number));

  const toggleStudent = (id) => {
    const next = new Set(selectedStudents);
    const numericId = Number(id);

    if (next.has(numericId)) next.delete(numericId);
    else next.add(numericId);

    setSelectedStudentIds(Array.from(next));
  };

  const submitImport = async (event) => {
    event.preventDefault();

    if (!importFile) {
      setError(t("peopleOps.import.fileRequired"));
      return;
    }

    setSaving("import");
    setError("");
    setMessage("");

    const formData = new FormData();
    formData.append("file", importFile);
    formData.append("dry_run", String(importDryRun));

    if (importEntity === "students" && importClassroom) {
      const classroom = classrooms.find(
        (item) => String(item.id) === String(importClassroom)
      );

      if (classroom) {
        formData.append("classroom", classroom.id);
        formData.append("academic_year", classroom.academic_year);
      }
    }

    try {
      const { data } = await api.post(
        importEndpoints[importEntity],
        formData
      );

      setMessage(
        t("peopleOps.import.result", {
          created: data.created,
          updated: data.updated,
          enrolled: data.enrolled,
          errors: data.errors.length,
        })
      );

      if (!importDryRun) {
        await load();
        await onChanged?.();
      }
    } catch (err) {
      setError(parseError(err, t("peopleOps.errors.import")));
    } finally {
      setSaving("");
    }
  };

  const downloadTemplate = async () => {
    setSaving("template");
    setError("");

    try {
      const { data } = await api.get(
        templateEndpoints[importEntity],
        { responseType: "blob" }
      );
      downloadBlob(data, `template-${importEntity}.csv`);
    } catch (err) {
      setError(parseError(err, t("peopleOps.errors.download")));
    } finally {
      setSaving("");
    }
  };

  const submitBulkAssignment = async (event) => {
    event.preventDefault();

    if (!selectedStudentIds.length) {
      setError(t("peopleOps.bulk.selectStudents"));
      return;
    }

    setSaving("bulk");
    setError("");
    setMessage("");

    try {
      const { data } = await api.post(
        "/people/bulk/class-assignment/",
        {
          student_ids: selectedStudentIds,
          academic_year: Number(bulkYear),
          classroom: Number(bulkClassroom),
        }
      );

      setMessage(
        t("peopleOps.bulk.result", {
          created: data.created,
          updated: data.updated,
        })
      );
      setSelectedStudentIds([]);

      await load();
      await onChanged?.();
    } catch (err) {
      setError(parseError(err, t("peopleOps.errors.bulk")));
    } finally {
      setSaving("");
    }
  };

  const previewPromotions = async () => {
    if (!sourceYear) return;

    setSaving("preview");
    setError("");
    setMessage("");

    try {
      const { data } = await api.post(
        "/people/promotions/preview/",
        {
          academic_year: Number(sourceYear),
        }
      );

      setPromotionRows(
        data.items.map((item) => ({
          ...item,
          selected: true,
          decision:
            item.suggested_decision === "PENDING"
              ? "PROMOTED"
              : item.suggested_decision,
          target_classroom: "",
          reason: "",
        }))
      );
    } catch (err) {
      setError(parseError(err, t("peopleOps.errors.preview")));
    } finally {
      setSaving("");
    }
  };

  const updatePromotionRow = (index, patch) => {
    setPromotionRows((current) =>
      current.map((row, rowIndex) =>
        rowIndex === index ? { ...row, ...patch } : row
      )
    );
  };

  const applyPromotions = async () => {
    const items = promotionRows
      .filter((row) => row.selected)
      .map((row) => ({
        enrollment_id: row.enrollment_id,
        decision: row.decision,
        target_classroom:
          ["PROMOTED", "REPEATED"].includes(row.decision)
            ? Number(row.target_classroom) || null
            : null,
        reason: row.reason || "",
      }));

    if (!items.length) {
      setError(t("peopleOps.promotion.selectRows"));
      return;
    }

    const missingTarget = items.some(
      (item) =>
        ["PROMOTED", "REPEATED"].includes(item.decision) &&
        !item.target_classroom
    );

    if (missingTarget) {
      setError(t("peopleOps.promotion.targetRequired"));
      return;
    }

    setSaving("promotion");
    setError("");
    setMessage("");

    try {
      const { data } = await api.post(
        "/people/promotions/apply/",
        { items }
      );

      setMessage(
        t("peopleOps.promotion.result", {
          promoted: data.promoted,
          repeated: data.repeated,
          graduated: data.graduated,
          transferred: data.transferred,
          withdrawn: data.withdrawn,
        })
      );

      await load();
      await previewPromotions();
      await onChanged?.();
    } catch (err) {
      setError(parseError(err, t("peopleOps.errors.promotion")));
    } finally {
      setSaving("");
    }
  };

  const prepareYear = async (event) => {
    event.preventDefault();

    setSaving("prepare");
    setError("");
    setMessage("");

    try {
      const payload = {
        ...prepareForm,
        source_academic_year: Number(
          prepareForm.source_academic_year
        ),
      };

      const { data } = await api.post(
        "/people/academic-years/prepare/",
        payload
      );

      setMessage(
        t("peopleOps.prepare.result", {
          year: data.academic_year_name,
          classes: data.classrooms_created,
          periods: data.periods_created,
        })
      );

      await load();
      await onChanged?.();
    } catch (err) {
      setError(parseError(err, t("peopleOps.errors.prepare")));
    } finally {
      setSaving("");
    }
  };

  const exportList = async (entity, format) => {
    setSaving(`export-${entity}-${format}`);
    setError("");

    try {
      const params = new URLSearchParams();
      params.set("file_format", format);

      if (entity === "students" || entity === "enrollments") {
        if (activeYear) {
          params.set("academic_year", activeYear.id);
        }
      }

      const { data } = await api.get(
        `${exportEndpoints[entity]}?${params.toString()}`,
        { responseType: "blob" }
      );

      downloadBlob(
        data,
        `${entity}.${format === "xlsx" ? "xlsx" : "csv"}`
      );
    } catch (err) {
      setError(parseError(err, t("peopleOps.errors.export")));
    } finally {
      setSaving("");
    }
  };

  if (loading) {
    return (
      <div className="grid min-h-[260px] place-items-center rounded-3xl border border-slate-200 bg-white">
        <div className="inline-flex items-center gap-2 text-sm text-slate-500">
          <Loader2 size={17} className="animate-spin" />
          {t("peopleOps.loading")}
        </div>
      </div>
    );
  }

  const tabs = [
    ["import", t("peopleOps.tabs.import"), Upload],
    ["bulk", t("peopleOps.tabs.bulk"), CheckSquare2],
    ["promotion", t("peopleOps.tabs.promotion"), ArrowRightLeft],
    ["prepare", t("peopleOps.tabs.prepare"), RefreshCw],
    ["export", t("peopleOps.tabs.export"), Download],
  ];

  return (
    <div className="space-y-5">
      <div className="flex flex-col justify-between gap-4 xl:flex-row xl:items-end">
        <div>
          <div className="text-xs font-medium uppercase tracking-[0.18em] text-slate-400">
            {t("peopleOps.step")}
          </div>
          <h2 className="mt-2 text-2xl font-semibold tracking-tight">
            {t("peopleOps.title")}
          </h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">
            {t("peopleOps.description")}
          </p>
        </div>

        {syncing && (
          <div className="inline-flex items-center gap-2 text-xs text-slate-400">
            <RefreshCw size={13} className="animate-spin" />
            {t("peopleOps.syncing")}
          </div>
        )}
      </div>

      {error && (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {error}
        </div>
      )}

      {message && (
        <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          {message}
        </div>
      )}

      <div className="flex gap-1 overflow-x-auto rounded-2xl border border-slate-200 bg-white p-1.5">
        {tabs.map(([id, label, Icon]) => (
          <button
            key={id}
            type="button"
            onClick={() => {
              setTab(id);
              setError("");
              setMessage("");
            }}
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

      {tab === "import" && (
        <div className="grid gap-5 xl:grid-cols-[.8fr_1.2fr]">
          <form
            onSubmit={submitImport}
            className="rounded-3xl border border-slate-200 bg-white p-6"
          >
            <h3 className="font-semibold">
              {t("peopleOps.import.title")}
            </h3>
            <p className="mt-1 text-xs leading-5 text-slate-500">
              {t("peopleOps.import.help")}
            </p>

            <div className="mt-5 space-y-4">
              <Field label={t("peopleOps.import.entity")}>
                <select
                  className={inputClass}
                  value={importEntity}
                  onChange={(e) => {
                    setImportEntity(e.target.value);
                    setImportFile(null);
                  }}
                >
                  <option value="students">
                    {t("people.tabs.students")}
                  </option>
                  <option value="teachers">
                    {t("people.tabs.teachers")}
                  </option>
                  <option value="guardians">
                    {t("people.tabs.guardians")}
                  </option>
                </select>
              </Field>

              <Field label={t("peopleOps.import.file")}>
                <input
                  key={importEntity}
                  required
                  type="file"
                  accept=".csv,.xlsx"
                  className={inputClass}
                  onChange={(e) =>
                    setImportFile(e.target.files?.[0] || null)
                  }
                />
              </Field>

              {importEntity === "students" && (
                <Field
                  label={t("peopleOps.import.classroom")}
                  hint={t("common.optional")}
                >
                  <select
                    className={inputClass}
                    value={importClassroom}
                    onChange={(e) =>
                      setImportClassroom(e.target.value)
                    }
                  >
                    <option value="">
                      {t("peopleOps.import.noEnrollment")}
                    </option>
                    {classrooms.map((classroom) => (
                      <option
                        key={classroom.id}
                        value={classroom.id}
                      >
                        {classroom.academic_year_name} •{" "}
                        {classroom.name}
                      </option>
                    ))}
                  </select>
                </Field>
              )}

              <label className="flex items-center gap-3 rounded-xl border border-slate-200 px-3.5 py-3 text-sm">
                <input
                  type="checkbox"
                  checked={importDryRun}
                  onChange={(e) =>
                    setImportDryRun(e.target.checked)
                  }
                />
                {t("peopleOps.import.dryRun")}
              </label>

              <div className="grid gap-2 sm:grid-cols-2">
                <button
                  type="button"
                  onClick={downloadTemplate}
                  disabled={saving === "template"}
                  className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
                >
                  <FileSpreadsheet size={16} />
                  {t("peopleOps.import.template")}
                </button>

                <button
                  className={primaryButton}
                  disabled={saving === "import"}
                >
                  {saving === "import" ? (
                    <Loader2 size={16} className="animate-spin" />
                  ) : (
                    <Upload size={16} />
                  )}
                  {t("peopleOps.import.run")}
                </button>
              </div>
            </div>
          </form>

          <section className="rounded-3xl border border-slate-200 bg-white p-6">
            <h3 className="font-semibold">
              {t("peopleOps.import.expectedColumns")}
            </h3>
            <div className="mt-4 space-y-3 text-sm text-slate-600">
              <div className="rounded-2xl bg-slate-50 p-4">
                <strong>{t("people.tabs.students")}</strong>
                <div className="mt-2 font-mono text-xs leading-6">
                  matricule, first_name, last_name, gender,
                  date_of_birth, phone, email, admission_date
                </div>
              </div>
              <div className="rounded-2xl bg-slate-50 p-4">
                <strong>{t("people.tabs.teachers")}</strong>
                <div className="mt-2 font-mono text-xs leading-6">
                  employee_number, first_name, last_name, phone,
                  email, speciality, hire_date
                </div>
              </div>
              <div className="rounded-2xl bg-slate-50 p-4">
                <strong>{t("people.tabs.guardians")}</strong>
                <div className="mt-2 font-mono text-xs leading-6">
                  first_name, last_name, phone, alternate_phone,
                  email, occupation, preferred_language
                </div>
              </div>
            </div>
          </section>
        </div>
      )}

      {tab === "bulk" && (
        <form
          onSubmit={submitBulkAssignment}
          className="rounded-3xl border border-slate-200 bg-white p-6"
        >
          <div>
            <h3 className="font-semibold">
              {t("peopleOps.bulk.title")}
            </h3>
            <p className="mt-1 text-xs leading-5 text-slate-500">
              {t("peopleOps.bulk.help")}
            </p>
          </div>

          <div className="mt-5 grid gap-4 sm:grid-cols-2">
            <Field label={t("people.enrollments.year")}>
              <select
                required
                className={inputClass}
                value={bulkYear}
                onChange={(e) => {
                  setBulkYear(e.target.value);
                  setBulkClassroom("");
                }}
              >
                <option value="">{t("common.choose")}</option>
                {years.map((year) => (
                  <option key={year.id} value={year.id}>
                    {year.name}
                  </option>
                ))}
              </select>
            </Field>

            <Field label={t("people.enrollments.classroom")}>
              <select
                required
                className={inputClass}
                value={bulkClassroom}
                onChange={(e) =>
                  setBulkClassroom(e.target.value)
                }
              >
                <option value="">{t("common.choose")}</option>
                {bulkClassrooms.map((classroom) => (
                  <option
                    key={classroom.id}
                    value={classroom.id}
                  >
                    {classroom.name} • {classroom.level_name}
                  </option>
                ))}
              </select>
            </Field>
          </div>

          <div className="mt-5 rounded-2xl border border-slate-200 bg-slate-50 p-3">
            <div className="flex flex-col justify-between gap-2 border-b border-slate-200 pb-3 sm:flex-row sm:items-center">
              <div className="text-sm font-medium">
                {t("peopleOps.bulk.students")}
              </div>
              <div className="flex items-center gap-2 text-xs">
                <span className="rounded-full bg-white px-2.5 py-1">
                  {t("peopleOps.bulk.selected", {
                    count: selectedStudentIds.length,
                  })}
                </span>
                <button
                  type="button"
                  onClick={() =>
                    setSelectedStudentIds(
                      students.map((student) => student.id)
                    )
                  }
                  className="rounded-lg px-2.5 py-1.5 hover:bg-white"
                >
                  {t("peopleOps.bulk.selectAll")}
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedStudentIds([])}
                  className="rounded-lg px-2.5 py-1.5 hover:bg-white"
                >
                  {t("peopleOps.bulk.clear")}
                </button>
              </div>
            </div>

            <div className="mt-3 grid max-h-80 gap-2 overflow-y-auto sm:grid-cols-2 lg:grid-cols-3">
              {students.map((student) => {
                const selected = selectedStudents.has(
                  Number(student.id)
                );

                return (
                  <label
                    key={student.id}
                    className={`flex cursor-pointer items-center gap-3 rounded-xl border px-3 py-2.5 text-sm ${
                      selected
                        ? "border-slate-900 bg-slate-950 text-white"
                        : "border-slate-200 bg-white"
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={selected}
                      onChange={() => toggleStudent(student.id)}
                    />
                    <span className="min-w-0 flex-1 truncate">
                      {student.last_name} {student.first_name}
                    </span>
                    <span className="text-[10px] opacity-70">
                      {student.matricule}
                    </span>
                  </label>
                );
              })}
            </div>
          </div>

          <div className="mt-5 flex justify-end">
            <button
              className={primaryButton}
              disabled={
                saving === "bulk" ||
                !bulkYear ||
                !bulkClassroom ||
                !selectedStudentIds.length
              }
            >
              <CheckSquare2 size={16} />
              {t("peopleOps.bulk.assign")}
            </button>
          </div>
        </form>
      )}

      {tab === "promotion" && (
        <div className="space-y-5">
          <section className="rounded-3xl border border-slate-200 bg-white p-6">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-[1fr_1fr_auto] lg:items-end">
              <Field label={t("peopleOps.promotion.sourceYear")}>
                <select
                  className={inputClass}
                  value={sourceYear}
                  onChange={(e) => {
                    setSourceYear(e.target.value);
                    setPromotionRows([]);
                  }}
                >
                  <option value="">{t("common.choose")}</option>
                  {years.map((year) => (
                    <option key={year.id} value={year.id}>
                      {year.name}
                    </option>
                  ))}
                </select>
              </Field>

              <Field label={t("peopleOps.promotion.targetYear")}>
                <select
                  className={inputClass}
                  value={targetYear}
                  onChange={(e) =>
                    setTargetYear(e.target.value)
                  }
                >
                  <option value="">{t("common.choose")}</option>
                  {years
                    .filter(
                      (year) =>
                        String(year.id) !== String(sourceYear)
                    )
                    .map((year) => (
                      <option key={year.id} value={year.id}>
                        {year.name}
                      </option>
                    ))}
                </select>
              </Field>

              <button
                type="button"
                onClick={previewPromotions}
                disabled={!sourceYear || saving === "preview"}
                className={primaryButton}
              >
                <RefreshCw size={16} />
                {t("peopleOps.promotion.preview")}
              </button>
            </div>
          </section>

          {promotionRows.length > 0 && (
            <section className="rounded-3xl border border-slate-200 bg-white p-6">
              <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
                <div>
                  <h3 className="font-semibold">
                    {t("peopleOps.promotion.title")}
                  </h3>
                  <p className="mt-1 text-xs text-slate-500">
                    {t("peopleOps.promotion.help")}
                  </p>
                </div>

                <button
                  type="button"
                  onClick={applyPromotions}
                  disabled={saving === "promotion"}
                  className={primaryButton}
                >
                  <ArrowRightLeft size={16} />
                  {t("peopleOps.promotion.apply")}
                </button>
              </div>

              <div className="mt-5 space-y-3">
                {promotionRows.map((row, index) => (
                  <div
                    key={row.enrollment_id}
                    className="grid gap-3 rounded-2xl border border-slate-200 p-4 xl:grid-cols-[32px_1.2fr_120px_180px_1fr]"
                  >
                    <div className="pt-2">
                      <input
                        type="checkbox"
                        checked={row.selected}
                        onChange={(e) =>
                          updatePromotionRow(index, {
                            selected: e.target.checked,
                          })
                        }
                      />
                    </div>

                    <div>
                      <div className="font-medium">
                        {row.student_name}
                      </div>
                      <div className="mt-1 text-xs text-slate-500">
                        {row.classroom_name} • {row.level_name}
                      </div>
                      <div className="mt-1 text-xs text-slate-400">
                        {t("peopleOps.promotion.threshold")}:{" "}
                        {row.threshold}
                      </div>
                    </div>

                    <div className="text-sm">
                      <div className="text-xs text-slate-400">
                        {t("people.enrollments.finalAverage")}
                      </div>
                      <div className="mt-1 font-medium">
                        {row.final_average ?? "—"}
                      </div>
                    </div>

                    <select
                      className={inputClass}
                      value={row.decision}
                      onChange={(e) =>
                        updatePromotionRow(index, {
                          decision: e.target.value,
                        })
                      }
                    >
                      <option value="PROMOTED">
                        {t("people.promotion.promoted")}
                      </option>
                      <option value="REPEATED">
                        {t("people.promotion.repeated")}
                      </option>
                      <option value="GRADUATED">
                        {t("people.promotion.graduated")}
                      </option>
                      <option value="TRANSFERRED">
                        {t("people.promotion.transferred")}
                      </option>
                      <option value="WITHDRAWN">
                        {t("people.promotion.withdrawn")}
                      </option>
                    </select>

                    {["PROMOTED", "REPEATED"].includes(
                      row.decision
                    ) ? (
                      <select
                        className={inputClass}
                        value={row.target_classroom}
                        disabled={!targetYear}
                        onChange={(e) =>
                          updatePromotionRow(index, {
                            target_classroom: e.target.value,
                          })
                        }
                      >
                        <option value="">
                          {t("peopleOps.promotion.targetClass")}
                        </option>
                        {targetClassrooms.map((classroom) => (
                          <option
                            key={classroom.id}
                            value={classroom.id}
                          >
                            {classroom.name} •{" "}
                            {classroom.level_name}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <input
                        className={inputClass}
                        placeholder={t(
                          "peopleOps.promotion.reason"
                        )}
                        value={row.reason}
                        onChange={(e) =>
                          updatePromotionRow(index, {
                            reason: e.target.value,
                          })
                        }
                      />
                    )}
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>
      )}

      {tab === "prepare" && (
        <form
          onSubmit={prepareYear}
          className="rounded-3xl border border-slate-200 bg-white p-6"
        >
          <div>
            <h3 className="font-semibold">
              {t("peopleOps.prepare.title")}
            </h3>
            <p className="mt-1 max-w-3xl text-xs leading-5 text-slate-500">
              {t("peopleOps.prepare.help")}
            </p>
          </div>

          <div className="mt-5 grid gap-4 sm:grid-cols-2">
            <Field label={t("peopleOps.prepare.source")}>
              <select
                required
                className={inputClass}
                value={prepareForm.source_academic_year}
                onChange={(e) => {
                  const year = years.find(
                    (item) =>
                      String(item.id) === e.target.value
                  );
                  setPrepareForm({
                    ...prepareForm,
                    source_academic_year: e.target.value,
                    period_system:
                      year?.period_system ||
                      prepareForm.period_system,
                  });
                }}
              >
                <option value="">{t("common.choose")}</option>
                {years.map((year) => (
                  <option key={year.id} value={year.id}>
                    {year.name}
                  </option>
                ))}
              </select>
            </Field>

            <Field label={t("peopleOps.prepare.name")}>
              <input
                required
                className={inputClass}
                value={prepareForm.name}
                onChange={(e) =>
                  setPrepareForm({
                    ...prepareForm,
                    name: e.target.value,
                  })
                }
                placeholder="2027/2028"
              />
            </Field>

            <Field label={t("peopleOps.prepare.start")}>
              <input
                required
                type="date"
                className={inputClass}
                value={prepareForm.start_date}
                onChange={(e) =>
                  setPrepareForm({
                    ...prepareForm,
                    start_date: e.target.value,
                  })
                }
              />
            </Field>

            <Field label={t("peopleOps.prepare.end")}>
              <input
                required
                type="date"
                className={inputClass}
                value={prepareForm.end_date}
                onChange={(e) =>
                  setPrepareForm({
                    ...prepareForm,
                    end_date: e.target.value,
                  })
                }
              />
            </Field>

            <Field label={t("academics.year.system")}>
              <select
                className={inputClass}
                value={prepareForm.period_system}
                onChange={(e) =>
                  setPrepareForm({
                    ...prepareForm,
                    period_system: e.target.value,
                  })
                }
              >
                <option value="TRIMESTER">
                  {t("academics.year.trimesters")}
                </option>
                <option value="SEMESTER">
                  {t("academics.year.semesters")}
                </option>
                <option value="CUSTOM">
                  {t("academics.year.custom")}
                </option>
              </select>
            </Field>

            <div className="space-y-2 rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <label className="flex items-center gap-3 text-sm">
                <input
                  type="checkbox"
                  checked={prepareForm.clone_classrooms}
                  onChange={(e) =>
                    setPrepareForm({
                      ...prepareForm,
                      clone_classrooms: e.target.checked,
                    })
                  }
                />
                {t("peopleOps.prepare.cloneClasses")}
              </label>

              <label className="flex items-center gap-3 text-sm">
                <input
                  type="checkbox"
                  checked={prepareForm.clone_periods}
                  onChange={(e) =>
                    setPrepareForm({
                      ...prepareForm,
                      clone_periods: e.target.checked,
                    })
                  }
                />
                {t("peopleOps.prepare.clonePeriods")}
              </label>

              <label className="flex items-center gap-3 text-sm">
                <input
                  type="checkbox"
                  checked={prepareForm.is_active}
                  onChange={(e) =>
                    setPrepareForm({
                      ...prepareForm,
                      is_active: e.target.checked,
                    })
                  }
                />
                {t("peopleOps.prepare.activate")}
              </label>
            </div>
          </div>

          <div className="mt-5 flex justify-end">
            <button
              className={primaryButton}
              disabled={saving === "prepare"}
            >
              <RefreshCw size={16} />
              {t("peopleOps.prepare.create")}
            </button>
          </div>
        </form>
      )}

      {tab === "export" && (
        <section className="rounded-3xl border border-slate-200 bg-white p-6">
          <div>
            <h3 className="font-semibold">
              {t("peopleOps.export.title")}
            </h3>
            <p className="mt-1 text-xs leading-5 text-slate-500">
              {t("peopleOps.export.help")}
            </p>
          </div>

          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            {[
              ["students", t("people.tabs.students")],
              ["teachers", t("people.tabs.teachers")],
              ["guardians", t("people.tabs.guardians")],
              ["enrollments", t("people.tabs.enrollments")],
            ].map(([entity, label]) => (
              <div
                key={entity}
                className="flex flex-col justify-between gap-4 rounded-2xl border border-slate-200 p-4 sm:flex-row sm:items-center"
              >
                <div className="font-medium">{label}</div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => exportList(entity, "csv")}
                    className="rounded-xl border border-slate-200 px-3 py-2 text-xs font-medium hover:bg-slate-50"
                  >
                    CSV
                  </button>
                  <button
                    type="button"
                    onClick={() => exportList(entity, "xlsx")}
                    className="rounded-xl bg-slate-950 px-3 py-2 text-xs font-medium text-white"
                  >
                    XLSX
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
