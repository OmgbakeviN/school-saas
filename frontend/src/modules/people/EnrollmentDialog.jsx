import { useEffect, useMemo, useState } from "react";
import { Loader2, Save } from "lucide-react";

import Dialog from "../../components/Dialog";
import Field from "../../components/Field";
import { useI18n } from "../../i18n";
import api from "../../services/api";

const inputClass =
  "w-full rounded-xl border border-slate-200 bg-white px-3.5 py-3 text-sm outline-none focus:border-slate-400 focus:ring-4 focus:ring-slate-100";

export default function EnrollmentDialog({
  open,
  enrollment,
  students,
  years,
  classrooms,
  onClose,
  onSaved,
}) {
  const { t } = useI18n();
  const activeYear = years.find((year) => year.is_active) || years[0] || null;

  const [form, setForm] = useState({
    student: "",
    academic_year: "",
    classroom: "",
    enrollment_date: "",
    roll_number: "",
    status: "ACTIVE",
    promotion_decision: "PENDING",
    final_average: "",
    decision_reason: "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) return;

    setForm(
      enrollment
        ? {
            student: String(enrollment.student),
            academic_year: String(enrollment.academic_year),
            classroom: String(enrollment.classroom),
            enrollment_date: enrollment.enrollment_date || "",
            roll_number: enrollment.roll_number || "",
            status: enrollment.status || "ACTIVE",
            promotion_decision: enrollment.promotion_decision || "PENDING",
            final_average: enrollment.final_average ?? "",
            decision_reason: enrollment.decision_reason || "",
          }
        : {
            student: "",
            academic_year: activeYear ? String(activeYear.id) : "",
            classroom: "",
            enrollment_date: "",
            roll_number: "",
            status: "ACTIVE",
            promotion_decision: "PENDING",
            final_average: "",
            decision_reason: "",
          }
    );

    setError("");
  }, [open, enrollment, activeYear?.id]);

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
        ...form,
        student: Number(form.student),
        academic_year: Number(form.academic_year),
        classroom: Number(form.classroom),
        enrollment_date: form.enrollment_date || null,
        final_average: form.final_average === "" ? null : Number(form.final_average),
      };

      const { data } = enrollment
        ? await api.patch(`/people/enrollments/${enrollment.id}/`, payload)
        : await api.post("/people/enrollments/", payload);

      await onSaved?.(data);
      onClose?.();
    } catch (err) {
      const payload = err?.response?.data;
      const first = payload && Object.values(payload)[0];
      let message = payload?.detail;

      if (!message && Array.isArray(first)) {
        message = first[0];
      } else if (!message && first && typeof first === "object") {
        const nested = Object.values(first)[0];
        message = Array.isArray(nested) ? nested[0] : nested;
      }

      setError(message || t("people.errors.saveEnrollment"));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={() => !saving && onClose?.()}
      title={enrollment ? t("people.enrollments.editTitle") : t("people.enrollments.createTitle")}
      description={t("people.enrollments.dialogHelp")}
      maxWidth="max-w-3xl"
      footer={
        <div className="flex justify-end gap-2">
          <button type="button" disabled={saving} onClick={onClose} className="rounded-xl px-4 py-2.5 text-sm font-medium text-slate-600 hover:bg-white">
            {t("common.cancel")}
          </button>
          <button type="submit" form="enrollment-form" disabled={saving || !form.student || !form.academic_year || !form.classroom} className="inline-flex items-center gap-2 rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-medium text-white disabled:opacity-50">
            {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
            {t("common.save")}
          </button>
        </div>
      }
    >
      <form id="enrollment-form" onSubmit={submit} className="space-y-5">
        {error && <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>}

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <Field label={t("people.enrollments.student")}>
              <select
                required
                disabled={Boolean(enrollment)}
                className={inputClass}
                value={form.student}
                onChange={(e) => setForm({ ...form, student: e.target.value })}
              >
                <option value="">{t("common.choose")}</option>
                {students.map((student) => (
                  <option key={student.id} value={student.id}>
                    {student.last_name} {student.first_name} — {student.matricule}
                  </option>
                ))}
              </select>
            </Field>
          </div>

          <Field label={t("people.enrollments.year")}>
            <select
              required
              className={inputClass}
              value={form.academic_year}
              onChange={(e) =>
                setForm({
                  ...form,
                  academic_year: e.target.value,
                  classroom: "",
                })
              }
            >
              <option value="">{t("common.choose")}</option>
              {years.map((year) => (
                <option key={year.id} value={year.id}>
                  {year.name}{year.is_active ? ` — ${t("common.active")}` : ""}
                </option>
              ))}
            </select>
          </Field>

          <Field label={t("people.enrollments.classroom")}>
            <select required className={inputClass} value={form.classroom} onChange={(e) => setForm({ ...form, classroom: e.target.value })}>
              <option value="">{t("common.choose")}</option>
              {availableClassrooms.map((classroom) => (
                <option key={classroom.id} value={classroom.id}>
                  {classroom.name} — {classroom.level_name}
                </option>
              ))}
            </select>
          </Field>

          <Field label={t("people.enrollments.date")} hint={t("common.optional")}>
            <input type="date" className={inputClass} value={form.enrollment_date} onChange={(e) => setForm({ ...form, enrollment_date: e.target.value })} />
          </Field>

          <Field label={t("people.enrollments.rollNumber")} hint={t("common.optional")}>
            <input className={inputClass} value={form.roll_number} onChange={(e) => setForm({ ...form, roll_number: e.target.value })} />
          </Field>

          <Field label={t("people.enrollments.status")}>
            <select className={inputClass} value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
              <option value="ACTIVE">{t("people.enrollmentStatus.active")}</option>
              <option value="COMPLETED">{t("people.enrollmentStatus.completed")}</option>
              <option value="TRANSFERRED">{t("people.enrollmentStatus.transferred")}</option>
              <option value="WITHDRAWN">{t("people.enrollmentStatus.withdrawn")}</option>
            </select>
          </Field>

          <Field label={t("people.enrollments.decision")}>
            <select className={inputClass} value={form.promotion_decision} onChange={(e) => setForm({ ...form, promotion_decision: e.target.value })}>
              <option value="PENDING">{t("people.promotion.pending")}</option>
              <option value="PROMOTED">{t("people.promotion.promoted")}</option>
              <option value="REPEATED">{t("people.promotion.repeated")}</option>
              <option value="GRADUATED">{t("people.promotion.graduated")}</option>
              <option value="TRANSFERRED">{t("people.promotion.transferred")}</option>
              <option value="WITHDRAWN">{t("people.promotion.withdrawn")}</option>
            </select>
          </Field>

          <Field label={t("people.enrollments.finalAverage")} hint={t("people.enrollments.futureCalculated")}>
            <input type="number" step="0.001" className={inputClass} value={form.final_average} onChange={(e) => setForm({ ...form, final_average: e.target.value })} />
          </Field>

          <div className="sm:col-span-2">
            <Field label={t("people.enrollments.reason")} hint={t("common.optional")}>
              <textarea className={`${inputClass} min-h-20`} value={form.decision_reason} onChange={(e) => setForm({ ...form, decision_reason: e.target.value })} />
            </Field>
          </div>
        </div>
      </form>
    </Dialog>
  );
}
