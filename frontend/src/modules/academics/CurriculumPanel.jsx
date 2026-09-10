import { useEffect, useMemo, useState } from "react";
import {
  BookMarked,
  Check,
  Gauge,
  Loader2,
  Plus,
  RefreshCw,
  Sigma,
  Trash2,
  Pencil,
} from "lucide-react";

import Field from "../../components/Field";
import { useI18n } from "../../i18n";
import api from "../../services/api";
import LevelCheckboxSelector from "./LevelCheckboxSelector";
import SubjectEditDialog from "./SubjectEditDialog";
import AssignmentEditDialog from "./AssignmentEditDialog";

const inputClass =
  "w-full rounded-xl border border-slate-200 bg-white px-3.5 py-3 text-sm outline-none focus:border-slate-400 focus:ring-4 focus:ring-slate-100 disabled:bg-slate-50 disabled:text-slate-400";

const primaryButton =
  "inline-flex items-center justify-center gap-2 rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-medium text-white disabled:opacity-40";

const emptySubject = {
  name: "",
  code: "",
  category: "",
  default_teaching_language: "DEFAULT",
  is_active: true,
};

const emptyAssignment = {
  level: "",
  subject: "",
  coefficient: "1",
  max_score_override: "",
  teaching_language: "DEFAULT",
  order: 0,
  is_active: true,
};

const emptyPeriod = {
  academic_year: "",
  name: "",
  code: "",
  kind: "TRIMESTER",
  order: 1,
  weight: "1",
  start_date: "",
  end_date: "",
  is_active: true,
};

function slugify(value) {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function EmptyState({ children }) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-6 text-center text-sm text-slate-500">
      {children}
    </div>
  );
}

