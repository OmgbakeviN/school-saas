import { useEffect, useMemo, useState } from "react";
import {
  Edit3,
  LayoutTemplate,
  Loader2,
  Plus,
  Save,
  Star,
  Trash2,
} from "lucide-react";

import api from "../../services/api";


const inputClass =
  "w-full rounded-xl border border-slate-200 bg-white px-3.5 py-3 text-sm outline-none focus:border-slate-400 focus:ring-4 focus:ring-slate-100";

const templateChoices = [
  {
    key: "CLASSIC",
    labelKey: "classic",
    orientation: "A4 portrait",
  },
  {
    key: "MODERN",
    labelKey: "modern",
    orientation: "A4 portrait",
  },
  {
    key: "COMPACT",
    labelKey: "compact",
    orientation: "A4 portrait",
  },
  {
    key: "SECONDARY_LANDSCAPE",
    labelKey: "secondaryLandscape",
    orientation: "A4 paysage",
  },
];

const defaultForm = {
  id: null,
  name: "",
  cycle: "",
  template_key: "CLASSIC",
  language_mode: "AUTO",
  is_default: true,
  show_rank: true,
  show_class_average: true,
  show_effective: true,
  show_decision: true,
  show_subject_comments: true,
  show_teacher_comment: true,
  show_direction_comment: true,
  show_student_photo: false,
  show_qr: true,
  font_scale: "1.00",
};

function parseError(error, fallback) {
  return (
    error?.response?.data?.detail ||
    error?.response?.data?.name?.[0] ||
    error?.response?.data?.non_field_errors?.[0] ||
    fallback
  );
}

function Toggle({ checked, onChange, label, help }) {
  return (
    <label className="flex cursor-pointer items-start gap-3 rounded-2xl border border-slate-200 bg-white p-3">
      <input
        type="checkbox"
        checked={checked}
        onChange={(event) => onChange(event.target.checked)}
        className="mt-1 h-4 w-4 accent-[var(--school-primary)]"
      />
      <span>
        <span className="block text-sm font-medium">{label}</span>
        {help && (
          <span className="mt-0.5 block text-xs leading-5 text-slate-500">
            {help}
          </span>
        )}
      </span>
    </label>
  );
}

