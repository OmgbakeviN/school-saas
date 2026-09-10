import { useEffect, useMemo, useState } from "react";
import Dialog from "../../components/Dialog";
import Field from "../../components/Field";
import { useI18n } from "../../i18n";

const inputClass =
  "w-full rounded-xl border border-slate-200 bg-white px-3.5 py-3 text-sm outline-none focus:border-slate-400 focus:ring-4 focus:ring-slate-100";

export default function AssessmentDialog({ open, item, assignments, periods, onClose, onSave }) {
  const { t } = useI18n();
  const [form, setForm] = useState({
    teaching_assignment: "",
    academic_period: "",
    title: "",
    kind: "TEST",
    assessment_date: "",
    max_score: "20",
    weight: "1",
    instructions: "",
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open) return;
    setForm({
      teaching_assignment: item?.teaching_assignment ? String(item.teaching_assignment) : "",
      academic_period: item?.academic_period ? String(item.academic_period) : "",
      title: item?.title || "",
      kind: item?.kind || "TEST",
      assessment_date: item?.assessment_date || "",
      max_score: item?.max_score || "20",
      weight: item?.weight || "1",
      instructions: item?.instructions || "",
    });
  }, [open, item]);

  const selectedAssignment = assignments.find(
    (assignment) => String(assignment.id) === String(form.teaching_assignment)
  );

  const filteredPeriods = useMemo(() => {
    if (!selectedAssignment) return periods;
    return periods.filter(
      (period) => String(period.academic_year) === String(selectedAssignment.academic_year)
    );
  }, [periods, selectedAssignment]);

  const submit = async (event) => {
    event.preventDefault();
    setSaving(true);
    try {
      await onSave({
        ...form,
        teaching_assignment: Number(form.teaching_assignment),
        academic_period: Number(form.academic_period),
      });
      onClose();
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={item ? t("assessments.dialog.editTitle") : t("assessments.dialog.createTitle")}
      description={t("assessments.dialog.help")}
    >
      <form onSubmit={submit} className="space-y-4">
        <Field label={t("assessments.fields.assignment")}>
          <select
            required
            disabled={Boolean(item?.grade_count)}
            className={inputClass}
            value={form.teaching_assignment}
            onChange={(e) =>
              setForm({ ...form, teaching_assignment: e.target.value, academic_period: "" })
            }
          >
            <option value="">{t("common.choose")}</option>
            {assignments.filter((a) => a.is_active && a.can_enter_scores).map((assignment) => (
              <option key={assignment.id} value={assignment.id}>
                {assignment.subject_name} • {assignment.classroom_name} • {assignment.teacher_name}{assignment.is_automatic ? ` • ${t("assessments.fields.classTeacherAccess")}` : ""}
              </option>
            ))}
          </select>
        </Field>

        <Field label={t("assessments.fields.period")}>
          <select
            required
            disabled={Boolean(item?.grade_count)}
            className={inputClass}
            value={form.academic_period}
            onChange={(e) => setForm({ ...form, academic_period: e.target.value })}
          >
            <option value="">{t("common.choose")}</option>
            {filteredPeriods.map((period) => (
              <option key={period.id} value={period.id}>
                {period.name} • {period.academic_year_name}
              </option>
            ))}
          </select>
        </Field>

        <div className="grid gap-4 sm:grid-cols-2">
          <Field label={t("assessments.fields.title")}>
            <input
              required
              className={inputClass}
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
            />
          </Field>
          <Field label={t("assessments.fields.kind")}>
            <select
              className={inputClass}
              value={form.kind}
              onChange={(e) => setForm({ ...form, kind: e.target.value })}
            >
              {[
                ["QUIZ", t("assessments.kinds.quiz")],
                ["TEST", t("assessments.kinds.test")],
                ["HOMEWORK", t("assessments.kinds.homework")],
                ["EXAM", t("assessments.kinds.exam")],
                ["ORAL", t("assessments.kinds.oral")],
                ["PRACTICAL", t("assessments.kinds.practical")],
                ["OTHER", t("assessments.kinds.other")],
              ].map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select>
          </Field>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <Field label={t("assessments.fields.date")}>
            <input
              type="date"
              className={inputClass}
              value={form.assessment_date}
              onChange={(e) => setForm({ ...form, assessment_date: e.target.value })}
            />
          </Field>
          <Field label={t("assessments.fields.maxScore")}>
            <input
              required
              min="0.01"
              step="0.01"
              type="number"
              disabled={Boolean(item?.grade_count)}
              className={inputClass}
              value={form.max_score}
              onChange={(e) => setForm({ ...form, max_score: e.target.value })}
            />
          </Field>
          <Field label={t("assessments.fields.weight")}>
            <input
              required
              min="0.001"
              step="0.001"
              type="number"
              className={inputClass}
              value={form.weight}
              onChange={(e) => setForm({ ...form, weight: e.target.value })}
            />
          </Field>
        </div>

        <Field label={t("assessments.fields.instructions")}>
          <textarea
            rows={3}
            className={inputClass}
            value={form.instructions}
            onChange={(e) => setForm({ ...form, instructions: e.target.value })}
          />
        </Field>

        <div className="flex justify-end gap-2 pt-2">
          <button type="button" onClick={onClose} className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm">
            {t("common.cancel")}
          </button>
          <button disabled={saving} className="rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-medium text-white disabled:opacity-40">
            {saving ? t("common.loading") : t("common.save")}
          </button>
        </div>
      </form>
    </Dialog>
  );
}