function apiError(error, fallback) {
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

export default function CurriculumPanel({ canManage }) {
  const { t } = useI18n();

  const [tab, setTab] = useState("periods");
  const [initialLoading, setInitialLoading] = useState(true);
  const [backgroundLoading, setBackgroundLoading] = useState(false);
  const [saving, setSaving] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const [years, setYears] = useState([]);
  const [periods, setPeriods] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [levels, setLevels] = useState([]);
  const [cycles, setCycles] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [policy, setPolicy] = useState({
    default_max_score: "20.00",
    default_promotion_threshold: "10.00",
  });

  const [periodForm, setPeriodForm] = useState(emptyPeriod);
  const [subjectForm, setSubjectForm] = useState(emptySubject);
  const [assignmentForm, setAssignmentForm] = useState(emptyAssignment);
  const [selectedLevelIds, setSelectedLevelIds] = useState([]);
  const [editingSubject, setEditingSubject] = useState(null);
  const [editingAssignment, setEditingAssignment] = useState(null);

  const activeYear = useMemo(
    () => years.find((year) => year.is_active) || years[0] || null,
    [years]
  );

  const load = async ({ initial = false } = {}) => {
    if (initial) {
      setInitialLoading(true);
    } else {
      setBackgroundLoading(true);
    }

    setError("");

    try {
      const [
        yearsRes,
        periodsRes,
        subjectsRes,
        levelsRes,
        cyclesRes,
        assignmentsRes,
        policyRes,
      ] = await Promise.all([
        api.get("/academics/years/"),
        api.get("/academics/periods/"),
        api.get("/academics/subjects/"),
        api.get("/academics/levels/"),
        api.get("/academics/cycles/"),
        api.get("/academics/level-subjects/"),
        api.get("/academics/policy/"),
      ]);

      setYears(yearsRes.data);
      setPeriods(periodsRes.data);
      setSubjects(subjectsRes.data);
      setLevels(levelsRes.data);
      setCycles(cyclesRes.data);
      setAssignments(assignmentsRes.data);
      setPolicy(policyRes.data);

      const active =
        yearsRes.data.find((year) => year.is_active) ||
        yearsRes.data[0];

      setPeriodForm((form) => ({
        ...form,
        academic_year:
          form.academic_year ||
          (active ? String(active.id) : ""),
        kind:
          form.kind ||
          (active?.period_system === "SEMESTER"
            ? "SEMESTER"
            : "TRIMESTER"),
      }));

      setAssignmentForm((form) => ({
        ...form,
        subject:
          form.subject ||
          (subjectsRes.data[0]
            ? String(subjectsRes.data[0].id)
            : ""),
      }));
    } catch (err) {
      setError(
        apiError(
          err,
          t("curriculum.errors.load")
        )
      );
    } finally {
      if (initial) {
        setInitialLoading(false);
      } else {
        setBackgroundLoading(false);
      }
    }
  };

  useEffect(() => {
    load({ initial: true });
  }, []);

  const silentRefresh = () => load();

  const createPeriod = async (event) => {
    event.preventDefault();
    setSaving("period");
    setError("");
    setMessage("");

    try {
      await api.post("/academics/periods/", {
        ...periodForm,
        academic_year: Number(periodForm.academic_year),
        order: Number(periodForm.order),
        weight: Number(periodForm.weight),
        start_date: periodForm.start_date || null,
        end_date: periodForm.end_date || null,
      });

      setPeriodForm({
        ...emptyPeriod,
        academic_year:
          activeYear ? String(activeYear.id) : "",
        kind:
          activeYear?.period_system === "SEMESTER"
            ? "SEMESTER"
            : "TRIMESTER",
      });

      await silentRefresh();
    } catch (err) {
      setError(apiError(err, t("curriculum.errors.save")));
    } finally {
      setSaving("");
    }
  };

  const bootstrapPeriods = async () => {
    if (!periodForm.academic_year && !activeYear) return;

    setSaving("bootstrap-periods");
    setError("");
    setMessage("");

    try {
      const yearId =
        Number(periodForm.academic_year) ||
        activeYear.id;

      const { data } = await api.post(
        "/academics/periods/bootstrap/",
        { academic_year: yearId }
      );

      setMessage(data.message);
      await silentRefresh();
    } catch (err) {
      setError(apiError(err, t("curriculum.errors.generatePeriods")));
    } finally {
      setSaving("");
    }
  };

  const createSubject = async (event) => {
    event.preventDefault();
    setSaving("subject");
    setError("");

    try {
      await api.post("/academics/subjects/", subjectForm);
      setSubjectForm(emptySubject);
      await silentRefresh();
    } catch (err) {
      setError(apiError(err, t("curriculum.errors.save")));
    } finally {
      setSaving("");
    }
  };

  const assignSubject = async (event) => {
    event.preventDefault();

    if (!assignmentForm.subject || !selectedLevelIds.length) {
      setError(t("curriculum.subjects.selectAtLeastOneLevel"));
      return;
    }

    setSaving("assignment");
    setError("");
    setMessage("");

    try {
      const { data } = await api.post(
        "/academics/level-subjects/bulk/",
        {
          subject: Number(assignmentForm.subject),
          levels: selectedLevelIds.map(Number),
          coefficient: Number(assignmentForm.coefficient),
          max_score_override:
            assignmentForm.max_score_override === ""
              ? null
              : Number(assignmentForm.max_score_override),
          teaching_language: assignmentForm.teaching_language,
          order: Number(assignmentForm.order),
          is_active: assignmentForm.is_active,
        }
      );

      setSelectedLevelIds([]);
      setMessage(
        t("curriculum.subjects.bulkAssigned", {
          created: data.created_count,
          updated: data.updated_count,
        })
      );

      await silentRefresh();
    } catch (err) {
      setError(apiError(err, t("curriculum.errors.assign")));
    } finally {
      setSaving("");
    }
  };

  const savePolicy = async (event) => {
    event.preventDefault();
    setSaving("policy");
    setError("");
    setMessage("");

    try {
      const { data } = await api.patch("/academics/policy/", {
        default_max_score: Number(policy.default_max_score),
        default_promotion_threshold: Number(
          policy.default_promotion_threshold
        ),
      });

      setPolicy(data);
      setMessage(t("curriculum.rules.saved"));
    } catch (err) {
      setError(apiError(err, t("curriculum.errors.save")));
    } finally {
      setSaving("");
    }
  };

  const saveCycleRule = async (
    cycle,
    field,
    value
  ) => {
    setSaving(`cycle-${cycle.id}`);
    setError("");

    try {
      await api.patch(
        `/academics/cycles/${cycle.id}/`,
        {
          [field]:
            value === "" ? null : Number(value),
        }
      );
      await silentRefresh();
    } catch (err) {
      setError(apiError(err, t("curriculum.errors.save")));
    } finally {
      setSaving("");
    }
  };

  const saveLevelRule = async (
    level,
    field,
    value
  ) => {
    setSaving(`level-${level.id}`);
    setError("");

    try {
      await api.patch(
        `/academics/levels/${level.id}/`,
        {
          [field]:
            value === "" ? null : Number(value),
        }
      );
      await silentRefresh();
    } catch (err) {
      setError(apiError(err, t("curriculum.errors.save")));
    } finally {
      setSaving("");
    }
  };

  const remove = async (endpoint, label) => {
    if (!window.confirm(`${t("common.delete")}: ${label} ?`)) {
      return;
    }

    setError("");

    try {
      await api.delete(endpoint);
      await silentRefresh();
    } catch (err) {
      setError(apiError(err, t("curriculum.errors.delete")));
    }
  };

  if (initialLoading) {
    return (
      <div className="grid min-h-[260px] place-items-center rounded-3xl border border-slate-200 bg-white">
        <div className="inline-flex items-center gap-2 text-sm text-slate-500">
          <Loader2
            size={17}
            className="animate-spin"
          />
          {t("curriculum.loading")}
        </div>
      </div>
    );
  }

  const selectedYear =
    years.find(
      (year) =>
        String(year.id) ===
        String(periodForm.academic_year)
    ) || activeYear;

  return (
    <div className="space-y-5">
      <div className="flex flex-col justify-between gap-4 xl:flex-row xl:items-end">
        <div>
          <div className="text-xs font-medium uppercase tracking-[0.18em] text-slate-400">
            {t("curriculum.step")}
          </div>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight">
            {t("curriculum.title")}
          </h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">
            {t("curriculum.description")}
          </p>
        </div>

        {backgroundLoading && (
          <div className="inline-flex items-center gap-2 text-xs text-slate-400">
            <RefreshCw
              size={13}
              className="animate-spin"
            />
            {t("curriculum.syncing")}
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
        {[
          ["periods", t("curriculum.tabs.periods"), BookMarked],
          ["subjects", t("curriculum.tabs.subjects"), Sigma],
          ["rules", t("curriculum.tabs.rules"), Gauge],
        ].map(([id, label, Icon]) => (
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

      {tab === "periods" && (
        <div className="grid gap-5 xl:grid-cols-[.8fr_1.2fr]">
          {canManage && (
            <form
              onSubmit={createPeriod}
              className="rounded-3xl border border-slate-200 bg-white p-6"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h2 className="font-semibold">
                    {t("curriculum.periods.create")}
                  </h2>
                  <p className="mt-1 text-xs leading-5 text-slate-500">
                    {t("curriculum.periods.help")}
                  </p>
                </div>
              </div>

              <div className="mt-5 space-y-4">
                <Field label={t("curriculum.periods.year")}>
                  <select
                    required
                    className={inputClass}
                    value={periodForm.academic_year}
                    onChange={(e) =>
                      setPeriodForm((form) => ({
                        ...form,
                        academic_year: e.target.value,
                      }))
                    }
                  >
                    <option value="">
                      {t("common.choose")}
                    </option>
                    {years.map((year) => (
                      <option
                        key={year.id}
                        value={year.id}
                      >
                        {year.name}
                        {year.is_active
                          ? ` — ${t("common.active")}`
                          : ""}
                      </option>
                    ))}
                  </select>
                </Field>

                <button
                  type="button"
                  onClick={bootstrapPeriods}
                  disabled={
                    !selectedYear ||
                    saving === "bootstrap-periods"
                  }
                  className="inline-flex w-full items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-40"
                >
                  {saving === "bootstrap-periods" ? (
                    <Loader2
                      size={16}
                      className="animate-spin"
                    />
                  ) : (
                    <RefreshCw size={16} />
                  )}
                  {t("curriculum.periods.generate")}
                </button>

                <div className="border-t border-slate-100 pt-4">
                  <div className="mb-3 text-xs font-semibold uppercase tracking-[0.15em] text-slate-400">
                    {t("curriculum.periods.manual")}
                  </div>

                  <div className="space-y-4">
                    <Field label={t("curriculum.periods.name")}>
                      <input
                        required
                        className={inputClass}
                        value={periodForm.name}
                        onChange={(e) =>
                          setPeriodForm((form) => ({
                            ...form,
                            name: e.target.value,
                            code:
                              form.code ||
                              slugify(e.target.value),
                          }))
                        }
                      />
                    </Field>

                    <Field label={t("curriculum.periods.code")}>
                      <input
                        required
                        className={inputClass}
                        value={periodForm.code}
                        onChange={(e) =>
                          setPeriodForm((form) => ({
                            ...form,
                            code: slugify(e.target.value),
                          }))
                        }
                      />
                    </Field>

                    <div className="grid gap-4 sm:grid-cols-2">
                      <Field label={t("curriculum.periods.type")}>
                        <select
                          className={inputClass}
                          value={periodForm.kind}
                          onChange={(e) =>
                            setPeriodForm((form) => ({
                              ...form,
                              kind: e.target.value,
                            }))
                          }
                        >
                          <option value="TRIMESTER">
                            {t("curriculum.periods.trimester")}
                          </option>
                          <option value="SEMESTER">
                            {t("curriculum.periods.semester")}
                          </option>
                          <option value="CUSTOM">
                            {t("curriculum.periods.custom")}
                          </option>
                        </select>
                      </Field>

                      <Field label={t("curriculum.periods.weight")}>
                        <input
                          required
                          min="0.001"
                          step="0.001"
                          type="number"
                          className={inputClass}
                          value={periodForm.weight}
                          onChange={(e) =>
                            setPeriodForm((form) => ({
                              ...form,
                              weight: e.target.value,
                            }))
                          }
                        />
                      </Field>
                    </div>

                    <div className="grid gap-4 sm:grid-cols-2">
                      <Field
                        label={t("curriculum.periods.start")}
                        hint={t("common.optional")}
                      >
                        <input
                          type="date"
                          className={inputClass}
                          value={periodForm.start_date}
                          onChange={(e) =>
                            setPeriodForm((form) => ({
                              ...form,
                              start_date: e.target.value,
                            }))
                          }
                        />
                      </Field>

                      <Field
                        label={t("curriculum.periods.end")}
                        hint={t("common.optional")}
                      >
                        <input
                          type="date"
                          className={inputClass}
                          value={periodForm.end_date}
                          onChange={(e) =>
                            setPeriodForm((form) => ({
                              ...form,
                              end_date: e.target.value,
                            }))
                          }
                        />
                      </Field>
                    </div>

                    <button
                      className={`${primaryButton} w-full`}
                      disabled={saving === "period"}
                    >
                      <Plus size={16} />
                      {t("curriculum.periods.add")}
                    </button>
                  </div>
                </div>
              </div>
            </form>
          )}

          <section className="rounded-3xl border border-slate-200 bg-white p-6">
            <h2 className="font-semibold">
              {t("curriculum.periods.configured")}
            </h2>

            <div className="mt-5 space-y-3">
              {!periods.length && (
                <EmptyState>
                  {t("curriculum.periods.empty")}
                </EmptyState>
              )}

              {periods.map((period) => (
                <div
                  key={period.id}
                  className="flex flex-col gap-3 rounded-2xl border border-slate-200 p-4 sm:flex-row sm:items-center"
                >
                  <div className="min-w-0 flex-1">
                    <div className="font-medium">
                      {period.name}
                    </div>
                    <div className="mt-1 text-xs text-slate-500">
                      {period.academic_year_name} •{" "}
                      {period.kind} •{" "}
                      {t("curriculum.periods.weightShort")}:{" "}
                      {period.weight}
                    </div>
                  </div>

                  {canManage && (
                    <button
                      type="button"
                      onClick={() =>
                        remove(
                          `/academics/periods/${period.id}/`,
                          period.name
                        )
                      }
                      className="grid h-9 w-9 place-items-center rounded-xl text-slate-400 hover:bg-rose-50 hover:text-rose-600"
                    >
                      <Trash2 size={16} />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </section>
        </div>
      )}

      {tab === "subjects" && (
        <div className="space-y-5">
          {canManage && (
            <div className="grid gap-5 xl:grid-cols-2">
              <form
                onSubmit={createSubject}
                className="rounded-3xl border border-slate-200 bg-white p-6"
              >
                <h2 className="font-semibold">
                  {t("curriculum.subjects.catalogTitle")}
                </h2>
                <p className="mt-1 text-xs leading-5 text-slate-500">
                  {t("curriculum.subjects.catalogHelp")}
                </p>

                <div className="mt-5 grid gap-4 sm:grid-cols-2">
                  <Field label={t("curriculum.subjects.name")}>
                    <input
                      required
                      className={inputClass}
                      value={subjectForm.name}
                      onChange={(e) =>
                        setSubjectForm((form) => ({
                          ...form,
                          name: e.target.value,
                          code:
                            form.code ||
                            slugify(e.target.value),
                        }))
                      }
                    />
                  </Field>

                  <Field label={t("curriculum.subjects.code")}>
                    <input
                      required
                      className={inputClass}
                      value={subjectForm.code}
                      onChange={(e) =>
                        setSubjectForm((form) => ({
                          ...form,
                          code: slugify(e.target.value),
                        }))
                      }
                    />
                  </Field>

                  <Field
                    label={t("curriculum.subjects.category")}
                    hint={t("common.optional")}
                  >
                    <input
                      className={inputClass}
                      value={subjectForm.category}
                      onChange={(e) =>
                        setSubjectForm((form) => ({
                          ...form,
                          category: e.target.value,
                        }))
                      }
                      placeholder="Sciences"
                    />
                  </Field>

                  <Field
                    label={t("curriculum.subjects.defaultLanguage")}
                  >
                    <select
                      className={inputClass}
                      value={
                        subjectForm.default_teaching_language
                      }
                      onChange={(e) =>
                        setSubjectForm((form) => ({
                          ...form,
                          default_teaching_language:
                            e.target.value,
                        }))
                      }
                    >
                      <option value="DEFAULT">
                        {t("curriculum.languages.section")}
                      </option>
                      <option value="FRENCH">
                        {t("common.french")}
                      </option>
                      <option value="ENGLISH">
                        {t("common.english")}
                      </option>
                      <option value="BILINGUAL">
                        {t("curriculum.languages.bilingual")}
                      </option>
                    </select>
                  </Field>

                  <div className="sm:col-span-2">
                    <button
                      className={`${primaryButton} w-full`}
                      disabled={saving === "subject"}
                    >
                      <Plus size={16} />
                      {t("curriculum.subjects.add")}
                    </button>
                  </div>
                </div>
              </form>

              <form
                onSubmit={assignSubject}
                className="rounded-3xl border border-slate-200 bg-white p-6"
              >
                <h2 className="font-semibold">
                  {t("curriculum.subjects.assignTitle")}
                </h2>
                <p className="mt-1 text-xs leading-5 text-slate-500">
                  {t("curriculum.subjects.assignHelp")}
                </p>

                <div className="mt-5 grid gap-4 sm:grid-cols-2">
                  <div className="sm:col-span-2">
                    <Field label={t("curriculum.subjects.subject")}>
                      <select
                        required
                        className={inputClass}
                        value={assignmentForm.subject}
                        onChange={(e) =>
                          setAssignmentForm((form) => ({
                            ...form,
                            subject: e.target.value,
                          }))
                        }
                      >
                        <option value="">
                          {t("common.choose")}
                        </option>
                        {subjects.map((subject) => (
                          <option
                            key={subject.id}
                            value={subject.id}
                          >
                            {subject.name}
                          </option>
                        ))}
                      </select>
                    </Field>
                  </div>

                  <div className="sm:col-span-2">
                    <LevelCheckboxSelector
                      levels={levels}
                      assignments={assignments}
                      subjectId={assignmentForm.subject}
                      value={selectedLevelIds}
                      onChange={setSelectedLevelIds}
                      t={t}
                    />
                  </div>

                  <Field label={t("curriculum.subjects.coefficient")}>
                    <input
                      required
                      min="0.001"
                      step="0.001"
                      type="number"
                      className={inputClass}
                      value={assignmentForm.coefficient}
                      onChange={(e) =>
                        setAssignmentForm((form) => ({
                          ...form,
                          coefficient: e.target.value,
                        }))
                      }
                    />
                  </Field>

                  <Field
                    label={t("curriculum.subjects.maxScore")}
                    hint={t("curriculum.rules.inherit")}
                  >
                    <input
                      min="0.01"
                      step="0.01"
                      type="number"
                      className={inputClass}
                      value={
                        assignmentForm.max_score_override
                      }
                      onChange={(e) =>
                        setAssignmentForm((form) => ({
                          ...form,
                          max_score_override:
                            e.target.value,
                        }))
                      }
                      placeholder={policy.default_max_score}
                    />
                  </Field>

                  <div className="sm:col-span-2">
                    <Field
                      label={t("curriculum.subjects.language")}
                    >
                      <select
                        className={inputClass}
                        value={
                          assignmentForm.teaching_language
                        }
                        onChange={(e) =>
                          setAssignmentForm((form) => ({
                            ...form,
                            teaching_language:
                              e.target.value,
                          }))
                        }
                      >
                        <option value="DEFAULT">
                          {t("curriculum.languages.section")}
                        </option>
                        <option value="FRENCH">
                          {t("common.french")}
                        </option>
                        <option value="ENGLISH">
                          {t("common.english")}
                        </option>
                        <option value="BILINGUAL">
                          {t("curriculum.languages.bilingual")}
                        </option>
                      </select>
                    </Field>
                  </div>

                  <div className="sm:col-span-2">
                    <button
                      className={`${primaryButton} w-full`}
                      disabled={
                        saving === "assignment" ||
                        !subjects.length ||
                        !levels.length ||
                        !selectedLevelIds.length
                      }
                    >
                      <Plus size={16} />
                      {t("curriculum.subjects.assign")}
                    </button>
                  </div>
                </div>
              </form>
            </div>
          )}

          <section className="rounded-3xl border border-slate-200 bg-white p-6">
            <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
              <div>
                <h2 className="font-semibold">
                  {t("curriculum.subjects.programTitle")}
                </h2>
                <p className="mt-1 text-xs text-slate-500">
                  {t("curriculum.subjects.programHelp")}
                </p>
              </div>

              <div className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                {assignments.length}
              </div>
            </div>

            <div className="mt-5 space-y-3">
              {!assignments.length && (
                <EmptyState>
                  {t("curriculum.subjects.emptyAssignments")}
                </EmptyState>
              )}

              {assignments.map((assignment) => (
                <div
                  key={assignment.id}
                  className="flex flex-col gap-3 rounded-2xl border border-slate-200 p-4 md:flex-row md:items-center"
                >
                  <div className="min-w-0 flex-1">
                    <div className="font-medium">
                      {assignment.subject_name}
                    </div>
                    <div className="mt-1 text-xs text-slate-500">
                      {assignment.section_name} •{" "}
                      {assignment.cycle_name} •{" "}
                      {assignment.level_name}
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center gap-2 text-xs">
                    <span className="rounded-lg bg-slate-100 px-2.5 py-1.5">
                      {t("curriculum.subjects.coefficientShort")}{" "}
                      {assignment.coefficient}
                    </span>
                    <span className="rounded-lg bg-slate-100 px-2.5 py-1.5">
                      / {assignment.effective_max_score}
                    </span>
                  </div>

                  {canManage && (
                    <div className="flex items-center gap-1">
                      <button
                        type="button"
                        onClick={() => setEditingAssignment(assignment)}
                        className="grid h-9 w-9 place-items-center rounded-xl text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                        title={t("curriculum.subjects.editAssignmentTitle")}
                      >
                        <Pencil size={15} />
                      </button>
                      <button
                        type="button"
                        onClick={() =>
                          remove(
                            `/academics/level-subjects/${assignment.id}/`,
                            `${assignment.subject_name} — ${assignment.level_name}`
                          )
                        }
                        className="grid h-9 w-9 place-items-center rounded-xl text-slate-400 hover:bg-rose-50 hover:text-rose-600"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-3xl border border-slate-200 bg-white p-6">
            <h2 className="font-semibold">
              {t("curriculum.subjects.catalogConfigured")}
            </h2>
            <div className="mt-4 flex flex-wrap gap-2">
              {!subjects.length && (
                <span className="text-sm text-slate-500">
                  {t("curriculum.subjects.emptyCatalog")}
                </span>
              )}

              {subjects.map((subject) => (
                <div
                  key={subject.id}
                  className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm"
                >
                  <span>{subject.name}</span>
                  {canManage && (
                    <div className="flex items-center gap-1">
                      <button
                        type="button"
                        onClick={() => setEditingSubject(subject)}
                        className="grid h-7 w-7 place-items-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                        title={t("curriculum.subjects.editTitle")}
                      >
                        <Pencil size={13} />
                      </button>
                      <button
                        type="button"
                        onClick={() =>
                          remove(
                            `/academics/subjects/${subject.id}/`,
                            subject.name
                          )
                        }
                        className="grid h-7 w-7 place-items-center rounded-lg text-slate-400 hover:bg-rose-50 hover:text-rose-600"
                        title={t("common.delete")}
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>
        </div>
      )}

      {tab === "rules" && (
        <div className="space-y-5">
          <form
            onSubmit={savePolicy}
            className="rounded-3xl border border-slate-200 bg-white p-6"
          >
            <div>
              <h2 className="font-semibold">
                {t("curriculum.rules.schoolTitle")}
              </h2>
              <p className="mt-1 max-w-3xl text-xs leading-5 text-slate-500">
                {t("curriculum.rules.schoolHelp")}
              </p>
            </div>

            <div className="mt-5 grid gap-5 sm:grid-cols-2">
              <Field label={t("curriculum.rules.maxScore")}>
                <input
                  disabled={!canManage}
                  required
                  min="0.01"
                  step="0.01"
                  type="number"
                  className={inputClass}
                  value={policy.default_max_score}
                  onChange={(e) =>
                    setPolicy((current) => ({
                      ...current,
                      default_max_score: e.target.value,
                    }))
                  }
                />
              </Field>

              <Field
                label={t("curriculum.rules.promotionThreshold")}
              >
                <input
                  disabled={!canManage}
                  required
                  min="0"
                  step="0.01"
                  type="number"
                  className={inputClass}
                  value={
                    policy.default_promotion_threshold
                  }
                  onChange={(e) =>
                    setPolicy((current) => ({
                      ...current,
                      default_promotion_threshold:
                        e.target.value,
                    }))
                  }
                />
              </Field>
            </div>

            {canManage && (
              <div className="mt-5 flex justify-end">
                <button
                  disabled={saving === "policy"}
                  className={primaryButton}
                >
                  <Check size={16} />
                  {t("common.save")}
                </button>
              </div>
            )}
          </form>

          <section className="rounded-3xl border border-slate-200 bg-white p-6">
            <div>
              <h2 className="font-semibold">
                {t("curriculum.rules.cycleTitle")}
              </h2>
              <p className="mt-1 max-w-3xl text-xs leading-5 text-slate-500">
                {t("curriculum.rules.cycleHelp")}
              </p>
            </div>

            <div className="mt-5 space-y-3">
              {!cycles.length && (
                <EmptyState>
                  {t("curriculum.rules.noCycles")}
                </EmptyState>
              )}

              {cycles.map((cycle) => (
                <CycleRuleRow
                  key={cycle.id}
                  cycle={cycle}
                  canManage={canManage}
                  saving={saving === `cycle-${cycle.id}`}
                  onSave={saveCycleRule}
                  t={t}
                />
              ))}
            </div>
          </section>

          <section className="rounded-3xl border border-slate-200 bg-white p-6">
            <div>
              <h2 className="font-semibold">
                {t("curriculum.rules.levelTitle")}
              </h2>
              <p className="mt-1 max-w-3xl text-xs leading-5 text-slate-500">
                {t("curriculum.rules.levelHelp")}
              </p>
            </div>

            <div className="mt-5 space-y-3">
              {!levels.length && (
                <EmptyState>
                  {t("curriculum.rules.noLevels")}
                </EmptyState>
              )}

              {levels.map((level) => (
                <LevelRuleRow
                  key={level.id}
                  level={level}
                  canManage={canManage}
                  saving={
                    saving === `level-${level.id}`
                  }
                  onSave={saveLevelRule}
                  t={t}
                />
              ))}
            </div>
          </section>
        </div>
      )}

      <SubjectEditDialog
        subject={editingSubject}
        open={Boolean(editingSubject)}
        onClose={() => setEditingSubject(null)}
        onSaved={async () => {
          await silentRefresh();
        }}
      />

      <AssignmentEditDialog
        assignment={editingAssignment}
        open={Boolean(editingAssignment)}
        onClose={() => setEditingAssignment(null)}
        onSaved={async () => {
          await silentRefresh();
        }}
      />
    </div>
  );
}

function CycleRuleRow({
  cycle,
  canManage,
  saving,
  onSave,
  t,
}) {
  const [threshold, setThreshold] = useState(
    cycle.promotion_threshold_override ?? ""
  );
  const [maxScore, setMaxScore] = useState(
    cycle.max_score_override ?? ""
  );

  useEffect(() => {
    setThreshold(cycle.promotion_threshold_override ?? "");
    setMaxScore(cycle.max_score_override ?? "");
  }, [
    cycle.promotion_threshold_override,
    cycle.max_score_override,
  ]);

  return (
    <div className="grid gap-4 rounded-2xl border border-slate-200 p-4 lg:grid-cols-[1fr_170px_170px] lg:items-end">
      <div>
        <div className="font-medium">{cycle.name}</div>
        <div className="mt-1 text-xs text-slate-500">
          {cycle.section_name}
        </div>
        <div className="mt-2 text-xs text-slate-400">
          {t("curriculum.rules.effective")}: {" "}
          {cycle.effective_promotion_threshold} / {" "}
          {cycle.effective_max_score}
        </div>
      </div>

      <Field
        label={t("curriculum.rules.cycleThreshold")}
        hint={t("curriculum.rules.inherit")}
      >
        <input
          disabled={!canManage || saving}
          type="number"
          min="0"
          step="0.01"
          className={inputClass}
          value={threshold}
          placeholder={String(cycle.effective_promotion_threshold)}
          onChange={(e) => setThreshold(e.target.value)}
          onBlur={() =>
            canManage &&
            String(cycle.promotion_threshold_override ?? "") !== String(threshold) &&
            onSave(cycle, "promotion_threshold_override", threshold)
          }
        />
      </Field>

      <Field
        label={t("curriculum.rules.cycleMaxScore")}
        hint={t("curriculum.rules.inherit")}
      >
        <input
          disabled={!canManage || saving}
          type="number"
          min="0.01"
          step="0.01"
          className={inputClass}
          value={maxScore}
          placeholder={String(cycle.effective_max_score)}
          onChange={(e) => setMaxScore(e.target.value)}
          onBlur={() =>
            canManage &&
            String(cycle.max_score_override ?? "") !== String(maxScore) &&
            onSave(cycle, "max_score_override", maxScore)
          }
        />
      </Field>
    </div>
  );
}

function LevelRuleRow({
  level,
  canManage,
  saving,
  onSave,
  t,
}) {
  const [threshold, setThreshold] = useState(
    level.promotion_threshold_override ?? ""
  );
  const [maxScore, setMaxScore] = useState(
    level.max_score_override ?? ""
  );

  useEffect(() => {
    setThreshold(
      level.promotion_threshold_override ?? ""
    );
    setMaxScore(level.max_score_override ?? "");
  }, [
    level.promotion_threshold_override,
    level.max_score_override,
  ]);

  return (
    <div className="grid gap-4 rounded-2xl border border-slate-200 p-4 lg:grid-cols-[1fr_170px_170px] lg:items-end">
      <div>
        <div className="font-medium">{level.name}</div>
        <div className="mt-1 text-xs text-slate-500">
          {level.section_name} • {level.cycle_name}
        </div>
        <div className="mt-2 text-xs text-slate-400">
          {t("curriculum.rules.effective")}:{" "}
          {level.effective_promotion_threshold} /{" "}
          {level.effective_max_score}
        </div>
      </div>

      <Field
        label={t("curriculum.rules.levelThreshold")}
        hint={t("curriculum.rules.inherit")}
      >
        <input
          disabled={!canManage || saving}
          type="number"
          min="0"
          step="0.01"
          className={inputClass}
          value={threshold}
          placeholder={String(
            level.effective_promotion_threshold
          )}
          onChange={(e) =>
            setThreshold(e.target.value)
          }
          onBlur={() =>
            canManage &&
            String(
              level.promotion_threshold_override ?? ""
            ) !== String(threshold) &&
            onSave(
              level,
              "promotion_threshold_override",
              threshold
            )
          }
        />
      </Field>

      <Field
        label={t("curriculum.rules.levelMaxScore")}
        hint={t("curriculum.rules.inherit")}
      >
        <input
          disabled={!canManage || saving}
          type="number"
          min="0.01"
          step="0.01"
          className={inputClass}
          value={maxScore}
          placeholder={String(
            level.effective_max_score
          )}
          onChange={(e) =>
            setMaxScore(e.target.value)
          }
          onBlur={() =>
            canManage &&
            String(
              level.max_score_override ?? ""
            ) !== String(maxScore) &&
            onSave(
              level,
              "max_score_override",
              maxScore
            )
          }
        />
      </Field>
    </div>
  );
}
