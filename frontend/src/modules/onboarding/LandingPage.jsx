import { ArrowRight, Building2, Layers3, ShieldCheck } from "lucide-react";
import { Link } from "react-router-dom";
import Brand from "../../components/Brand";
import LanguageSwitcher from "../../components/LanguageSwitcher";
import { useI18n } from "../../i18n";

export default function LandingPage() {
  const { t } = useI18n();
  const features = [
    { icon: Building2, title: t("landing.portalTitle"), text: t("landing.portalText") },
    { icon: Layers3, title: t("landing.levelsTitle"), text: t("landing.levelsText") },
    { icon: ShieldCheck, title: t("landing.tenantTitle"), text: t("landing.tenantText") },
  ];

  return (
    <main className="gradient-grid min-h-screen">
      <header className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-6 py-6">
        <Brand />
        <div className="flex items-center gap-2">
          <LanguageSwitcher />
          <Link to="/create-school" className="rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-medium text-white">
            {t("landing.create")}
          </Link>
        </div>
      </header>

      <section className="mx-auto grid max-w-7xl gap-12 px-6 pb-20 pt-16 lg:grid-cols-[1.15fr_.85fr] lg:items-center">
        <div>
          <span className="inline-flex rounded-full border border-slate-200 bg-white/80 px-3 py-1 text-xs font-medium text-slate-600">{t("landing.badge")}</span>
          <h1 className="mt-6 max-w-4xl text-5xl font-bold tracking-[-0.04em] text-slate-950 md:text-6xl">{t("landing.title")}</h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600">{t("landing.description")}</p>
          <Link to="/create-school" className="mt-8 inline-flex items-center gap-2 rounded-2xl bg-slate-950 px-5 py-3 font-medium text-white shadow-soft">
            {t("landing.start")} <ArrowRight size={18} />
          </Link>
        </div>

        <div className="rounded-[32px] border border-white bg-white/75 p-5 shadow-soft backdrop-blur">
          <div className="rounded-[26px] bg-slate-950 p-6 text-white">
            <p className="text-xs uppercase tracking-[.25em] text-slate-400">{t("landing.example")}</p>
            <div className="mt-6 text-2xl font-semibold">Collège Saint Joseph</div>
            <div className="mt-2 text-sm text-slate-400">saint-joseph.school.bewiseinnovation.com</div>
            <div className="mt-8 grid grid-cols-2 gap-3">
              {[t("landing.bilingual"), t("landing.both"), t("landing.hybrid"), t("landing.isolated")].map((item) => (
                <div key={item} className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm">{item}</div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto grid max-w-7xl gap-4 px-6 pb-16 md:grid-cols-3">
        {features.map(({ icon: Icon, title, text }) => (
          <div key={title} className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="grid h-11 w-11 place-items-center rounded-2xl bg-slate-100"><Icon size={20} /></div>
            <h2 className="mt-5 font-semibold">{title}</h2>
            <p className="mt-2 text-sm leading-6 text-slate-500">{text}</p>
          </div>
        ))}
      </section>
    </main>
  );
}