export default function ReportCardTemplatesPanel({
  cycles,
  t,
  onMessage,
  onError,
}) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState("");
  const [templates, setTemplates] = useState([]);
  const [form, setForm] = useState(defaultForm);

  const currentChoice = useMemo(
    () =>
      templateChoices.find(
        (item) => item.key === form.template_key
      ) || templateChoices[0],
    [form.template_key]
  );

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await api.get("/report-cards/templates/");
      setTemplates(data);
    } catch (error) {
      onError(
        parseError(error, t("reportCards.templates.errors.load"))
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const reset = () => {
    setForm({
      ...defaultForm,
      name: t("reportCards.templates.defaultName"),
    });
  };

  useEffect(() => {
    if (!form.name) {
      reset();
    }
  }, []);

  const save = async (event) => {
    event.preventDefault();
    setSaving("save");

    const payload = {
      name: form.name,
      cycle: form.cycle ? Number(form.cycle) : null,
      template_key: form.template_key,
      language_mode: form.language_mode,
      is_default: form.is_default,
      show_rank: form.show_rank,
      show_class_average: form.show_class_average,
      show_effective: form.show_effective,
      show_decision: form.show_decision,
      show_subject_comments: form.show_subject_comments,
      show_teacher_comment: form.show_teacher_comment,
      show_direction_comment: form.show_direction_comment,
      show_student_photo: form.show_student_photo,
      show_qr: form.show_qr,
      font_scale: form.font_scale,
    };

    try {
      if (form.id) {
        await api.patch(
          `/report-cards/templates/${form.id}/`,
          payload
        );
        onMessage(t("reportCards.templates.messages.updated"));
      } else {
        await api.post("/report-cards/templates/", payload);
        onMessage(t("reportCards.templates.messages.created"));
      }

      reset();
      await load();
    } catch (error) {
      onError(
        parseError(error, t("reportCards.templates.errors.save"))
      );
    } finally {
      setSaving("");
    }
  };

  const edit = (template) => {
    setForm({
      id: template.id,
      name: template.name,
      cycle: template.cycle ? String(template.cycle) : "",
      template_key: template.template_key,
      language_mode: template.language_mode || "AUTO",
      is_default: template.is_default,
      show_rank: template.show_rank,
      show_class_average: template.show_class_average,
      show_effective: template.show_effective,
      show_decision: template.show_decision,
      show_subject_comments: template.show_subject_comments,
      show_teacher_comment: template.show_teacher_comment,
      show_direction_comment: template.show_direction_comment,
      show_student_photo: Boolean(template.show_student_photo),
      show_qr: template.show_qr,
      font_scale: String(template.font_scale),
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const setDefault = async (template) => {
    setSaving(`default-${template.id}`);
    try {
      await api.post(
        `/report-cards/templates/${template.id}/set-default/`,
        { is_default: true }
      );
      onMessage(t("reportCards.templates.messages.defaultSet"));
      await load();
    } catch (error) {
      onError(
        parseError(
          error,
          t("reportCards.templates.errors.defaultSet")
        )
      );
    } finally {
      setSaving("");
    }
  };

  const remove = async (template) => {
    if (!window.confirm(t("reportCards.templates.deleteConfirm"))) {
      return;
    }

    setSaving(`delete-${template.id}`);
    try {
      await api.delete(
        `/report-cards/templates/${template.id}/`
      );
      if (form.id === template.id) {
        reset();
      }
      onMessage(t("reportCards.templates.messages.deleted"));
      await load();
    } catch (error) {
      onError(
        parseError(
          error,
          t("reportCards.templates.errors.delete")
        )
      );
    } finally {
      setSaving("");
    }
  };

  if (loading) {
    return (
      <div className="grid min-h-[240px] place-items-center rounded-3xl border border-slate-200 bg-white">
        <span className="inline-flex items-center gap-2 text-sm text-slate-500">
          <Loader2 size={17} className="animate-spin" />
          {t("reportCards.templates.loading")}
        </span>
      </div>
    );
  }

  return (
    <div className="grid gap-5 xl:grid-cols-[1.05fr_.95fr]">
      <form
        onSubmit={save}
        className="rounded-3xl border border-slate-200 bg-white p-5 sm:p-6"
      >
        <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
          <div>
            <div className="flex items-center gap-2">
              <LayoutTemplate size={18} className="text-slate-400" />
              <h2 className="font-semibold">
                {form.id
                  ? t("reportCards.templates.editTitle")
                  : t("reportCards.templates.createTitle")}
              </h2>
            </div>
            <p className="mt-1 text-xs leading-5 text-slate-500">
              {t("reportCards.templates.formHelp")}
            </p>
          </div>

          {form.id && (
            <button
              type="button"
              onClick={reset}
              className="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-xs font-medium hover:bg-slate-50"
            >
              <Plus size={14} />
              {t("reportCards.templates.new")}
            </button>
          )}
        </div>

        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          <label className="block sm:col-span-2">
            <span className="text-xs font-medium text-slate-500">
              {t("reportCards.templates.fields.name")}
            </span>
            <input
              required
              className={`${inputClass} mt-2`}
              value={form.name}
              onChange={(event) =>
                setForm({ ...form, name: event.target.value })
              }
            />
          </label>

          <label className="block">
            <span className="text-xs font-medium text-slate-500">
              {t("reportCards.templates.fields.scope")}
            </span>
            <select
              className={`${inputClass} mt-2`}
              value={form.cycle}
              onChange={(event) =>
                setForm({ ...form, cycle: event.target.value })
              }
            >
              <option value="">
                {t("reportCards.templates.allCycles")}
              </option>
              {cycles.map((cycle) => (
                <option key={cycle.id} value={cycle.id}>
                  {cycle.section_name} • {cycle.name}
                </option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="text-xs font-medium text-slate-500">
              {t("reportCards.templates.fields.language")}
            </span>
            <select
              className={`${inputClass} mt-2`}
              value={form.language_mode}
              onChange={(event) =>
                setForm({
                  ...form,
                  language_mode: event.target.value,
                })
              }
            >
              <option value="AUTO">
                {t("reportCards.templates.languages.auto")}
              </option>
              <option value="FRENCH">
                {t("reportCards.templates.languages.french")}
              </option>
              <option value="ENGLISH">
                {t("reportCards.templates.languages.english")}
              </option>
            </select>
            <span className="mt-1.5 block text-[11px] leading-4 text-slate-400">
              {t("reportCards.templates.languageHelp")}
            </span>
          </label>

          <label className="block">
            <span className="text-xs font-medium text-slate-500">
              {t("reportCards.templates.fields.fontScale")}
            </span>
            <select
              className={`${inputClass} mt-2`}
              value={form.font_scale}
              onChange={(event) =>
                setForm({
                  ...form,
                  font_scale: event.target.value,
                })
              }
            >
              <option value="1.10">110%</option>
              <option value="1.05">105%</option>
              <option value="1.00">100%</option>
              <option value="0.95">95%</option>
              <option value="0.90">90%</option>
              <option value="0.85">85%</option>
              <option value="0.80">80%</option>
            </select>
          </label>
        </div>

        <div className="mt-5">
          <div className="text-xs font-medium text-slate-500">
            {t("reportCards.templates.fields.layout")}
          </div>

          <div className="mt-2 grid gap-3 sm:grid-cols-2">
            {templateChoices.map((choice) => {
              const selected =
                form.template_key === choice.key;

              return (
                <button
                  key={choice.key}
                  type="button"
                  onClick={() =>
                    setForm({
                      ...form,
                      template_key: choice.key,
                    })
                  }
                  className={`rounded-2xl border p-4 text-left transition ${
                    selected
                      ? "shadow-sm"
                      : "border-slate-200 hover:bg-slate-50"
                  }`}
                  style={
                    selected
                      ? {
                          borderColor:
                            "var(--school-primary)",
                          background:
                            "rgb(var(--school-primary-rgb) / 0.08)",
                        }
                      : undefined
                  }
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium">
                      {t(
                        `reportCards.templates.choices.${choice.labelKey}.name`
                      )}
                    </span>
                    {selected && (
                      <span
                        className="h-2.5 w-2.5 rounded-full"
                        style={{
                          background:
                            "var(--school-primary)",
                        }}
                      />
                    )}
                  </div>
                  <div className="mt-1 text-xs text-slate-400">
                    {choice.orientation}
                  </div>
                  <div className="mt-2 text-xs leading-5 text-slate-500">
                    {t(
                      `reportCards.templates.choices.${choice.labelKey}.help`
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          <Toggle
            checked={form.show_rank}
            onChange={(value) =>
              setForm({ ...form, show_rank: value })
            }
            label={t("reportCards.templates.options.rank")}
          />
          <Toggle
            checked={form.show_class_average}
            onChange={(value) =>
              setForm({
                ...form,
                show_class_average: value,
              })
            }
            label={t(
              "reportCards.templates.options.classAverage"
            )}
          />
          <Toggle
            checked={form.show_effective}
            onChange={(value) =>
              setForm({ ...form, show_effective: value })
            }
            label={t("reportCards.templates.options.effective")}
          />
          <Toggle
            checked={form.show_decision}
            onChange={(value) =>
              setForm({ ...form, show_decision: value })
            }
            label={t("reportCards.templates.options.decision")}
          />
          <Toggle
            checked={form.show_subject_comments}
            onChange={(value) =>
              setForm({
                ...form,
                show_subject_comments: value,
              })
            }
            label={t(
              "reportCards.templates.options.subjectComments"
            )}
          />
          <Toggle
            checked={form.show_teacher_comment}
            onChange={(value) =>
              setForm({
                ...form,
                show_teacher_comment: value,
              })
            }
            label={t(
              "reportCards.templates.options.teacherComment"
            )}
          />
          <Toggle
            checked={form.show_direction_comment}
            onChange={(value) =>
              setForm({
                ...form,
                show_direction_comment: value,
              })
            }
            label={t(
              "reportCards.templates.options.directionComment"
            )}
          />
          <Toggle
            checked={form.show_student_photo}
            onChange={(value) =>
              setForm({ ...form, show_student_photo: value })
            }
            label={t("reportCards.templates.options.studentPhoto")}
          />
          <Toggle
            checked={form.show_qr}
            onChange={(value) =>
              setForm({ ...form, show_qr: value })
            }
            label={t("reportCards.templates.options.qr")}
          />
        </div>

        <label className="mt-4 flex items-center gap-3 rounded-2xl bg-slate-50 p-4">
          <input
            type="checkbox"
            checked={form.is_default}
            onChange={(event) =>
              setForm({
                ...form,
                is_default: event.target.checked,
              })
            }
            className="h-4 w-4 accent-[var(--school-primary)]"
          />
          <span>
            <span className="block text-sm font-medium">
              {t("reportCards.templates.fields.default")}
            </span>
            <span className="mt-0.5 block text-xs text-slate-500">
              {t("reportCards.templates.defaultHelp")}
            </span>
          </span>
        </label>

        <div className="mt-5 rounded-2xl border border-blue-100 bg-blue-50/60 p-4 text-xs leading-5 text-blue-800">
          {t("reportCards.templates.a4Rule", {
            orientation: currentChoice.orientation,
          })}
        </div>

        <div className="mt-5 flex justify-end">
          <button
            className="inline-flex items-center gap-2 rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-medium text-white disabled:opacity-40"
            disabled={saving === "save"}
          >
            {saving === "save" ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <Save size={16} />
            )}
            {t("common.save")}
          </button>
        </div>
      </form>

      <section className="rounded-3xl border border-slate-200 bg-white p-5 sm:p-6">
        <div>
          <h2 className="font-semibold">
            {t("reportCards.templates.listTitle")}
          </h2>
          <p className="mt-1 text-xs leading-5 text-slate-500">
            {t("reportCards.templates.listHelp")}
          </p>
        </div>

        <div className="mt-5 space-y-3">
          {!templates.length && (
            <div className="rounded-2xl bg-slate-50 p-8 text-center text-sm text-slate-500">
              {t("reportCards.templates.empty")}
            </div>
          )}

          {templates.map((template) => (
            <div
              key={template.id}
              className="rounded-2xl border border-slate-200 p-4"
            >
              <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-medium">
                      {template.name}
                    </span>
                    {template.is_default && (
                      <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-1 text-[10px] font-medium text-amber-700">
                        <Star size={10} />
                        {t("reportCards.templates.defaultBadge")}
                      </span>
                    )}
                  </div>
                  <div className="mt-1 text-xs text-slate-500">
                    {template.template_label} •{" "}
                    {template.orientation} •{" "}
                    {t(
                      `reportCards.templates.languages.${
                        template.language_mode === "ENGLISH"
                          ? "english"
                          : template.language_mode === "FRENCH"
                            ? "french"
                            : "auto"
                      }`
                    )} • v{template.version}
                  </div>
                  <div className="mt-1 text-xs text-slate-400">
                    {template.cycle_name ||
                      t("reportCards.templates.allCycles")}
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  {!template.is_default && (
                    <button
                      type="button"
                      onClick={() => setDefault(template)}
                      disabled={
                        saving === `default-${template.id}`
                      }
                      className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 px-3 py-2 text-xs font-medium hover:bg-slate-50"
                    >
                      <Star size={13} />
                      {t("reportCards.templates.setDefault")}
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => edit(template)}
                    className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 px-3 py-2 text-xs font-medium hover:bg-slate-50"
                  >
                    <Edit3 size={13} />
                    {t("common.edit")}
                  </button>
                  <button
                    type="button"
                    onClick={() => remove(template)}
                    disabled={
                      saving === `delete-${template.id}`
                    }
                    className="inline-flex items-center gap-1.5 rounded-xl border border-rose-200 px-3 py-2 text-xs font-medium text-rose-700 hover:bg-rose-50"
                  >
                    <Trash2 size={13} />
                    {t("common.delete")}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-5 rounded-2xl bg-slate-50 p-4 text-xs leading-5 text-slate-600">
          {t("reportCards.templates.previewHelp")}
        </div>
      </section>
    </div>
  );
}
