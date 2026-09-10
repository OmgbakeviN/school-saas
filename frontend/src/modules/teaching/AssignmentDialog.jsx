import { useEffect, useMemo, useState } from "react";
import { Loader2 } from "lucide-react";

import Dialog from "../../components/Dialog";
import Field from "../../components/Field";
import { useI18n } from "../../i18n";
import api from "../../services/api";

const inputClass =
  "w-full rounded-xl border border-slate-200 bg-white px-3.5 py-3 text-sm outline-none focus:border-slate-400 focus:ring-4 focus:ring-slate-100";

const emptyForm = {
  academic_year: "",
  teacher: "",
  classroom: "",
  subject: "",
  can_enter_scores: true,
  is_active: true,
  notes: "",
};

export default function AssignmentDialog({
  open,
  item,
  years,
  teachers,
  classrooms,
  levelSubjects,
  subjects,
  onClose,
  onSaved,
}) {
  const { t } = useI18n();
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) return;
    setError("");
    setForm(
      item
        ? {
            academic_year: String(item.academic_year),
            teacher: String(item.teacher),
            classroom: String(item.classroom),
            subject: String(item.subject),
            can_enter_scores: item.can_enter_scores,
            is_active: item.is_active,
            notes: item.notes || "",
          }
        : {
            ...emptyForm,
            academic_year: String(
              years.find((year) => year.is_active)?.id || years[0]?.id || ""
            ),
          }
    );
  }, [open, item, years]);

  const availableClassrooms = useMemo(
    () =>
      classrooms.filter(
        (classroom) =>
          String(classroom.academic_year) === String(form.academic_year)
      ),
    [classrooms, form.academic_year]
  );

  const selectedClassroom = classrooms.find(
    (classroom) => String(classroom.id) === String(form.classroom)
  );

  const allowedSubjectIds = useMemo(() => {
    if (!selectedClassroom) return new Set();
    return new Set(
      levelSubjects
        .filter(
          (config) =>
            config.is_active &&
            String(config.level) === String(selectedClassroom.level)
        )
        .map((config) => Number(config.subject))
    );
  }, [levelSubjects, selectedClassroom]);

  const availableSubjects = subjects.filter(
    (subject) => subject.is_active && allowedSubjectIds.has(Number(subject.id))
  );

  const submit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError("");

    try {
      const payload = {
        academic_year: Number(form.academic_year),
        teacher: Number(form.teacher),
        classroom: Number(form.classroom),
        subject: Number(form.subject),
        can_enter_scores: form.can_enter_scores,
        is_active: form.is_active,
        notes: form.notes,
      };

      if (item) {
        await api.patch(`/teaching/assignments/${item.id}/`, payload);
      } else {
        await api.post("/teaching/assignments/", payload);
      }

      await onSaved?.();
      onClose?.();
    } catch (err) {
      const payload = err?.response?.data;
      const first = payload && Object.values(payload)[0];
      setError(
        Array.isArray(first)
          ? String(first[0])
          : typeof first === "string"
            ? first
            : payload?.detail || t("teaching.errors.saveAssignment")
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={item ? t("teaching.assignment.editTitle") : t("teaching.assignment.createTitle")}
      description={t("teaching.assignment.dialogHelp")}
      maxWidth="max-w-2xl"
      footer={
        <div className="flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-700"
          >
            {t("common.cancel")}
          </button>
          <button
            form="teaching-assignment-form"
            disabled={saving}
            className="inline-flex items-center gap-2 rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-medium text-white disabled:opacity-50"
          >
            {saving && <Loader2 size={16} className="animate-spin" />}
            {t("common.save")}
          </button>
        </div>
      }
    >
      <form id="teaching-assignment-form" onSubmit={submit} className="space-y-4">
        {error && (
          <div className="rounded-xl bg-rose-50 px-3.5 py-3 text-sm text-rose-700">
            {error}
          </div>
        )}

        <div className="grid gap-4 sm:grid-cols-2">
          <Field label={t("teaching.fields.year")}>
            <select
              required
              className={inputClass}
              value={form.academic_year}
              onChange={(e) =>
                setForm({
                  ...form,
                  academic_year: e.target.value,
                  classroom: "",
                  subject: "",
                })
              }
            >
              <option value="">{t("common.choose")}</option>
              {years.map((year) => (
                <option key={year.id} value={year.id}>
                  {year.name}
                </option>
              ))}
            </select>
          </Field>

          <Field label={t("teaching.fields.teacher")}>
            <select
              required
              className={inputClass}
              value={form.teacher}
              onChange={(e) => setForm({ ...form, teacher: e.target.value })}
            >
              <option value="">{t("common.choose")}</option>
              {teachers
                .filter((teacher) => teacher.status === "ACTIVE")
                .map((teacher) => (
                  <option key={teacher.id} value={teacher.id}>
                    {teacher.last_name} {teacher.first_name} • {teacher.employee_number}
                  </option>
                ))}
            </select>
          </Field>

          <Field label={t("teaching.fields.classroom")}>
            <select
              required
              className={inputClass}
              value={form.classroom}
              onChange={(e) =>
                setForm({ ...form, classroom: e.target.value, subject: "" })
              }
            >
              <option value="">{t("common.choose")}</option>
              {availableClassrooms.map((classroom) => (
                <option key={classroom.id} value={classroom.id}>
                  {classroom.name} • {classroom.level_name}
                </option>
              ))}
            </select>
          </Field>

          <Field
            label={t("teaching.fields.subject")}
            hint={selectedClassroom ? t("teaching.assignment.subjectHint") : ""}
          >
            <select
              required
              disabled={!selectedClassroom}
              className={inputClass}
              value={form.subject}
              onChange={(e) => setForm({ ...form, subject: e.target.value })}
            >
              <option value="">{t("common.choose")}</option>
              {availableSubjects.map((subject) => (
                <option key={subject.id} value={subject.id}>
                  {subject.name}
                </option>
              ))}
            </select>
          </Field>
        </div>

        <Field label={t("teaching.fields.notes")} hint={t("common.optional")}>
          <input
            className={inputClass}
            value={form.notes}
            onChange={(e) => setForm({ ...form, notes: e.target.value })}
          />
        </Field>

        <div className="grid gap-2 sm:grid-cols-2">
          <label className="flex items-center gap-3 rounded-xl border border-slate-200 px-3.5 py-3 text-sm">
            <input
              type="checkbox"
              checked={form.can_enter_scores}
              onChange={(e) =>
                setForm({ ...form, can_enter_scores: e.target.checked })
              }
            />
            {t("teaching.assignment.scorePermission")}
          </label>

          <label className="flex items-center gap-3 rounded-xl border border-slate-200 px-3.5 py-3 text-sm">
            <input
              type="checkbox"
              checked={form.is_active}
              onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
            />
            {t("teaching.fields.active")}
          </label>
        </div>
      </form>
    </Dialog>
  );
}
