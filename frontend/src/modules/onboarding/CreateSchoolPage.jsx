import { useMemo, useState } from "react";
import { ArrowLeft, ArrowRight, Check, Loader2 } from "lucide-react";
import { Link } from "react-router-dom";
import Brand from "../../components/Brand";
import Field from "../../components/Field";
import LanguageSwitcher from "../../components/LanguageSwitcher";
import { useI18n } from "../../i18n";
import { buildTenantUrl } from "../../lib/tenant";
import api from "../../services/api";

const initialForm = {
  name: "", slug: "", acronym: "", city: "Yaoundé", country: "Cameroun", phone: "", email: "",
  language_mode: "FRENCH", education_level: "PRIMARY_SECONDARY", teaching_model: "HYBRID",
  owner_first_name: "", owner_last_name: "", owner_email: "", owner_password: "",
};

const inputClass = "w-full rounded-xl border border-slate-200 bg-white px-3.5 py-3 text-sm outline-none transition focus:border-slate-400 focus:ring-4 focus:ring-slate-100";

function slugifyLocal(value) {
  return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 80);
}

export default function CreateSchoolPage() {
  const { t } = useI18n();
  const [step, setStep] = useState(1);
  const [form, setForm] = useState(initialForm);
  const [slugTouched, setSlugTouched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState("");
  const [created, setCreated] = useState(null);

  const portalPreview = useMemo(() => buildTenantUrl(form.slug || "mon-ecole"), [form.slug]);

  const update = (key, value) => {
    const next = { ...form, [key]: value };
    if (key === "name" && !slugTouched) next.slug = slugifyLocal(value);
    setForm(next);
  };

  const submit = async () => {
    setLoading(true);
    setApiError("");
    try {
      const { data } = await api.post("/public/onboarding/schools/", form, { skipAuth: true, skipAuthRefresh: true });
      setCreated(data.school);
      setStep(4);
    } catch (error) {
      const payload = error?.response?.data;
      if (payload && typeof payload === "object") {
        const firstKey = Object.keys(payload)[0];
        const raw = payload[firstKey];
        const message = Array.isArray(raw) ? raw[0] : typeof raw === "object" ? Object.values(raw)?.[0]?.[0] : raw;
        setApiError(String(message || t("onboarding.genericError")));
      } else {
        setApiError(t("onboarding.serverError"));
      }
    } finally {
      setLoading(false);
    }
  };

  const createdPortalUrl = created ? buildTenantUrl(created.slug) : "";
  const steps = [[1, t("onboarding.schoolStep")], [2, t("onboarding.modelStep")], [3, t("onboarding.adminStep")], [4, t("onboarding.doneStep")]];

  return (
    <main className="gradient-grid min-h-screen px-4 py-8 sm:px-6">
      <div className="mx-auto max-w-5xl">
        <div className="flex items-center justify-between gap-3">
          <Link to="/" className="inline-flex items-center gap-2 text-sm text-slate-500 hover:text-slate-900"><ArrowLeft size={16} />{t("common.back")}</Link>
          <div className="flex items-center gap-2"><LanguageSwitcher /><Brand /></div>
        </div>

        <div className="mt-10 grid gap-6 lg:grid-cols-[260px_1fr]">
          <aside className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="text-xs font-medium uppercase tracking-[0.18em] text-slate-400">{t("onboarding.installation")}</div>
            <div className="mt-5 space-y-2">
              {steps.map(([number, label]) => (
                <div key={number} className={`flex items-center gap-3 rounded-xl px-3 py-3 text-sm ${step === number ? "bg-slate-950 text-white" : step > number ? "bg-emerald-50 text-emerald-700" : "text-slate-500"}`}>
                  <div className={`grid h-7 w-7 place-items-center rounded-full text-xs ${step === number ? "bg-white/15" : "bg-slate-100"}`}>{step > number ? <Check size={14} /> : number}</div>
                  {label}
                </div>
              ))}
            </div>
          </aside>

          <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft sm:p-8">
            {step === 1 && (
              <>
                <h1 className="text-2xl font-semibold tracking-tight">{t("onboarding.schoolTitle")}</h1>
                <p className="mt-2 text-sm text-slate-500">{t("onboarding.schoolText")}</p>
                <div className="mt-8 grid gap-5 sm:grid-cols-2">
                  <div className="sm:col-span-2"><Field label={t("onboarding.schoolName")}><input className={inputClass} value={form.name} onChange={(e) => update("name", e.target.value)} placeholder="Complexe Scolaire La Réussite" /></Field></div>
                  <Field label={t("onboarding.acronym")} hint={t("common.optional")}><input className={inputClass} value={form.acronym} onChange={(e) => update("acronym", e.target.value)} placeholder="CSLR" /></Field>
                  <Field label={t("onboarding.city")}><input className={inputClass} value={form.city} onChange={(e) => update("city", e.target.value)} /></Field>
                  <div className="sm:col-span-2">
                    <Field label={t("onboarding.portal")}><input className={inputClass} value={form.slug} onChange={(e) => { setSlugTouched(true); update("slug", slugifyLocal(e.target.value)); }} placeholder="la-reussite" /></Field>
                    <div className="mt-2 rounded-xl bg-slate-50 px-3.5 py-2.5 text-xs text-slate-500"><span className="font-medium text-slate-800">{portalPreview}</span></div>
                  </div>
                  <Field label={t("onboarding.phone")} hint={t("common.optional")}><input className={inputClass} value={form.phone} onChange={(e) => update("phone", e.target.value)} /></Field>
                  <Field label={t("onboarding.schoolEmail")} hint={t("common.optional")}><input type="email" className={inputClass} value={form.email} onChange={(e) => update("email", e.target.value)} /></Field>
                </div>
                <div className="mt-8 flex justify-end"><button onClick={() => setStep(2)} disabled={!form.name || !form.slug} className="inline-flex items-center gap-2 rounded-xl bg-slate-950 px-5 py-3 text-sm font-medium text-white disabled:opacity-40">{t("common.continue")}<ArrowRight size={17} /></button></div>
              </>
            )}

            {step === 2 && (
              <>
                <h1 className="text-2xl font-semibold tracking-tight">{t("onboarding.modelTitle")}</h1>
                <p className="mt-2 text-sm text-slate-500">{t("onboarding.modelText")}</p>
                <div className="mt-8 space-y-6">
                  <Field label={t("onboarding.languageSection")}><select className={inputClass} value={form.language_mode} onChange={(e) => update("language_mode", e.target.value)}><option value="FRENCH">{t("onboarding.french")}</option><option value="ENGLISH">{t("onboarding.english")}</option><option value="BILINGUAL">{t("onboarding.bilingual")}</option></select></Field>
                  <Field label={t("onboarding.coveredCycles")}><select className={inputClass} value={form.education_level} onChange={(e) => update("education_level", e.target.value)}><option value="PRIMARY">{t("onboarding.primary")}</option><option value="SECONDARY">{t("onboarding.secondary")}</option><option value="PRIMARY_SECONDARY">{t("onboarding.both")}</option></select></Field>
                  <Field label={t("onboarding.teachingModel")}><select className={inputClass} value={form.teaching_model} onChange={(e) => update("teaching_model", e.target.value)}><option value="CLASS_TEACHER">{t("onboarding.classTeacher")}</option><option value="SUBJECT_TEACHER">{t("onboarding.subjectTeachers")}</option><option value="HYBRID">{t("onboarding.hybrid")}</option></select></Field>
                </div>
                <div className="mt-8 flex justify-between"><button onClick={() => setStep(1)} className="rounded-xl px-4 py-3 text-sm font-medium text-slate-500 hover:bg-slate-50">{t("common.back")}</button><button onClick={() => setStep(3)} className="inline-flex items-center gap-2 rounded-xl bg-slate-950 px-5 py-3 text-sm font-medium text-white">{t("common.continue")}<ArrowRight size={17} /></button></div>
              </>
            )}

            {step === 3 && (
              <>
                <h1 className="text-2xl font-semibold tracking-tight">{t("onboarding.adminTitle")}</h1>
                <p className="mt-2 text-sm text-slate-500">{t("onboarding.adminText")}</p>
                <div className="mt-8 grid gap-5 sm:grid-cols-2">
                  <Field label={t("onboarding.firstName")}><input className={inputClass} value={form.owner_first_name} onChange={(e) => update("owner_first_name", e.target.value)} /></Field>
                  <Field label={t("onboarding.lastName")}><input className={inputClass} value={form.owner_last_name} onChange={(e) => update("owner_last_name", e.target.value)} /></Field>
                  <div className="sm:col-span-2"><Field label={t("onboarding.email")}><input type="email" className={inputClass} value={form.owner_email} onChange={(e) => update("owner_email", e.target.value)} /></Field></div>
                  <div className="sm:col-span-2"><Field label={t("onboarding.password")} hint={t("onboarding.passwordHint")}><input type="password" className={inputClass} value={form.owner_password} onChange={(e) => update("owner_password", e.target.value)} /></Field></div>
                </div>
                {apiError && <div className="mt-5 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{apiError}</div>}
                <div className="mt-8 flex justify-between"><button onClick={() => setStep(2)} className="rounded-xl px-4 py-3 text-sm font-medium text-slate-500 hover:bg-slate-50">{t("common.back")}</button><button onClick={submit} disabled={loading || !form.owner_first_name || !form.owner_last_name || !form.owner_email || form.owner_password.length < 8} className="inline-flex items-center gap-2 rounded-xl bg-slate-950 px-5 py-3 text-sm font-medium text-white disabled:opacity-40">{loading ? <Loader2 size={17} className="animate-spin" /> : <Check size={17} />}{t("onboarding.create")}</button></div>
              </>
            )}

            {step === 4 && created && (
              <div className="py-8 text-center">
                <div className="mx-auto grid h-16 w-16 place-items-center rounded-3xl bg-emerald-100 text-emerald-700"><Check size={30} /></div>
                <h1 className="mt-6 text-3xl font-semibold tracking-tight">{t("onboarding.doneTitle")}</h1>
                <p className="mx-auto mt-3 max-w-xl text-sm leading-6 text-slate-500"><strong className="text-slate-800">{created.name}</strong> {t("onboarding.doneText")}</p>
                <div className="mx-auto mt-7 max-w-xl rounded-2xl bg-slate-950 p-5 text-left text-white"><div className="text-xs uppercase tracking-[0.2em] text-slate-400">{t("onboarding.yourPortal")}</div><div className="mt-2 break-all font-medium">{createdPortalUrl}</div></div>
                <a href={createdPortalUrl} className="mt-7 inline-flex items-center gap-2 rounded-xl bg-slate-950 px-5 py-3 text-sm font-medium text-white">{t("onboarding.openPortal")}<ArrowRight size={17} /></a>
              </div>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}
