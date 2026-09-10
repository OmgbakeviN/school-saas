import { useEffect, useState } from "react";
import { Link2, Loader2 } from "lucide-react";

import Dialog from "../../components/Dialog";
import Field from "../../components/Field";
import { useI18n } from "../../i18n";
import api from "../../services/api";

const inputClass =
  "w-full rounded-xl border border-slate-200 bg-white px-3.5 py-3 text-sm outline-none focus:border-slate-400 focus:ring-4 focus:ring-slate-100";

export default function GuardianLinkDialog({
  open,
  guardian,
  students,
  onClose,
  onSaved,
}) {
  const { t } = useI18n();
  const [form, setForm] = useState({
    student: "",
    relationship: "GUARDIAN",
    is_primary: false,
    receives_notifications: true,
    can_receive_results: true,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) return;
    setForm({
      student: "",
      relationship: "GUARDIAN",
      is_primary: false,
      receives_notifications: true,
      can_receive_results: true,
    });
    setError("");
  }, [open, guardian]);

  const submit = async (event) => {
    event.preventDefault();
    if (!guardian) return;

    setSaving(true);
    setError("");

    try {
      const { data } = await api.post("/people/guardian-links/", {
        ...form,
        student: Number(form.student),
        guardian: guardian.id,
      });
      await onSaved?.(data);
      onClose?.();
    } catch (err) {
      const payload = err?.response?.data;
      const first = payload && Object.values(payload)[0];
      setError(
        payload?.detail ||
          (Array.isArray(first) ? first[0] : null) ||
          t("people.errors.linkGuardian")
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={() => !saving && onClose?.()}
      title={t("people.guardians.linkTitle")}
      description={
        guardian
          ? t("people.guardians.linkHelp", {
              name: `${guardian.first_name} ${guardian.last_name}`,
            })
          : ""
      }
      footer={
        <div className="flex justify-end gap-2">
          <button type="button" disabled={saving} onClick={onClose} className="rounded-xl px-4 py-2.5 text-sm font-medium text-slate-600 hover:bg-white">
            {t("common.cancel")}
          </button>
          <button
            type="submit"
            form="guardian-link-form"
            disabled={saving || !form.student}
            className="inline-flex items-center gap-2 rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-medium text-white disabled:opacity-50"
          >
            {saving ? <Loader2 size={16} className="animate-spin" /> : <Link2 size={16} />}
            {t("people.guardians.link")}
          </button>
        </div>
      }
    >
      <form id="guardian-link-form" onSubmit={submit} className="space-y-4">
        {error && <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>}

        <Field label={t("people.guardians.student")}>
          <select required className={inputClass} value={form.student} onChange={(e) => setForm({ ...form, student: e.target.value })}>
            <option value="">{t("common.choose")}</option>
            {students.map((student) => (
              <option key={student.id} value={student.id}>
                {student.last_name} {student.first_name} — {student.matricule}
              </option>
            ))}
          </select>
        </Field>

        <Field label={t("people.guardians.relationship")}>
          <select className={inputClass} value={form.relationship} onChange={(e) => setForm({ ...form, relationship: e.target.value })}>
            <option value="FATHER">{t("people.relationship.father")}</option>
            <option value="MOTHER">{t("people.relationship.mother")}</option>
            <option value="GUARDIAN">{t("people.relationship.guardian")}</option>
            <option value="SIBLING">{t("people.relationship.sibling")}</option>
            <option value="OTHER">{t("people.relationship.other")}</option>
          </select>
        </Field>

        <div className="space-y-2 rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <label className="flex items-center gap-3 text-sm">
            <input type="checkbox" checked={form.is_primary} onChange={(e) => setForm({ ...form, is_primary: e.target.checked })} />
            {t("people.guardians.primaryContact")}
          </label>
          <label className="flex items-center gap-3 text-sm">
            <input type="checkbox" checked={form.receives_notifications} onChange={(e) => setForm({ ...form, receives_notifications: e.target.checked })} />
            {t("people.guardians.notifications")}
          </label>
          <label className="flex items-center gap-3 text-sm">
            <input type="checkbox" checked={form.can_receive_results} onChange={(e) => setForm({ ...form, can_receive_results: e.target.checked })} />
            {t("people.guardians.resultsPermission")}
          </label>
        </div>
      </form>
    </Dialog>
  );
}
