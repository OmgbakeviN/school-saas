import { useState } from "react";
import { CheckCircle2, KeyRound, Loader2 } from "lucide-react";

import Field from "../../components/Field";
import { useI18n } from "../../i18n";
import api from "../../services/api";

const inputClass =
  "w-full rounded-xl border border-slate-200 bg-white px-3.5 py-3 text-sm outline-none focus:border-slate-400 focus:ring-4 focus:ring-slate-100";

export default function MyAccountPanel({ user }) {
  const { t } = useI18n();
  const [form, setForm] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  });
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const submit = async (event) => {
    event.preventDefault();
    setMessage("");
    setError("");

    if (form.new_password !== form.confirm_password) {
      setError(t("account.passwordMismatch"));
      return;
    }

    setSaving(true);
    try {
      await api.post("/auth/change-password/", {
        current_password: form.current_password,
        new_password: form.new_password,
      });
      setForm({
        current_password: "",
        new_password: "",
        confirm_password: "",
      });
      setMessage(t("account.passwordChanged"));
    } catch (err) {
      const payload = err?.response?.data;
      const first = payload && Object.values(payload)[0];
      setError(
        Array.isArray(first)
          ? String(first[0])
          : payload?.detail || t("account.passwordError")
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-5">
      <div>
        <div className="text-xs font-medium uppercase tracking-[0.18em] text-slate-400">
          {t("account.step")}
        </div>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight">
          {t("account.title")}
        </h1>
        <p className="mt-2 text-sm text-slate-500">
          {t("account.description")}
        </p>
      </div>

      <section className="rounded-3xl border border-slate-200 bg-white p-6">
        <div className="flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-xl bg-slate-100">
            <KeyRound size={18} />
          </div>
          <div>
            <h2 className="font-semibold">{t("account.security")}</h2>
            <p className="text-sm text-slate-500">{user?.email}</p>
          </div>
        </div>

        <form onSubmit={submit} className="mt-6 max-w-xl space-y-4">
          <Field label={t("account.currentPassword")}>
            <input
              required
              type="password"
              className={inputClass}
              value={form.current_password}
              onChange={(e) =>
                setForm({ ...form, current_password: e.target.value })
              }
            />
          </Field>

          <Field label={t("account.newPassword")} hint={t("account.passwordHint")}>
            <input
              required
              minLength={8}
              type="password"
              className={inputClass}
              value={form.new_password}
              onChange={(e) => setForm({ ...form, new_password: e.target.value })}
            />
          </Field>

          <Field label={t("account.confirmPassword")}>
            <input
              required
              minLength={8}
              type="password"
              className={inputClass}
              value={form.confirm_password}
              onChange={(e) =>
                setForm({ ...form, confirm_password: e.target.value })
              }
            />
          </Field>

          {error && (
            <div className="rounded-xl bg-rose-50 px-3.5 py-3 text-sm text-rose-700">
              {error}
            </div>
          )}

          {message && (
            <div className="flex items-center gap-2 rounded-xl bg-emerald-50 px-3.5 py-3 text-sm text-emerald-800">
              <CheckCircle2 size={16} />
              {message}
            </div>
          )}

          <button
            disabled={saving}
            className="inline-flex items-center gap-2 rounded-xl bg-slate-950 px-5 py-3 text-sm font-medium text-white disabled:opacity-50"
          >
            {saving && <Loader2 size={16} className="animate-spin" />}
            {t("account.changePassword")}
          </button>
        </form>
      </section>
    </div>
  );
}
