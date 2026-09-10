import { useEffect, useState } from "react";
import { Loader2, Save } from "lucide-react";

import Dialog from "../../components/Dialog";
import Field from "../../components/Field";
import { useI18n } from "../../i18n";
import api from "../../services/api";

const inputClass =
  "w-full rounded-xl border border-slate-200 bg-white px-3.5 py-3 text-sm outline-none focus:border-slate-400 focus:ring-4 focus:ring-slate-100";

const emptyForm = {
  matricule: "",
  first_name: "",
  last_name: "",
  gender: "",
  date_of_birth: "",
  place_of_birth: "",
  nationality: "",
  address: "",
  phone: "",
  email: "",
  admission_date: "",
  status: "ACTIVE",
  notes: "",
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

export default function StudentDialog({
  open,
  student,
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
      student
        ? {
            matricule: student.matricule || "",
            first_name: student.first_name || "",
            last_name: student.last_name || "",
            gender: student.gender || "",
            date_of_birth: student.date_of_birth || "",
            place_of_birth: student.place_of_birth || "",
            nationality: student.nationality || "",
            address: student.address || "",
            phone: student.phone || "",
            email: student.email || "",
            admission_date: student.admission_date || "",
            status: student.status || "ACTIVE",
            notes: student.notes || "",
          }
        : emptyForm
    );
    setError("");
  }, [open, student]);

  const submit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError("");

    const payload = {
      ...form,
      date_of_birth: form.date_of_birth || null,
      admission_date: form.admission_date || null,
    };

    try {
      const { data } = student
        ? await api.patch(`/people/students/${student.id}/`, payload)
        : await api.post("/people/students/", payload);

      await onSaved?.(data);
      onClose?.();
    } catch (err) {
      setError(parseError(err, t("people.errors.saveStudent")));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={() => !saving && onClose?.()}
      title={
        student
          ? t("people.students.editTitle")
          : t("people.students.createTitle")
      }
      description={t("people.students.dialogHelp")}
      maxWidth="max-w-3xl"
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
            form="student-form"
            disabled={saving}
            className="inline-flex items-center gap-2 rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-medium text-white disabled:opacity-50"
          >
            {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
            {t("common.save")}
          </button>
        </div>
      }
    >
      <form id="student-form" onSubmit={submit} className="space-y-5">
        {error && (
          <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {error}
          </div>
        )}

        <div className="grid gap-4 sm:grid-cols-2">
          <Field label={t("people.students.matricule")} hint={t("people.students.autoCode")}>
            <input
              className={inputClass}
              value={form.matricule}
              onChange={(e) => setForm({ ...form, matricule: e.target.value })}
              placeholder="STU-00001"
            />
          </Field>

          <Field label={t("people.students.status")}>
            <select
              className={inputClass}
              value={form.status}
              onChange={(e) => setForm({ ...form, status: e.target.value })}
            >
              <option value="ACTIVE">{t("people.status.active")}</option>
              <option value="INACTIVE">{t("people.status.inactive")}</option>
              <option value="GRADUATED">{t("people.status.graduated")}</option>
              <option value="TRANSFERRED">{t("people.status.transferred")}</option>
              <option value="WITHDRAWN">{t("people.status.withdrawn")}</option>
            </select>
          </Field>

          <Field label={t("people.fields.firstName")}>
            <input required className={inputClass} value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} />
          </Field>

          <Field label={t("people.fields.lastName")}>
            <input required className={inputClass} value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} />
          </Field>

          <Field label={t("people.students.gender")} hint={t("common.optional")}>
            <select className={inputClass} value={form.gender} onChange={(e) => setForm({ ...form, gender: e.target.value })}>
              <option value="">{t("common.choose")}</option>
              <option value="MALE">{t("people.gender.male")}</option>
              <option value="FEMALE">{t("people.gender.female")}</option>
              <option value="OTHER">{t("people.gender.other")}</option>
            </select>
          </Field>

          <Field label={t("people.students.birthDate")} hint={t("common.optional")}>
            <input type="date" className={inputClass} value={form.date_of_birth} onChange={(e) => setForm({ ...form, date_of_birth: e.target.value })} />
          </Field>

          <Field label={t("people.students.birthPlace")} hint={t("common.optional")}>
            <input className={inputClass} value={form.place_of_birth} onChange={(e) => setForm({ ...form, place_of_birth: e.target.value })} />
          </Field>

          <Field label={t("people.students.nationality")} hint={t("common.optional")}>
            <input className={inputClass} value={form.nationality} onChange={(e) => setForm({ ...form, nationality: e.target.value })} />
          </Field>

          <Field label={t("people.fields.phone")} hint={t("common.optional")}>
            <input className={inputClass} value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          </Field>

          <Field label={t("people.fields.email")} hint={t("common.optional")}>
            <input type="email" className={inputClass} value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          </Field>

          <Field label={t("people.students.admissionDate")} hint={t("common.optional")}>
            <input type="date" className={inputClass} value={form.admission_date} onChange={(e) => setForm({ ...form, admission_date: e.target.value })} />
          </Field>

          <Field label={t("people.fields.address")} hint={t("common.optional")}>
            <input className={inputClass} value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
          </Field>

          <div className="sm:col-span-2">
            <Field label={t("people.fields.notes")} hint={t("common.optional")}>
              <textarea
                className={`${inputClass} min-h-24 resize-y`}
                value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
              />
            </Field>
          </div>
        </div>
      </form>
    </Dialog>
  );
}
