import { useEffect, useMemo, useState } from "react";
import {
  BarChart3,
  BookOpen,
  BookOpenCheck,
  ClipboardCheck,
  FileText,
  GraduationCap,
  Home,
  KeyRound,
  LogOut,
  Settings,
  Users,
  UserRoundCog,
  WalletCards,
} from "lucide-react";
import Brand from "../../components/Brand";
import LanguageSwitcher from "../../components/LanguageSwitcher";
import SchoolIdentity from "../../components/SchoolIdentity";
import { useI18n } from "../../i18n";
import api, { clearAuth, storeAuth } from "../../services/api";
import AcademicWorkspace from "../academics/AcademicWorkspace";
import PeopleWorkspace from "../people/PeopleWorkspace";
import TeachingWorkspace from "../teaching/TeachingWorkspace";
import AssessmentWorkspace from "../assessments/AssessmentWorkspace";
import ReportCardsWorkspace from "../report-cards/ReportCardsWorkspace";
import FinanceWorkspace from "../finance/FinanceWorkspace";
import MembersPanel from "./MembersPanel";
import MyAccountPanel from "./MyAccountPanel";
import SchoolSettingsPanel from "./SchoolSettingsPanel";

const inputClass =
  "w-full rounded-xl border border-slate-200 bg-white px-3.5 py-3 text-sm outline-none focus:border-slate-400 focus:ring-4 focus:ring-slate-100";

const adminRoles = new Set(["OWNER", "DIRECTOR"]);
const peopleRoles = new Set(["OWNER", "DIRECTOR", "MANAGER"]);
const teachingRoles = new Set(["OWNER", "DIRECTOR", "MANAGER", "TEACHER"]);
const teachingManagementRoles = new Set(["OWNER", "DIRECTOR", "MANAGER"]);
const assessmentRoles = new Set(["OWNER", "DIRECTOR", "MANAGER", "TEACHER"]);
const assessmentManagementRoles = new Set(["OWNER", "DIRECTOR", "MANAGER"]);
const reportCardRoles = new Set(["OWNER", "DIRECTOR", "MANAGER", "TEACHER"]);
const financeRoles = new Set(["OWNER", "DIRECTOR", "MANAGER", "ACCOUNTANT"]);

