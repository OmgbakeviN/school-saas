import { useEffect, useMemo, useState } from "react";
import { Loader2 } from "lucide-react";

import Dialog from "../../components/Dialog";
import Field from "../../components/Field";
import { useI18n } from "../../i18n";
import api from "../../services/api";

const inputClass =
  "w-full rounded-xl border border-slate-200 bg-white px-3.5 py-3 text-sm outline-none focus:border-slate-400 focus:ring-4 focus:ring-slate-100";

export default function LeadershipDialog({
  open,
  item,
  years,
  teachers,
  classrooms,
  onClose,
  onSaved,
}) {
  const { t } = useI18n();
  const [form, setForm] = useState({
    academic_year: "",
    classroom: "",
    teacher: "",
    role: "CLASS_TEACHER",
    is_active: true,
    notes: "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) return;
    const activeYear = years.find((year) => year.is_active) || years[0];
    setError("");
    setForm(
      item
        ? {
            academic_year: String(item.academic_year),
            classroom: String(item.classroom),
            teacher: String(item.teacher),
            role: item.role,
            is_active: item.is_active,
            notes: item.notes || "",
          }
        : {
            academic_year: String(activeYear?.id || ""),
            classroom: "",
            teacher: "",
            role: "CLASS_TEACHER",
            is_active: true,
            notes: "",
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

  const submit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError("");

    try {
      const payload = {
        academic_year: Number(form.academic_year),
        classroom: Number(form.classroom),
        teacher: Number(form.teacher),
        role: form.role,
        is_active: form.is_active,
        notes: form.notes,
      };

      if (item) {
        await api.patch(`/teaching/leaderships/${item.id}/`, payload);
      } else {
        await api.post("/teaching/leaderships/", payload);
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
            : payload?.detail || t("teaching.errors.saveLeadership")
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={item ? t("teaching.leadership.editTitle") : t("teaching.leadership.createTitle")}
      description={t("teaching.leadership.dialogHelp")}
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
            form="classroom-leadership-form"
            disabled={saving}
            className="inline-flex items-center gap-2 rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-medium text-white disabled:opacity-50"
          >
            {saving && <Loader2 size={16} className="animate-spin" />}
            {t("common.save")}
          </button>
        </div>
      }
    >
      <form id="classroom-leadership-form" onSubmit={submit} className="space-y-4">
        {error && (
          <div className="rounded-xl bg-rose-50 px-3.5 py-3 text-sm text-rose-700">
            {error}
          </div>
        )}

        <Field label={t("teaching.fields.year")}>
          <select
            required
            className={inputClass}
            value={form.academic_year}
            onChange={(e) =>
              setForm({ ...form, academic_year: e.target.value, classroom: "" })
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

        <Field label={t("teaching.fields.classroom")}>
          <select
            required
            className={inputClass}
            value={form.classroom}
            onChange={(e) => setForm({ ...form, classroom: e.target.value })}
          >
            <option value="">{t("common.choose")}</option>
            {availableClassrooms.map((classroom) => (
              <option key={classroom.id} value={classroom.id}>
                {classroom.name} • {classroom.level_name}
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
                  {teacher.last_name} {teacher.first_name}
                </option>
              ))}
          </select>
        </Field>

        <Field label={t("teaching.fields.role")}>
          <select
            className={inputClass}
            value={form.role}
            onChange={(e) => setForm({ ...form, role: e.target.value })}
          >
            <option value="CLASS_TEACHER">{t("teaching.roles.classTeacher")}</option>
            <option value="HOMEROOM_TEACHER">{t("teaching.roles.homeroomTeacher")}</option>
          </select>
        </Field>

        <Field label={t("teaching.fields.notes")} hint={t("common.optional")}>
          <input
            className={inputClass}
            value={form.notes}
            onChange={(e) => setForm({ ...form, notes: e.target.value })}
          />
        </Field>

        <label className="flex items-center gap-3 rounded-xl border border-slate-200 px-3.5 py-3 text-sm">
          <input
            type="checkbox"
            checked={form.is_active}
            onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
          />
          {t("teaching.fields.active")}
        </label>
      </form>
    </Dialog>
  );
}
