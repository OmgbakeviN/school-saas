import { useEffect, useMemo, useState } from "react";
import {
  BookOpenCheck,
  ClipboardCheck,
  FileText,
  GraduationCap,
  Home,
  KeyRound,
  LogOut,
  Menu,
  Settings,
  Users,
  WalletCards,
  X,
} from "lucide-react";
import Brand from "../../components/Brand";
import LanguageSwitcher from "../../components/LanguageSwitcher";
import SchoolIdentity from "../../components/SchoolIdentity";
import { useI18n } from "../../i18n";
import { createSchoolTheme } from "../../lib/schoolTheme";
import api, { clearAuth, storeAuth } from "../../services/api";
import AcademicWorkspace from "../academics/AcademicWorkspace";
import PeopleWorkspace from "../people/PeopleWorkspace";
import TeachingWorkspace from "../teaching/TeachingWorkspace";
import AssessmentWorkspace from "../assessments/AssessmentWorkspace";
import ReportCardsWorkspace from "../report-cards/ReportCardsWorkspace";
import FinanceWorkspace from "../finance/FinanceWorkspace";
import DashboardAnalytics from "./DashboardAnalytics";
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

export default function TenantPortal({ tenantSlug, initialSchool = null }) {
  const { t } = useI18n();
  const [dashboard, setDashboard] = useState(null);
  const [publicSchool, setPublicSchool] = useState(initialSchool);
  const [checking, setChecking] = useState(true);
  const [login, setLogin] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loadingLogin, setLoadingLogin] = useState(false);
  const [section, setSection] = useState("dashboard");
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  const loadDashboard = async () => {
    try {
      const { data } = await api.get("/tenant/dashboard/");
      setDashboard(data);
      setPublicSchool(data.school);
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
    if (initialSchool) {
      setPublicSchool(initialSchool);
    }
  }, [initialSchool]);

  useEffect(() => {
    const handleExpiredSession = () => {
      setDashboard(null);
      setChecking(false);
      setMobileNavOpen(false);
      setError(t("auth.expired"));
    };

    window.addEventListener("be-wise-auth-expired", handleExpiredSession);
    return () =>
      window.removeEventListener("be-wise-auth-expired", handleExpiredSession);
  }, [t]);

  useEffect(() => {
    if (!mobileNavOpen) return undefined;

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const handleEscape = (event) => {
      if (event.key === "Escape") setMobileNavOpen(false);
    };

    window.addEventListener("keydown", handleEscape);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleEscape);
    };
  }, [mobileNavOpen]);

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

  const activeSchool = dashboard?.school || publicSchool;
  const themeStyle = useMemo(
    () => createSchoolTheme(activeSchool),
    [activeSchool]
  );

  useEffect(() => {
    const root = document.documentElement;
    const previous = {};

    Object.entries(themeStyle).forEach(([key, value]) => {
      previous[key] = root.style.getPropertyValue(key);
      root.style.setProperty(key, value);
    });

    return () => {
      Object.entries(previous).forEach(([key, value]) => {
        if (value) root.style.setProperty(key, value);
        else root.style.removeProperty(key);
      });
    };
  }, [themeStyle]);

  const portalAddress = useMemo(() => window.location.host, [tenantSlug]);

  if (checking) {
    return (
      <div
        className="tenant-theme grid min-h-screen place-items-center bg-slate-50 text-sm text-slate-500"
        style={themeStyle}
      >
        <div className="flex flex-col items-center gap-4">
          {activeSchool ? (
            <SchoolIdentity school={activeSchool} compact />
          ) : (
            <Brand />
          )}
          <div>{t("common.loading")}</div>
        </div>
      </div>
    );
  }

  if (!dashboard) {
    return (
      <main
        className="tenant-theme tenant-login-shell gradient-grid relative grid min-h-screen place-items-center overflow-hidden px-3 py-5 sm:px-4 sm:py-10"
        style={themeStyle}
      >
        <div className="pointer-events-none absolute inset-x-0 top-0 h-1.5 tenant-brand-strip" />

        <div className="tenant-login-card w-full max-w-md overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-soft">
          <div className="tenant-primary-soft border-b border-slate-100 px-5 py-4 sm:px-7 sm:py-5">
            <div className="flex min-w-0 items-center justify-between gap-3">
              {activeSchool ? (
                <div className="min-w-0 flex-1">
                  <SchoolIdentity school={activeSchool} />
                </div>
              ) : (
                <Brand />
              )}
              <div className="shrink-0">
                <LanguageSwitcher />
              </div>
            </div>
          </div>

          <div className="p-5 sm:p-7">
            <div className="text-xs font-medium uppercase tracking-[0.18em] text-slate-400 break-all">
              {portalAddress}
            </div>
            <h1 className="mt-2 text-2xl font-semibold tracking-tight">
              {t("auth.title")}
            </h1>
            <p className="mt-2 text-sm leading-6 text-slate-500">
              {t("auth.subtitle")}
            </p>

            <form onSubmit={submitLogin} className="mt-7 space-y-4">
              <input
                type="email"
                placeholder={t("auth.email")}
                className={inputClass}
                value={login.email}
                onChange={(event) =>
                  setLogin({ ...login, email: event.target.value })
                }
              />
              <input
                type="password"
                placeholder={t("auth.password")}
                className={inputClass}
                value={login.password}
                onChange={(event) =>
                  setLogin({ ...login, password: event.target.value })
                }
              />

              {error && (
                <div className="rounded-xl bg-rose-50 px-3.5 py-3 text-sm text-rose-700">
                  {error}
                </div>
              )}

              <button
                disabled={loadingLogin}
                className="w-full rounded-xl bg-slate-950 px-4 py-3 text-sm font-medium text-white shadow-sm transition hover:opacity-95 disabled:opacity-50"
              >
                {loadingLogin ? t("auth.logging") : t("auth.login")}
              </button>
            </form>
          </div>
        </div>
      </main>
    );
  }

  const canManage = adminRoles.has(dashboard.membership.role);
  const canManagePeople = peopleRoles.has(dashboard.membership.role);
  const canSeeTeaching = teachingRoles.has(dashboard.membership.role);
  const canManageTeaching = teachingManagementRoles.has(
    dashboard.membership.role
  );
  const canManageTeacherAccounts = adminRoles.has(dashboard.membership.role);
  const canSeeAssessments = assessmentRoles.has(dashboard.membership.role);
  const canManageAssessments = assessmentManagementRoles.has(
    dashboard.membership.role
  );
  const isAssessmentDirection = adminRoles.has(dashboard.membership.role);
  const canSeeReportCards = reportCardRoles.has(dashboard.membership.role);
  const canSeeFinance = financeRoles.has(dashboard.membership.role);

  const nav = [
    { id: "dashboard", label: t("nav.dashboard"), icon: Home },
    { id: "academics", label: t("nav.academics"), icon: GraduationCap },
    ...(canSeeTeaching
      ? [{ id: "teaching", label: t("nav.teaching"), icon: BookOpenCheck }]
      : []),
    ...(canSeeAssessments
      ? [
          {
            id: "assessments",
            label: t("nav.assessments"),
            icon: ClipboardCheck,
          },
        ]
      : []),
    ...(canSeeReportCards
      ? [
          {
            id: "reportCards",
            label: t("nav.reportCards"),
            icon: FileText,
          },
        ]
      : []),
    ...(canSeeFinance
      ? [{ id: "finance", label: t("nav.finance"), icon: WalletCards }]
      : []),
    ...(canManagePeople
      ? [{ id: "people", label: t("nav.people"), icon: Users }]
      : []),
    { id: "settings", label: t("nav.school"), icon: Settings },
    { id: "account", label: t("nav.account"), icon: KeyRound },
    ...(canManage
      ? [{ id: "members", label: t("nav.team"), icon: Users }]
      : []),
  ];

  const logout = () => {
    clearAuth();
    window.location.reload();
  };

  const selectSection = (id) => {
    setSection(id);
    setMobileNavOpen(false);

    if (id === "dashboard") {
      loadDashboard();
    }

    window.requestAnimationFrame(() => {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  };

  const navButtons = nav.map(({ id, label, icon: Icon }) => (
    <button
      key={id}
      type="button"
      onClick={() => selectSection(id)}
      aria-current={section === id ? "page" : undefined}
      className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm transition ${
        section === id
          ? "tenant-primary-bg tenant-nav-active shadow-sm"
          : "text-slate-600 hover:bg-slate-50 hover:text-slate-950"
      }`}
    >
      <Icon size={17} className="shrink-0" />
      <span className="min-w-0 leading-5">{label}</span>
    </button>
  ));

  return (
    <div
      className="tenant-theme tenant-app-shell min-h-screen bg-slate-50"
      style={themeStyle}
    >
      <div className="tenant-brand-strip h-1" />

      <header className="tenant-header sticky top-0 z-40 border-b border-slate-200/80 bg-white/90 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-3 px-3 py-3 sm:px-6 sm:py-4">
          <div className="flex min-w-0 flex-1 items-center gap-2.5">
            <button
              type="button"
              onClick={() => setMobileNavOpen(true)}
              className="grid h-10 w-10 shrink-0 place-items-center rounded-xl border border-slate-200 bg-white text-slate-700 shadow-sm transition hover:bg-slate-50 lg:hidden"
              aria-label="Ouvrir le menu"
              aria-expanded={mobileNavOpen}
            >
              <Menu size={20} />
            </button>

            <div className="min-w-0 flex-1 sm:hidden">
              <SchoolIdentity school={dashboard.school} compact />
            </div>
            <div className="hidden min-w-0 flex-1 sm:block">
              <SchoolIdentity school={dashboard.school} />
            </div>
          </div>

          <div className="flex shrink-0 items-center gap-1 sm:gap-2">
            <div className="hidden sm:block">
              <LanguageSwitcher />
            </div>
            <button
              type="button"
              onClick={logout}
              className="inline-flex h-10 items-center gap-2 rounded-xl px-2.5 text-sm text-slate-500 transition hover:bg-slate-100 hover:text-slate-900 sm:px-3"
              title={t("common.logout")}
            >
              <LogOut size={17} />
              <span className="hidden md:inline">{t("common.logout")}</span>
            </button>
          </div>
        </div>
      </header>

      {mobileNavOpen && (
        <div
          className="tenant-mobile-nav-overlay fixed inset-0 z-[70] lg:hidden"
          role="dialog"
          aria-modal="true"
          aria-label="Navigation principale"
        >
          <button
            type="button"
            className="absolute inset-0 bg-slate-950/45 backdrop-blur-[2px]"
            aria-label="Fermer le menu"
            onClick={() => setMobileNavOpen(false)}
          />

          <aside className="tenant-mobile-drawer absolute left-0 top-0 flex h-[100dvh] w-[min(88vw,330px)] flex-col overflow-hidden bg-white shadow-2xl">
            <div className="tenant-brand-strip h-1 shrink-0" />
            <div className="flex shrink-0 items-center justify-between gap-3 border-b border-slate-100 px-4 py-4">
              <div className="min-w-0 flex-1">
                <SchoolIdentity school={dashboard.school} compact />
              </div>
              <button
                type="button"
                onClick={() => setMobileNavOpen(false)}
                className="grid h-10 w-10 shrink-0 place-items-center rounded-xl text-slate-500 hover:bg-slate-100"
                aria-label="Fermer le menu"
              >
                <X size={20} />
              </button>
            </div>

            <nav className="tenant-scrollbar min-h-0 flex-1 space-y-1 overflow-y-auto p-3">
              {navButtons}
            </nav>

            <div className="shrink-0 border-t border-slate-100 p-3">
              <div className="flex items-center justify-between gap-2 rounded-xl bg-slate-50 px-3 py-2">
                <LanguageSwitcher />
                <button
                  type="button"
                  onClick={logout}
                  className="inline-flex items-center gap-2 rounded-lg px-2.5 py-2 text-sm text-slate-600 hover:bg-white"
                >
                  <LogOut size={16} />
                  {t("common.logout")}
                </button>
              </div>
            </div>
          </aside>
        </div>
      )}

      <div className="mx-auto grid max-w-7xl gap-5 px-3 py-4 sm:px-6 sm:py-6 lg:grid-cols-[220px_minmax(0,1fr)] lg:gap-6 lg:py-7">
        <aside className="hidden lg:block">
          <nav className="tenant-nav-shell tenant-scrollbar sticky top-24 max-h-[calc(100vh-7rem)] space-y-1 overflow-y-auto rounded-2xl border border-slate-200 bg-white p-2 shadow-sm">
            {navButtons}
          </nav>
        </aside>

        <main className="min-w-0">
          {section === "dashboard" && (
            <DashboardAnalytics
              dashboard={dashboard}
              portalAddress={portalAddress}
            />
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
            <FinanceWorkspace role={dashboard.membership.role} />
          )}

          {section === "settings" && (
            <SchoolSettingsPanel
              school={dashboard.school}
              canManage={canManage}
              onUpdated={(school) =>
                setDashboard((current) => ({ ...current, school }))
              }
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
