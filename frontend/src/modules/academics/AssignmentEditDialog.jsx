import { useEffect, useState } from "react";
import { Loader2, Save } from "lucide-react";

import Dialog from "../../components/Dialog";
import Field from "../../components/Field";
import { useI18n } from "../../i18n";
import api from "../../services/api";

const inputClass =
  "w-full rounded-xl border border-slate-200 bg-white px-3.5 py-3 text-sm outline-none focus:border-slate-400 focus:ring-4 focus:ring-slate-100";

export default function AssignmentEditDialog({
  assignment,
  open,
  onClose,
  onSaved,
}) {
  const { t } = useI18n();
  const [form, setForm] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (assignment) {
      setForm({
        coefficient: assignment.coefficient ?? "1",
        max_score_override:
          assignment.max_score_override ?? "",
        teaching_language:
          assignment.teaching_language || "DEFAULT",
        is_active: assignment.is_active !== false,
      });
      setError("");
    }
  }, [assignment, open]);

  if (!form) return null;

  const save = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError("");

    try {
      const { data } = await api.patch(
        `/academics/level-subjects/${assignment.id}/`,
        {
          coefficient: Number(form.coefficient),
          max_score_override:
            form.max_score_override === ""
              ? null
              : Number(form.max_score_override),
          teaching_language: form.teaching_language,
          is_active: form.is_active,
        }
      );
      await onSaved?.(data);
      onClose?.();
    } catch (err) {
      const payload = err?.response?.data;
      const first =
        payload && typeof payload === "object"
          ? Object.values(payload)[0]
          : null;

      setError(
        payload?.detail ||
          (Array.isArray(first) ? first[0] : null) ||
          t("curriculum.errors.save")
      );
    } finally {
      setSaving(false);
    }
  };

  const title = assignment
    ? `${assignment.subject_name} — ${assignment.level_name}`
    : t("curriculum.subjects.editAssignmentTitle");

  return (
    <Dialog
      open={open}
      onClose={() => !saving && onClose?.()}
      title={title}
      description={t("curriculum.subjects.editAssignmentHelp")}
      footer={
        <div className="flex justify-end gap-2">
          <button
            type="button"
            disabled={saving}
            onClick={onClose}
            className="rounded-xl px-4 py-2.5 text-sm font-medium text-slate-600 hover:bg-white"
          >
            {t("common.cancel")}
          </button>
          <button
            type="submit"
            form="assignment-edit-form"
            disabled={saving}
            className="inline-flex items-center gap-2 rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-medium text-white disabled:opacity-50"
          >
            {saving ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <Save size={16} />
            )}
            {t("common.save")}
          </button>
        </div>
      }
    >
      <form
        id="assignment-edit-form"
        onSubmit={save}
        className="space-y-4"
      >
        {error && (
          <div className="rounded-xl border border-rose-200 bg-rose-50 px-3.5 py-3 text-sm text-rose-700">
            {error}
          </div>
        )}

        <Field label={t("curriculum.subjects.coefficient")}>
          <input
            required
            type="number"
            min="0.001"
            step="0.001"
            className={inputClass}
            value={form.coefficient}
            onChange={(event) =>
              setForm({
                ...form,
                coefficient: event.target.value,
              })
            }
          />
        </Field>

        <Field
          label={t("curriculum.subjects.maxScore")}
          hint={t("curriculum.rules.inherit")}
        >
          <input
            type="number"
            min="0.01"
            step="0.01"
            className={inputClass}
            value={form.max_score_override}
            onChange={(event) =>
              setForm({
                ...form,
                max_score_override: event.target.value,
              })
            }
          />
        </Field>

        <Field label={t("curriculum.subjects.language")}>
          <select
            className={inputClass}
            value={form.teaching_language}
            onChange={(event) =>
              setForm({
                ...form,
                teaching_language: event.target.value,
              })
            }
          >
            <option value="DEFAULT">
              {t("curriculum.languages.section")}
            </option>
            <option value="FRENCH">{t("common.french")}</option>
            <option value="ENGLISH">{t("common.english")}</option>
            <option value="BILINGUAL">
              {t("curriculum.languages.bilingual")}
            </option>
          </select>
        </Field>

        <label className="flex items-center gap-3 rounded-xl border border-slate-200 px-3.5 py-3 text-sm">
          <input
            type="checkbox"
            checked={form.is_active}
            onChange={(event) =>
              setForm({
                ...form,
                is_active: event.target.checked,
              })
            }
          />
          {t("curriculum.subjects.activeAssignment")}
        </label>
      </form>
    </Dialog>
  );
}
