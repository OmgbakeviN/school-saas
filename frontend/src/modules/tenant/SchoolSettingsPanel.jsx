import { useEffect, useState } from "react";
import { Check, ImagePlus, Loader2, Palette } from "lucide-react";
import Field from "../../components/Field";
import { useI18n } from "../../i18n";
import api from "../../services/api";

const inputClass =
  "w-full rounded-xl border border-slate-200 bg-white px-3.5 py-3 text-sm outline-none focus:border-slate-400 focus:ring-4 focus:ring-slate-100";

export default function SchoolSettingsPanel({ school, canManage, onUpdated }) {
  const { t } = useI18n();
  const [form, setForm] = useState(school);
  const [logo, setLogo] = useState(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => setForm(school), [school]);

  const update = (key, value) => setForm((current) => ({ ...current, [key]: value }));

  const save = async (event) => {
    event.preventDefault();
    setSaving(true);
    setMessage("");

    try {
      const data = new FormData();
      ["name", "acronym", "city", "country", "phone", "email", "motto", "primary_color", "secondary_color", "language_mode", "education_level", "teaching_model"]
        .forEach((key) => data.append(key, form[key] ?? ""));

      if (logo) data.append("logo", logo);

      const response = await api.patch("/tenant/settings/", data);
      onUpdated(response.data);
      setLogo(null);
      setMessage(t("settings.saved"));
    } catch (error) {
      setMessage(error?.response?.data?.detail || t("settings.saveError"));
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={save} className="space-y-6">
      {!canManage && (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">{t("settings.readOnly")}</div>
      )}

      <section className="rounded-3xl border border-slate-200 bg-white p-6">
        <div className="flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-xl bg-slate-100"><ImagePlus size={18} /></div>
          <div>
            <h2 className="font-semibold">{t("settings.identityTitle")}</h2>
            <p className="text-sm text-slate-500">{t("settings.identityText")}</p>
          </div>
        </div>

        <div className="mt-6 grid gap-5 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <Field label={t("settings.logo")} hint={t("settings.logoHint")}>
              <input disabled={!canManage} type="file" accept="image/png,image/jpeg,image/webp" onChange={(e) => setLogo(e.target.files?.[0] || null)} className="block w-full rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-5 text-sm disabled:opacity-60" />
            </Field>
          </div>

          <Field label={t("settings.name")}><input disabled={!canManage} className={inputClass} value={form.name || ""} onChange={(e) => update("name", e.target.value)} /></Field>
          <Field label={t("settings.acronym")}><input disabled={!canManage} className={inputClass} value={form.acronym || ""} onChange={(e) => update("acronym", e.target.value)} /></Field>

          <div className="sm:col-span-2">
            <Field label={t("settings.motto")}><input disabled={!canManage} className={inputClass} value={form.motto || ""} onChange={(e) => update("motto", e.target.value)} placeholder={t("settings.mottoPlaceholder")} /></Field>
          </div>

          <Field label={t("settings.city")}><input disabled={!canManage} className={inputClass} value={form.city || ""} onChange={(e) => update("city", e.target.value)} /></Field>
          <Field label={t("settings.country")}><input disabled={!canManage} className={inputClass} value={form.country || ""} onChange={(e) => update("country", e.target.value)} /></Field>
          <Field label={t("settings.phone")}><input disabled={!canManage} className={inputClass} value={form.phone || ""} onChange={(e) => update("phone", e.target.value)} /></Field>
          <Field label={t("settings.email")}><input disabled={!canManage} type="email" className={inputClass} value={form.email || ""} onChange={(e) => update("email", e.target.value)} /></Field>
        </div>
      </section>

      <section className="rounded-3xl border border-slate-200 bg-white p-6">
        <div className="flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-xl bg-slate-100"><Palette size={18} /></div>
          <div>
            <h2 className="font-semibold">{t("settings.brandingTitle")}</h2>
            <p className="text-sm text-slate-500">{t("settings.brandingText")}</p>
          </div>
        </div>

        <div className="mt-6 grid gap-5 sm:grid-cols-2">
          <Field label={t("settings.primaryColor")}>
            <div className="flex gap-2"><input disabled={!canManage} type="color" className="h-12 w-14 rounded-xl border border-slate-200 bg-white p-1" value={form.primary_color || "#0f172a"} onChange={(e) => update("primary_color", e.target.value)} /><input disabled={!canManage} className={inputClass} value={form.primary_color || ""} onChange={(e) => update("primary_color", e.target.value)} /></div>
          </Field>
          <Field label={t("settings.secondaryColor")}>
            <div className="flex gap-2"><input disabled={!canManage} type="color" className="h-12 w-14 rounded-xl border border-slate-200 bg-white p-1" value={form.secondary_color || "#2563eb"} onChange={(e) => update("secondary_color", e.target.value)} /><input disabled={!canManage} className={inputClass} value={form.secondary_color || ""} onChange={(e) => update("secondary_color", e.target.value)} /></div>
          </Field>

          <Field label={t("settings.language")}>
            <select disabled={!canManage} className={inputClass} value={form.language_mode || "FRENCH"} onChange={(e) => update("language_mode", e.target.value)}>
              <option value="FRENCH">{t("settings.french")}</option><option value="ENGLISH">{t("settings.english")}</option><option value="BILINGUAL">{t("settings.bilingual")}</option>
            </select>
          </Field>

          <Field label={t("settings.cycles")}>
            <select disabled={!canManage} className={inputClass} value={form.education_level || "PRIMARY_SECONDARY"} onChange={(e) => update("education_level", e.target.value)}>
              <option value="PRIMARY">{t("settings.primary")}</option><option value="SECONDARY">{t("settings.secondary")}</option><option value="PRIMARY_SECONDARY">{t("settings.both")}</option>
            </select>
          </Field>

          <div className="sm:col-span-2">
            <Field label={t("settings.teachingModel")}>
              <select disabled={!canManage} className={inputClass} value={form.teaching_model || "HYBRID"} onChange={(e) => update("teaching_model", e.target.value)}>
                <option value="CLASS_TEACHER">{t("settings.classTeacher")}</option><option value="SUBJECT_TEACHER">{t("settings.subjectTeacher")}</option><option value="HYBRID">{t("settings.hybrid")}</option>
              </select>
            </Field>
          </div>
        </div>
      </section>

      {canManage && (
        <div className="flex items-center justify-end gap-4">
          {message && <span className="text-sm text-slate-500">{message}</span>}
          <button disabled={saving} className="inline-flex items-center gap-2 rounded-xl bg-slate-950 px-5 py-3 text-sm font-medium text-white disabled:opacity-50">
            {saving ? <Loader2 className="animate-spin" size={17} /> : <Check size={17} />}
            {t("common.save")}
          </button>
        </div>
      )}
    </form>
  );
}
