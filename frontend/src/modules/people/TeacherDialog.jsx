import { useEffect, useState } from "react";
import { Loader2, Save } from "lucide-react";

import Dialog from "../../components/Dialog";
import Field from "../../components/Field";
import { useI18n } from "../../i18n";
import api from "../../services/api";

const inputClass =
  "w-full rounded-xl border border-slate-200 bg-white px-3.5 py-3 text-sm outline-none focus:border-slate-400 focus:ring-4 focus:ring-slate-100";

const emptyForm = {
  employee_number: "",
  first_name: "",
  last_name: "",
  phone: "",
  email: "",
  speciality: "",
  hire_date: "",
  status: "ACTIVE",
  notes: "",
};

function parseError(error, fallback) {
  const payload = error?.response?.data;
  if (!payload) return fallback;
  if (payload.detail) return String(payload.detail);
  const first = Object.values(payload)[0];
  if (Array.isArray(first)) return String(first[0]);
  return fallback;
}

export default function TeacherDialog({
  open,
  teacher,
  onClose,
  onSaved,
}) {
  const { t } = useI18n();
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) return;
    setForm(
      teacher
        ? {
            employee_number: teacher.employee_number || "",
            first_name: teacher.first_name || "",
            last_name: teacher.last_name || "",
            phone: teacher.phone || "",
            email: teacher.email || "",
            speciality: teacher.speciality || "",
            hire_date: teacher.hire_date || "",
            status: teacher.status || "ACTIVE",
            notes: teacher.notes || "",
          }
        : emptyForm
    );
    setError("");
  }, [open, teacher]);

  const submit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError("");

    try {
      const payload = {
        ...form,
        hire_date: form.hire_date || null,
      };

      const { data } = teacher
        ? await api.patch(`/people/teachers/${teacher.id}/`, payload)
        : await api.post("/people/teachers/", payload);

      await onSaved?.(data);
      onClose?.();
    } catch (err) {
      setError(parseError(err, t("people.errors.saveTeacher")));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={() => !saving && onClose?.()}
      title={teacher ? t("people.teachers.editTitle") : t("people.teachers.createTitle")}
      description={t("people.teachers.dialogHelp")}
      maxWidth="max-w-2xl"
      footer={
        <div className="flex justify-end gap-2">
          <button type="button" disabled={saving} onClick={onClose} className="rounded-xl px-4 py-2.5 text-sm font-medium text-slate-600 hover:bg-white">
            {t("common.cancel")}
          </button>
          <button type="submit" form="teacher-form" disabled={saving} className="inline-flex items-center gap-2 rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-medium text-white disabled:opacity-50">
            {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
            {t("common.save")}
          </button>
        </div>
      }
    >
      <form id="teacher-form" onSubmit={submit} className="space-y-4">
        {error && <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>}

        <div className="grid gap-4 sm:grid-cols-2">
          <Field label={t("people.teachers.employeeNumber")} hint={t("people.students.autoCode")}>
            <input className={inputClass} value={form.employee_number} onChange={(e) => setForm({ ...form, employee_number: e.target.value })} />
          </Field>

          <Field label={t("people.teachers.status")}>
            <select className={inputClass} value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
              <option value="ACTIVE">{t("people.status.active")}</option>
              <option value="INACTIVE">{t("people.status.inactive")}</option>
            </select>
          </Field>

          <Field label={t("people.fields.firstName")}>
            <input required className={inputClass} value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} />
          </Field>

          <Field label={t("people.fields.lastName")}>
            <input required className={inputClass} value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} />
          </Field>

          <Field label={t("people.fields.phone")} hint={t("common.optional")}>
            <input className={inputClass} value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          </Field>

          <Field label={t("people.fields.email")} hint={t("common.optional")}>
            <input type="email" className={inputClass} value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          </Field>

          <Field label={t("people.teachers.speciality")} hint={t("common.optional")}>
            <input className={inputClass} value={form.speciality} onChange={(e) => setForm({ ...form, speciality: e.target.value })} />
          </Field>

          <Field label={t("people.teachers.hireDate")} hint={t("common.optional")}>
            <input type="date" className={inputClass} value={form.hire_date} onChange={(e) => setForm({ ...form, hire_date: e.target.value })} />
          </Field>

          <div className="sm:col-span-2">
            <Field label={t("people.fields.notes")} hint={t("common.optional")}>
              <textarea className={`${inputClass} min-h-24`} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
            </Field>
          </div>
        </div>
      </form>
    </Dialog>
  );
}
