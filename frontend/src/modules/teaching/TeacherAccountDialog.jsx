import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

import Dialog from "../../components/Dialog";
import Field from "../../components/Field";
import { useI18n } from "../../i18n";
import api from "../../services/api";

const inputClass =
  "w-full rounded-xl border border-slate-200 bg-white px-3.5 py-3 text-sm outline-none focus:border-slate-400 focus:ring-4 focus:ring-slate-100";

export default function TeacherAccountDialog({ open, teacher, onClose, onSaved }) {
  const { t } = useI18n();
  const [form, setForm] = useState({ email: "", password: "" });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open || !teacher) return;
    setError("");
    setForm({
      email: teacher.email || "",
      password: "",
    });
  }, [open, teacher]);

  if (!teacher) return null;

  const submit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError("");

    try {
      const payload = { email: form.email };
      if (form.password) payload.password = form.password;

      await api.post(`/teaching/teachers/${teacher.id}/account/`, payload);
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
            : payload?.detail || t("teaching.errors.account")
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={t("teaching.accounts.dialogTitle")}
      description={t("teaching.accounts.dialogHelp", {
        name: `${teacher.last_name} ${teacher.first_name}`,
      })}
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
            form="teacher-account-form"
            disabled={saving}
            className="inline-flex items-center gap-2 rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-medium text-white disabled:opacity-50"
          >
            {saving && <Loader2 size={16} className="animate-spin" />}
            {t("teaching.accounts.createOrLink")}
          </button>
        </div>
      }
    >
      <form id="teacher-account-form" onSubmit={submit} className="space-y-4">
        {error && (
          <div className="rounded-xl bg-rose-50 px-3.5 py-3 text-sm text-rose-700">
            {error}
          </div>
        )}

        <Field label={t("auth.email")}>
          <input
            required
            type="email"
            className={inputClass}
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
          />
        </Field>

        <Field
          label={t("teaching.accounts.initialPassword")}
          hint={t("teaching.accounts.passwordHint")}
        >
          <input
            type="password"
            minLength={8}
            className={inputClass}
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
          />
        </Field>

        <div className="rounded-2xl border border-blue-100 bg-blue-50 p-4 text-xs leading-5 text-blue-800">
          {t("teaching.accounts.existingAccountHelp")}
        </div>
      </form>
    </Dialog>
  );
}
