import { useI18n } from "../i18n";

export default function LanguageSwitcher() {
  const { language, setLanguage, t } = useI18n();

  return (
    <div className="inline-flex rounded-xl border border-slate-200 bg-white p-1">
      <button
        type="button"
        onClick={() => setLanguage("fr")}
        title={t("common.french")}
        className={`rounded-lg px-2.5 py-1.5 text-xs font-semibold ${language === "fr" ? "bg-slate-950 text-white" : "text-slate-500 hover:bg-slate-50"}`}
      >
        FR
      </button>
      <button
        type="button"
        onClick={() => setLanguage("en")}
        title={t("common.english")}
        className={`rounded-lg px-2.5 py-1.5 text-xs font-semibold ${language === "en" ? "bg-slate-950 text-white" : "text-slate-500 hover:bg-slate-50"}`}
      >
        EN
      </button>
    </div>
  );
}