export default function TenantPortal({ tenantSlug }) {
  const { t } = useI18n();
  const [dashboard, setDashboard] = useState(null);
  const [checking, setChecking] = useState(true);
  const [login, setLogin] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loadingLogin, setLoadingLogin] = useState(false);
  const [section, setSection] = useState("dashboard");

  const loadDashboard = async () => {
    try {
      const { data } = await api.get("/tenant/dashboard/");
      setDashboard(data);
    } catch {
      setDashboard(null);
    } finally {
      setChecking(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, [tenantSlug]);

  useEffect(() => {
    const handleExpiredSession = () => {
      setDashboard(null);
      setChecking(false);
      setError(t("auth.expired"));
    };

    window.addEventListener("be-wise-auth-expired", handleExpiredSession);
    return () => window.removeEventListener("be-wise-auth-expired", handleExpiredSession);
  }, [t]);

  const submitLogin = async (event) => {
    event.preventDefault();
    setLoadingLogin(true);
    setError("");

    try {
      const { data } = await api.post("/auth/login/", login, {
        skipAuth: true,
        skipAuthRefresh: true,
      });
      storeAuth(data);
      await loadDashboard();
    } catch (err) {
      const detail =
        err?.response?.data?.detail ||
        err?.response?.data?.non_field_errors?.[0] ||
        "Connexion impossible.";
      setError(detail);
    } finally {
      setLoadingLogin(false);
    }
  };

  const canManage = dashboard ? adminRoles.has(dashboard.membership.role) : false;
  const canManagePeople = dashboard ? peopleRoles.has(dashboard.membership.role) : false;
  const canSeeTeaching = dashboard ? teachingRoles.has(dashboard.membership.role) : false;
  const canManageTeaching = dashboard ? teachingManagementRoles.has(dashboard.membership.role) : false;
  const canManageTeacherAccounts = dashboard ? adminRoles.has(dashboard.membership.role) : false;
  const canSeeAssessments = dashboard ? assessmentRoles.has(dashboard.membership.role) : false;
  const canManageAssessments = dashboard ? assessmentManagementRoles.has(dashboard.membership.role) : false;
  const isAssessmentDirection = dashboard ? adminRoles.has(dashboard.membership.role) : false;
  const canSeeReportCards = dashboard ? reportCardRoles.has(dashboard.membership.role) : false;
  const canSeeFinance = dashboard ? financeRoles.has(dashboard.membership.role) : false;
  const portalAddress = useMemo(() => window.location.host, [tenantSlug]);

  if (checking) {
    return (
      <div className="grid min-h-screen place-items-center bg-slate-50 text-sm text-slate-500">
        {t("common.loading")}
      </div>
    );
  }

  if (!dashboard) {
    return (
      <main className="gradient-grid grid min-h-screen place-items-center px-4 py-10">
        <div className="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-7 shadow-soft">
          <div className="flex items-center justify-between gap-3">
            <Brand />
            <LanguageSwitcher />
          </div>

          <div className="mt-8">
            <div className="text-xs font-medium uppercase tracking-[0.18em] text-slate-400">{portalAddress}</div>
            <h1 className="mt-2 text-2xl font-semibold tracking-tight">{t("auth.title")}</h1>
            <p className="mt-2 text-sm text-slate-500">{t("auth.subtitle")}</p>
          </div>

          <form onSubmit={submitLogin} className="mt-7 space-y-4">
            <input type="email" placeholder={t("auth.email")} className={inputClass} value={login.email} onChange={(e) => setLogin({ ...login, email: e.target.value })} />
            <input type="password" placeholder={t("auth.password")} className={inputClass} value={login.password} onChange={(e) => setLogin({ ...login, password: e.target.value })} />

            {error && <div className="rounded-xl bg-rose-50 px-3.5 py-3 text-sm text-rose-700">{error}</div>}

            <button disabled={loadingLogin} className="w-full rounded-xl bg-slate-950 px-4 py-3 text-sm font-medium text-white disabled:opacity-50">
              {loadingLogin ? t("auth.logging") : t("auth.login")}
            </button>
          </form>
        </div>
      </main>
    );
  }

  const cards = [
    { label: t("dashboard.years"), value: dashboard.foundation.academic_years, icon: BookOpen },
    { label: t("dashboard.classes"), value: dashboard.foundation.classes, icon: GraduationCap },
    { label: t("dashboard.students"), value: dashboard.foundation.students, icon: Users },
    { label: t("dashboard.teachers"), value: dashboard.foundation.teachers, icon: UserRoundCog },
  ];

  const nav = [
    { id: "dashboard", label: t("nav.dashboard"), icon: Home },
    { id: "academics", label: t("nav.academics"), icon: GraduationCap },
    ...(canSeeTeaching ? [{ id: "teaching", label: t("nav.teaching"), icon: BookOpenCheck }] : []),
    ...(canSeeAssessments ? [{ id: "assessments", label: t("nav.assessments"), icon: ClipboardCheck }] : []),
    ...(canSeeReportCards ? [{ id: "reportCards", label: t("nav.reportCards"), icon: FileText }] : []),
    ...(canSeeFinance ? [{ id: "finance", label: t("nav.finance"), icon: WalletCards }] : []),
    ...(canManagePeople ? [{ id: "people", label: t("nav.people"), icon: Users }] : []),
    { id: "settings", label: t("nav.school"), icon: Settings },
    { id: "account", label: t("nav.account"), icon: KeyRound },
    ...(canManage ? [{ id: "members", label: t("nav.team"), icon: Users }] : []),
  ];

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-5 px-6 py-4">
          <SchoolIdentity school={dashboard.school} />
          <div className="flex items-center gap-2">
            <LanguageSwitcher />
            <button
              onClick={() => {
                clearAuth();
                window.location.reload();
              }}
              className="inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm text-slate-500 hover:bg-slate-100 hover:text-slate-900"
            >
              <LogOut size={16} />
              <span className="hidden sm:inline">{t("common.logout")}</span>
            </button>
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl gap-6 px-6 py-7 lg:grid-cols-[220px_1fr]">
        <aside>
          <div className="sticky top-6 space-y-1 rounded-2xl border border-slate-200 bg-white p-2">
            {nav.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setSection(id)}
                className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm transition ${
                  section === id
                    ? "bg-slate-950 text-white"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-950"
                }`}
              >
                <Icon size={17} />
                {label}
              </button>
            ))}
          </div>
        </aside>

        <main className="min-w-0">
          {section === "dashboard" && (
            <>
              <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
                <div>
                  <div className="text-xs font-medium uppercase tracking-[0.18em] text-slate-400">{dashboard.membership.role_label}</div>
                  <h1 className="mt-2 text-3xl font-semibold tracking-tight">{dashboard.school.name}</h1>
                  <p className="mt-2 text-sm text-slate-500">{portalAddress}</p>
                </div>
                <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{t("dashboard.foundation")}</div>
              </div>

              <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {cards.map(({ label, value, icon: Icon }) => (
                  <div key={label} className="rounded-2xl border border-slate-200 bg-white p-5">
                    <div className="flex items-center justify-between">
                      <div className="text-sm text-slate-500">{label}</div>
                      <Icon size={18} className="text-slate-400" />
                    </div>
                    <div className="mt-5 text-3xl font-semibold">{value}</div>
                  </div>
                ))}
              </div>

              <div className="mt-6 grid gap-4 lg:grid-cols-[1.4fr_.6fr]">
                <section className="rounded-3xl border border-slate-200 bg-white p-6">
                  <div className="flex items-center gap-3">
                    <div className="grid h-10 w-10 place-items-center rounded-xl bg-slate-100"><BarChart3 size={18} /></div>
                    <div>
                      <h2 className="font-semibold">{t("dashboard.next")}</h2>
                      <p className="text-sm text-slate-500">{t("dashboard.academics")}</p>
                    </div>
                  </div>
                </section>

                <section className="rounded-3xl border border-slate-200 bg-white p-6">
                  <h2 className="font-semibold">{t("dashboard.configuration")}</h2>
                  <dl className="mt-6 space-y-4 text-sm">
                    <div><dt className="text-slate-400">{t("dashboard.language")}</dt><dd className="mt-1 font-medium">{dashboard.school.language_mode}</dd></div>
                    <div><dt className="text-slate-400">{t("dashboard.cycles")}</dt><dd className="mt-1 font-medium">{dashboard.school.education_level}</dd></div>
                    <div><dt className="text-slate-400">{t("dashboard.activeTeam")}</dt><dd className="mt-1 font-medium">{t("dashboard.members", { count: dashboard.foundation.members })}</dd></div>
                  </dl>
                </section>
              </div>
            </>
          )}

          {section === "academics" && (
            <AcademicWorkspace
              canManage={canManage}
              onCountsChanged={(counts) =>
                setDashboard((current) => ({
                  ...current,
                  foundation: { ...current.foundation, ...counts },
                }))
              }
            />
          )}

          {section === "people" && canManagePeople && (
            <PeopleWorkspace
              onCountsChanged={(counts) =>
                setDashboard((current) => ({
                  ...current,
                  foundation: {
                    ...current.foundation,
                    ...counts,
                  },
                }))
              }
            />
          )}

          {section === "teaching" && canSeeTeaching && (
            <TeachingWorkspace
              role={dashboard.membership.role}
              canManage={canManageTeaching}
              canManageAccounts={canManageTeacherAccounts}
            />
          )}

          {section === "assessments" && canSeeAssessments && (
            <AssessmentWorkspace
              role={dashboard.membership.role}
              canManage={canManageAssessments}
              isDirection={isAssessmentDirection}
            />
          )}

          {section === "reportCards" && canSeeReportCards && (
            <ReportCardsWorkspace
              role={dashboard.membership.role}
              isDirection={adminRoles.has(dashboard.membership.role)}
            />
          )}

          {section === "finance" && canSeeFinance && (
            <FinanceWorkspace
              role={dashboard.membership.role}
            />
          )}

          {section === "settings" && (
            <SchoolSettingsPanel
              school={dashboard.school}
              canManage={canManage}
              onUpdated={(school) => setDashboard((current) => ({ ...current, school }))}
            />
          )}

          {section === "account" && (
            <MyAccountPanel user={dashboard.user} />
          )}

          {section === "members" && canManage && <MembersPanel />}
        </main>
      </div>
    </div>
  );
}
