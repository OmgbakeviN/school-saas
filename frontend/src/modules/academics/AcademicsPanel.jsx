import { useEffect, useMemo, useState } from "react";
import {
  BookOpen,
  Check,
  ChevronDown,
  Layers3,
  Loader2,
  Plus,
  School,
  Sparkles,
  Trash2,
} from "lucide-react";
import Field from "../../components/Field";
import api from "../../services/api";
import { useI18n } from "../../i18n";

const inputClass =
  "w-full rounded-xl border border-slate-200 bg-white px-3.5 py-3 text-sm outline-none focus:border-slate-400 focus:ring-4 focus:ring-slate-100 disabled:bg-slate-50 disabled:text-slate-400";

const buttonClass =
  "inline-flex items-center justify-center gap-2 rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-medium text-white disabled:opacity-40";

const emptyYear = {
  name: "",
  start_date: "",
  end_date: "",
  period_system: "TRIMESTER",
  is_active: true,
  is_closed: false,
};

const emptySection = {
  name: "",
  code: "",
  language: "FRENCH",
  order: 0,
  is_active: true,
};

const emptyCycle = {
  section: "",
  name: "",
  code: "",
  kind: "SECONDARY",
  order: 0,
  is_active: true,
};

const emptyLevel = {
  cycle: "",
  name: "",
  code: "",
  order: 0,
  is_active: true,
};

const emptyClassroom = {
  academic_year: "",
  level: "",
  name: "",
  code: "",
  capacity: "",
  order: 0,
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

function EmptyState({ text }) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-6 text-center text-sm text-slate-500">
      {text}
    </div>
  );
}

