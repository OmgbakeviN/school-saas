import { useEffect, useState } from "react";
import { Loader2, Save } from "lucide-react";

import Dialog from "../../components/Dialog";
import Field from "../../components/Field";
import { useI18n } from "../../i18n";
import api from "../../services/api";

const inputClass =
  "w-full rounded-xl border border-slate-200 bg-white px-3.5 py-3 text-sm outline-none focus:border-slate-400 focus:ring-4 focus:ring-slate-100";

const emptyForm = {
  first_name: "",
  last_name: "",
  phone: "",
  alternate_phone: "",
  email: "",
  occupation: "",
  address: "",
  preferred_language: "FR",
  is_active: true,
};

function parseError(error, fallback) {
  const payload = error?.response?.data;
  if (!payload) return fallback;
  if (payload.detail) return String(payload.detail);
  const first = Object.values(payload)[0];
  if (Array.isArray(first)) return String(first[0]);
  return fallback;
}

export default function GuardianDialog({
  open,
  guardian,
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
      guardian
        ? {
            first_name: guardian.first_name || "",
            last_name: guardian.last_name || "",
            phone: guardian.phone || "",
            alternate_phone: guardian.alternate_phone || "",
            email: guardian.email || "",
            occupation: guardian.occupation || "",
            address: guardian.address || "",
            preferred_language: guardian.preferred_language || "FR",
            is_active: guardian.is_active !== false,
          }
        : emptyForm
    );
    setError("");
  }, [open, guardian]);

  const submit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError("");

    try {
      const { data } = guardian
        ? await api.patch(`/people/guardians/${guardian.id}/`, form)
        : await api.post("/people/guardians/", form);

      await onSaved?.(data);
      onClose?.();
    } catch (err) {
      setError(parseError(err, t("people.errors.saveGuardian")));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={() => !saving && onClose?.()}
      title={guardian ? t("people.guardians.editTitle") : t("people.guardians.createTitle")}
      description={t("people.guardians.dialogHelp")}
      maxWidth="max-w-2xl"
      footer={
        <div className="flex justify-end gap-2">
          <button type="button" disabled={saving} onClick={onClose} className="rounded-xl px-4 py-2.5 text-sm font-medium text-slate-600 hover:bg-white">
            {t("common.cancel")}
          </button>
          <button type="submit" form="guardian-form" disabled={saving} className="inline-flex items-center gap-2 rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-medium text-white disabled:opacity-50">
            {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
            {t("common.save")}
          </button>
        </div>
      }
    >
      <form id="guardian-form" onSubmit={submit} className="space-y-4">
        {error && <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>}

        <div className="grid gap-4 sm:grid-cols-2">
          <Field label={t("people.fields.firstName")}>
            <input required className={inputClass} value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} />
          </Field>
          <Field label={t("people.fields.lastName")}>
            <input required className={inputClass} value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} />
          </Field>
          <Field label={t("people.fields.phone")}>
            <input required className={inputClass} value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          </Field>
          <Field label={t("people.guardians.alternatePhone")} hint={t("common.optional")}>
            <input className={inputClass} value={form.alternate_phone} onChange={(e) => setForm({ ...form, alternate_phone: e.target.value })} />
          </Field>
          <Field label={t("people.fields.email")} hint={t("common.optional")}>
            <input type="email" className={inputClass} value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          </Field>
          <Field label={t("people.guardians.occupation")} hint={t("common.optional")}>
            <input className={inputClass} value={form.occupation} onChange={(e) => setForm({ ...form, occupation: e.target.value })} />
          </Field>
          <Field label={t("people.guardians.preferredLanguage")}>
            <select className={inputClass} value={form.preferred_language} onChange={(e) => setForm({ ...form, preferred_language: e.target.value })}>
              <option value="FR">{t("common.french")}</option>
              <option value="EN">{t("common.english")}</option>
            </select>
          </Field>
          <Field label={t("people.fields.address")} hint={t("common.optional")}>
            <input className={inputClass} value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
          </Field>
          <div className="sm:col-span-2">
            <label className="flex items-center gap-3 rounded-xl border border-slate-200 px-3.5 py-3 text-sm">
              <input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} />
              {t("people.guardians.active")}
            </label>
          </div>
        </div>
      </form>
    </Dialog>
  );
}