export default function AcademicsPanel({ canManage, onCountsChanged }) {
  const { t } = useI18n();
  const [tab, setTab] = useState("years");
  const [years, setYears] = useState([]);
  const [sections, setSections] = useState([]);
  const [cycles, setCycles] = useState([]);
  const [levels, setLevels] = useState([]);
  const [classrooms, setClassrooms] = useState([]);

  const [yearForm, setYearForm] = useState(emptyYear);
  const [sectionForm, setSectionForm] = useState(emptySection);
  const [cycleForm, setCycleForm] = useState(emptyCycle);
  const [levelForm, setLevelForm] = useState(emptyLevel);
  const [classroomForm, setClassroomForm] = useState(emptyClassroom);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const activeYear = useMemo(
    () => years.find((year) => year.is_active) || years[0] || null,
    [years]
  );

  const load = async ({ showLoader = false } = {}) => {
    if (showLoader) {
      setLoading(true);
    }
    setError("");

    try {
      const [yearsRes, sectionsRes, cyclesRes, levelsRes, classroomsRes] =
        await Promise.all([
          api.get("/academics/years/"),
          api.get("/academics/sections/"),
          api.get("/academics/cycles/"),
          api.get("/academics/levels/"),
          api.get("/academics/classrooms/"),
        ]);

      setYears(yearsRes.data);
      setSections(sectionsRes.data);
      setCycles(cyclesRes.data);
      setLevels(levelsRes.data);
      setClassrooms(classroomsRes.data);

      if (!cycleForm.section && sectionsRes.data[0]) {
        setCycleForm((form) => ({ ...form, section: String(sectionsRes.data[0].id) }));
      }
      if (!levelForm.cycle && cyclesRes.data[0]) {
        setLevelForm((form) => ({ ...form, cycle: String(cyclesRes.data[0].id) }));
      }
      if (classroomsRes.data || yearsRes.data.length || levelsRes.data.length) {
        setClassroomForm((form) => ({
          ...form,
          academic_year: form.academic_year || String(yearsRes.data.find((y) => y.is_active)?.id || yearsRes.data[0]?.id || ""),
          level: form.level || String(levelsRes.data[0]?.id || ""),
        }));
      }

      onCountsChanged?.({
        academic_years: yearsRes.data.length,
        classes: classroomsRes.data.length,
      });
    } catch (err) {
      setError(err?.response?.data?.detail || t("academics.errors.load"));
    } finally {
      if (showLoader) {
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    load({ showLoader: true });
  }, []);

  const post = async (endpoint, payload, after) => {
    setSaving(endpoint);
    setError("");
    setMessage("");

    try {
      await api.post(endpoint, payload);
      await load();
      after?.();
    } catch (err) {
      const payload = err?.response?.data;
      const first = payload && Object.values(payload)[0];
      const text = Array.isArray(first)
        ? first[0]
        : typeof first === "object" && first
        ? Object.values(first)?.[0]?.[0]
        : payload?.detail || t("academics.errors.save");
      setError(String(text));
    } finally {
      setSaving("");
    }
  };

  const remove = async (endpoint, label) => {
    if (!window.confirm(`${t("common.delete")}: ${label} ?`)) return;

    setError("");
    try {
      await api.delete(endpoint);
      await load();
    } catch (err) {
      setError(err?.response?.data?.detail || t("academics.errors.remove"));
    }
  };

  const bootstrap = async () => {
    setSaving("bootstrap");
    setError("");
    setMessage("");

    try {
      const { data } = await api.post("/academics/bootstrap/");
      setMessage(data.message);
      await load();
    } catch (err) {
      setError(err?.response?.data?.detail || t("academics.errors.generate"));
    } finally {
      setSaving("");
    }
  };

  const createYear = (event) => {
    event.preventDefault();
    post("/academics/years/", yearForm, () => setYearForm(emptyYear));
  };

  const createSection = (event) => {
    event.preventDefault();
    post("/academics/sections/", sectionForm, () => setSectionForm(emptySection));
  };

  const createCycle = (event) => {
    event.preventDefault();
    post(
      "/academics/cycles/",
      { ...cycleForm, section: Number(cycleForm.section) },
      () => setCycleForm({ ...emptyCycle, section: sections[0] ? String(sections[0].id) : "" })
    );
  };

  const createLevel = (event) => {
    event.preventDefault();
    post(
      "/academics/levels/",
      { ...levelForm, cycle: Number(levelForm.cycle) },
      () => setLevelForm({ ...emptyLevel, cycle: cycles[0] ? String(cycles[0].id) : "" })
    );
  };

  const createClassroom = (event) => {
    event.preventDefault();
    post(
      "/academics/classrooms/",
      {
        ...classroomForm,
        academic_year: Number(classroomForm.academic_year),
        level: Number(classroomForm.level),
        capacity: classroomForm.capacity ? Number(classroomForm.capacity) : null,
      },
      () =>
        setClassroomForm({
          ...emptyClassroom,
          academic_year: activeYear ? String(activeYear.id) : "",
          level: levels[0] ? String(levels[0].id) : "",
        })
    );
  };

  if (loading) {
    return (
      <div className="grid min-h-[300px] place-items-center rounded-3xl border border-slate-200 bg-white">
        <div className="inline-flex items-center gap-2 text-sm text-slate-500">
          <Loader2 size={17} className="animate-spin" />
          {t("academics.loading")}
        </div>
      </div>
    );
  }

  const hierarchy = sections.map((section) => ({
    ...section,
    cycles: cycles
      .filter((cycle) => cycle.section === section.id)
      .map((cycle) => ({
        ...cycle,
        levels: levels.filter((level) => level.cycle === cycle.id),
      })),
  }));

  return (
    <div className="space-y-5">
      <div className="flex flex-col justify-between gap-4 xl:flex-row xl:items-end">
        <div>
          <div className="text-xs font-medium uppercase tracking-[0.18em] text-slate-400">
            {t("academics.step")}
          </div>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight">
            {t("academics.title")}
          </h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
            {t("academics.description")}
          </p>
        </div>

        {canManage && (
          <button
            onClick={bootstrap}
            disabled={saving === "bootstrap"}
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
          >
            {saving === "bootstrap" ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <Sparkles size={16} />
            )}
            {t("academics.generate")}
          </button>
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
          ["years", t("academics.tabs.years"), BookOpen],
          ["structure", t("academics.tabs.structure"), Layers3],
          ["classes", t("academics.tabs.classes"), School],
        ].map(([id, label, Icon]) => (
          <button
            key={id}
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

      {tab === "years" && (
        <div className="grid gap-5 xl:grid-cols-[.9fr_1.1fr]">
          {canManage && (
            <form onSubmit={createYear} className="rounded-3xl border border-slate-200 bg-white p-6">
              <h2 className="font-semibold">{t("academics.year.new")}</h2>

              <div className="mt-5 space-y-4">
                <Field label={t("academics.year.name")} hint={t("academics.year.example")}>
                  <input
                    required
                    className={inputClass}
                    value={yearForm.name}
                    onChange={(e) => setYearForm({ ...yearForm, name: e.target.value })}
                  />
                </Field>

                <div className="grid gap-4 sm:grid-cols-2">
                  <Field label={t("academics.year.start")}>
                    <input
                      required
                      type="date"
                      className={inputClass}
                      value={yearForm.start_date}
                      onChange={(e) => setYearForm({ ...yearForm, start_date: e.target.value })}
                    />
                  </Field>
                  <Field label={t("academics.year.end")}>
                    <input
                      required
                      type="date"
                      className={inputClass}
                      value={yearForm.end_date}
                      onChange={(e) => setYearForm({ ...yearForm, end_date: e.target.value })}
                    />
                  </Field>
                </div>

                <Field label={t("academics.year.system")}>
                  <select
                    className={inputClass}
                    value={yearForm.period_system}
                    onChange={(e) => setYearForm({ ...yearForm, period_system: e.target.value })}
                  >
                    <option value="TRIMESTER">{t("academics.year.trimesters")}</option>
                    <option value="SEMESTER">{t("academics.year.semesters")}</option>
                    <option value="CUSTOM">{t("academics.year.custom")}</option>
                  </select>
                </Field>

                <label className="flex items-center gap-3 rounded-xl border border-slate-200 p-3 text-sm">
                  <input
                    type="checkbox"
                    checked={yearForm.is_active}
                    onChange={(e) => setYearForm({ ...yearForm, is_active: e.target.checked })}
                  />
                  {t("academics.year.active")}
                </label>

                <button
                  disabled={saving === "/academics/years/"}
                  className={`${buttonClass} w-full`}
                >
                  <Plus size={16} />
                  {t("academics.year.create")}
                </button>
              </div>
            </form>
          )}

          <section className="rounded-3xl border border-slate-200 bg-white p-6">
            <h2 className="font-semibold">{t("academics.year.configured")}</h2>
            <div className="mt-5 space-y-3">
              {!years.length && <EmptyState text={t("academics.year.empty")} />}

              {years.map((year) => (
                <div
                  key={year.id}
                  className="flex flex-col gap-3 rounded-2xl border border-slate-200 p-4 sm:flex-row sm:items-center"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{year.name}</span>
                      {year.is_active && (
                        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700">
                          <Check size={11} />
                          {t("common.active")}
                        </span>
                      )}
                    </div>
                    <div className="mt-1 text-xs text-slate-500">
                      {year.start_date} → {year.end_date} • {year.period_system}
                    </div>
                  </div>
                  {canManage && (
                    <button
                      onClick={() => remove(`/academics/years/${year.id}/`, year.name)}
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

      {tab === "structure" && (
        <div className="space-y-5">
          {canManage && (
            <div className="grid gap-4 xl:grid-cols-3">
              <form onSubmit={createSection} className="rounded-3xl border border-slate-200 bg-white p-5">
                <h3 className="font-semibold">{t("academics.structure.addSection")}</h3>
                <div className="mt-4 space-y-3">
                  <Field label={t("academics.structure.name")}>
                    <input
                      required
                      className={inputClass}
                      value={sectionForm.name}
                      onChange={(e) =>
                        setSectionForm({
                          ...sectionForm,
                          name: e.target.value,
                          code: sectionForm.code || slugify(e.target.value),
                        })
                      }
                    />
                  </Field>
                  <Field label={t("academics.structure.code")}>
                    <input required className={inputClass} value={sectionForm.code} onChange={(e) => setSectionForm({ ...sectionForm, code: slugify(e.target.value) })} />
                  </Field>
                  <Field label={t("academics.structure.language")}>
                    <select className={inputClass} value={sectionForm.language} onChange={(e) => setSectionForm({ ...sectionForm, language: e.target.value })}>
                      <option value="FRENCH">{t("academics.structure.french")}</option>
                      <option value="ENGLISH">{t("academics.structure.english")}</option>
                      <option value="BILINGUAL">{t("academics.structure.bilingual")}</option>
                    </select>
                  </Field>
                  <button className={`${buttonClass} w-full`}>
                    <Plus size={16} />
                    {t("academics.structure.section")}
                  </button>
                </div>
              </form>

              <form onSubmit={createCycle} className="rounded-3xl border border-slate-200 bg-white p-5">
                <h3 className="font-semibold">{t("academics.structure.addCycle")}</h3>
                <div className="mt-4 space-y-3">
                  <Field label={t("academics.structure.section")}>
                    <select required className={inputClass} value={cycleForm.section} onChange={(e) => setCycleForm({ ...cycleForm, section: e.target.value })}>
                      <option value="">{t("common.choose")}</option>
                      {sections.map((section) => <option key={section.id} value={section.id}>{section.name}</option>)}
                    </select>
                  </Field>
                  <Field label={t("academics.structure.name")}>
                    <input
                      required
                      className={inputClass}
                      value={cycleForm.name}
                      onChange={(e) =>
                        setCycleForm({
                          ...cycleForm,
                          name: e.target.value,
                          code: cycleForm.code || slugify(e.target.value),
                        })
                      }
                    />
                  </Field>
                  <Field label={t("academics.structure.code")}>
                    <input required className={inputClass} value={cycleForm.code} onChange={(e) => setCycleForm({ ...cycleForm, code: slugify(e.target.value) })} />
                  </Field>
                  <Field label={t("academics.structure.type")}>
                    <select className={inputClass} value={cycleForm.kind} onChange={(e) => setCycleForm({ ...cycleForm, kind: e.target.value })}>
                      <option value="PRIMARY">{t("academics.structure.primary")}</option>
                      <option value="SECONDARY">{t("academics.structure.secondary")}</option>
                      <option value="OTHER">{t("academics.structure.other")}</option>
                    </select>
                  </Field>
                  <button className={`${buttonClass} w-full`}>
                    <Plus size={16} />
                    {t("academics.structure.cycle")}
                  </button>
                </div>
              </form>

              <form onSubmit={createLevel} className="rounded-3xl border border-slate-200 bg-white p-5">
                <h3 className="font-semibold">{t("academics.structure.addLevel")}</h3>
                <div className="mt-4 space-y-3">
                  <Field label={t("academics.structure.cycle")}>
                    <select required className={inputClass} value={levelForm.cycle} onChange={(e) => setLevelForm({ ...levelForm, cycle: e.target.value })}>
                      <option value="">{t("common.choose")}</option>
                      {cycles.map((cycle) => <option key={cycle.id} value={cycle.id}>{cycle.section_name} • {cycle.name}</option>)}
                    </select>
                  </Field>
                  <Field label={t("academics.structure.name")}>
                    <input
                      required
                      className={inputClass}
                      value={levelForm.name}
                      onChange={(e) =>
                        setLevelForm({
                          ...levelForm,
                          name: e.target.value,
                          code: levelForm.code || slugify(e.target.value),
                        })
                      }
                    />
                  </Field>
                  <Field label={t("academics.structure.code")}>
                    <input required className={inputClass} value={levelForm.code} onChange={(e) => setLevelForm({ ...levelForm, code: slugify(e.target.value) })} />
                  </Field>
                  <button className={`${buttonClass} w-full`}>
                    <Plus size={16} />
                    {t("academics.classroom.level")}
                  </button>
                </div>
              </form>
            </div>
          )}

          <section className="rounded-3xl border border-slate-200 bg-white p-6">
            <h2 className="font-semibold">{t("academics.structure.hierarchy")}</h2>
            <div className="mt-5 space-y-4">
              {!hierarchy.length && <EmptyState text={t("academics.structure.empty")} />}

              {hierarchy.map((section) => (
                <div key={section.id} className="overflow-hidden rounded-2xl border border-slate-200">
                  <div className="flex items-center justify-between bg-slate-50 px-4 py-3">
                    <div>
                      <div className="font-medium">{section.name}</div>
                      <div className="text-xs text-slate-500">{section.language} • {section.code}</div>
                    </div>
                    {canManage && (
                      <button onClick={() => remove(`/academics/sections/${section.id}/`, section.name)} className="grid h-8 w-8 place-items-center rounded-lg text-slate-400 hover:bg-rose-50 hover:text-rose-600">
                        <Trash2 size={15} />
                      </button>
                    )}
                  </div>

                  <div className="space-y-3 p-4">
                    {!section.cycles.length && <div className="text-sm text-slate-400">{t("academics.structure.noCycle")}</div>}
                    {section.cycles.map((cycle) => (
                      <div key={cycle.id} className="rounded-xl border border-slate-200 p-4">
                        <div className="flex items-center justify-between gap-4">
                          <div>
                            <div className="font-medium">{cycle.name}</div>
                            <div className="text-xs text-slate-500">{cycle.kind}</div>
                          </div>
                          {canManage && (
                            <button onClick={() => remove(`/academics/cycles/${cycle.id}/`, cycle.name)} className="grid h-8 w-8 place-items-center rounded-lg text-slate-400 hover:bg-rose-50 hover:text-rose-600">
                              <Trash2 size={15} />
                            </button>
                          )}
                        </div>

                        <div className="mt-3 flex flex-wrap gap-2">
                          {cycle.levels.map((level) => (
                            <div key={level.id} className="group inline-flex items-center gap-1.5 rounded-lg bg-slate-100 px-2.5 py-1.5 text-xs font-medium text-slate-700">
                              {level.name}
                              {canManage && (
                                <button onClick={() => remove(`/academics/levels/${level.id}/`, level.name)} className="text-slate-400 hover:text-rose-600">
                                  ×
                                </button>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      )}

      {tab === "classes" && (
        <div className="grid gap-5 xl:grid-cols-[.8fr_1.2fr]">
          {canManage && (
            <form onSubmit={createClassroom} className="rounded-3xl border border-slate-200 bg-white p-6">
              <h2 className="font-semibold">{t("academics.classroom.createTitle")}</h2>
              <p className="mt-1 text-xs leading-5 text-slate-500">
                {t("academics.classroom.help")}
              </p>

              <div className="mt-5 space-y-4">
                <Field label={t("academics.classroom.year")}>
                  <select required className={inputClass} value={classroomForm.academic_year} onChange={(e) => setClassroomForm({ ...classroomForm, academic_year: e.target.value })}>
                    <option value="">{t("common.choose")}</option>
                    {years.map((year) => <option key={year.id} value={year.id}>{year.name}{year.is_active ? " — active" : ""}</option>)}
                  </select>
                </Field>

                <Field label={t("academics.classroom.level")}>
                  <select required className={inputClass} value={classroomForm.level} onChange={(e) => setClassroomForm({ ...classroomForm, level: e.target.value })}>
                    <option value="">{t("common.choose")}</option>
                    {levels.map((level) => (
                      <option key={level.id} value={level.id}>
                        {level.section_name} • {level.cycle_name} • {level.name}
                      </option>
                    ))}
                  </select>
                </Field>

                <Field label={t("academics.structure.name")}>
                  <input
                    required
                    className={inputClass}
                    value={classroomForm.name}
                    onChange={(e) =>
                      setClassroomForm({
                        ...classroomForm,
                        name: e.target.value,
                        code: classroomForm.code || slugify(e.target.value),
                      })
                    }
                    placeholder="3e A"
                  />
                </Field>

                <Field label={t("academics.structure.code")}>
                  <input required className={inputClass} value={classroomForm.code} onChange={(e) => setClassroomForm({ ...classroomForm, code: slugify(e.target.value) })} />
                </Field>

                <Field label={t("academics.classroom.capacity")} hint={t("common.optional")}>
                  <input type="number" min="1" className={inputClass} value={classroomForm.capacity} onChange={(e) => setClassroomForm({ ...classroomForm, capacity: e.target.value })} />
                </Field>

                <button disabled={!years.length || !levels.length} className={`${buttonClass} w-full`}>
                  <Plus size={16} />
                  {t("academics.classroom.create")}
                </button>
              </div>
            </form>
          )}

          <section className="rounded-3xl border border-slate-200 bg-white p-6">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="font-semibold">{t("academics.classroom.configured")}</h2>
                <p className="mt-1 text-xs text-slate-500">
                  {activeYear ? t("academics.classroom.activeYear", { name: activeYear.name }) : t("academics.classroom.noActiveYear")}
                </p>
              </div>
              <div className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                {t("academics.classroom.count", { count: classrooms.length })}
              </div>
            </div>

            <div className="mt-5 space-y-3">
              {!classrooms.length && <EmptyState text={t("academics.classroom.empty")} />}

              {classrooms.map((classroom) => (
                <div key={classroom.id} className="flex flex-col gap-3 rounded-2xl border border-slate-200 p-4 sm:flex-row sm:items-center">
                  <div className="flex-1">
                    <div className="font-medium">{classroom.name}</div>
                    <div className="mt-1 text-xs text-slate-500">
                      {classroom.academic_year_name} • {classroom.section_name} • {classroom.level_name}
                      {classroom.capacity ? ` • capacité ${classroom.capacity}` : ""}
                    </div>
                  </div>
                  {canManage && (
                    <button onClick={() => remove(`/academics/classrooms/${classroom.id}/`, classroom.name)} className="grid h-9 w-9 place-items-center rounded-xl text-slate-400 hover:bg-rose-50 hover:text-rose-600">
                      <Trash2 size={16} />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
