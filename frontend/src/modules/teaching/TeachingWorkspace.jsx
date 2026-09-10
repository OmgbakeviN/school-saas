import { useEffect, useMemo, useState } from "react";
import {
  BookOpenCheck,
  CheckCircle2,
  KeyRound,
  Loader2,
  Pencil,
  Plus,
  RefreshCw,
  ShieldCheck,
  Trash2,
  UserRoundCheck,
  Users,
  XCircle,
} from "lucide-react";

import { useI18n } from "../../i18n";
import api from "../../services/api";
import AssignmentDialog from "./AssignmentDialog";
import LeadershipDialog from "./LeadershipDialog";
import TeacherAccountDialog from "./TeacherAccountDialog";

function parseError(error, fallback) {
  const payload = error?.response?.data;
  if (!payload) return fallback;
  if (payload.detail) return String(payload.detail);
  const first = Object.values(payload)[0];
  if (Array.isArray(first)) return String(first[0]);
  if (typeof first === "string") return first;
  return fallback;
}

function EmptyState({ children }) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-8 text-center text-sm text-slate-500">
      {children}
    </div>
  );
}

function StatusBadge({ active, children }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${
        active
          ? "bg-emerald-50 text-emerald-700"
          : "bg-slate-100 text-slate-500"
      }`}
    >
      {active ? <CheckCircle2 size={12} /> : <XCircle size={12} />}
      {children}
    </span>
  );
}

export default function TeachingWorkspace({
  role,
  canManage,
  canManageAccounts,
}) {
  const { t } = useI18n();
  const teacherMode = role === "TEACHER";

  const [tab, setTab] = useState(teacherMode ? "mine" : "assignments");
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState("");

  const [assignments, setAssignments] = useState([]);
  const [leaderships, setLeaderships] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [years, setYears] = useState([]);
  const [classrooms, setClassrooms] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [levelSubjects, setLevelSubjects] = useState([]);
  const [myAccess, setMyAccess] = useState({
    teacher: null,
    assignments: [],
    leaderships: [],
  });

  const [assignmentDialog, setAssignmentDialog] = useState({
    open: false,
    item: null,
  });
  const [leadershipDialog, setLeadershipDialog] = useState({
    open: false,
    item: null,
  });
  const [accountDialog, setAccountDialog] = useState({
    open: false,
    teacher: null,
  });

  const load = async ({ initial = false } = {}) => {
    if (initial) setLoading(true);
    else setSyncing(true);
    setError("");

    try {
      const mePromise = api.get("/teaching/me/").catch((err) => {
        if (err?.response?.status === 409) {
          return { data: { teacher: null, assignments: [], leaderships: [], detail: err.response.data.detail } };
        }
        throw err;
      });

      if (canManage) {
        const [
          assignmentsRes,
          leadershipsRes,
          teachersRes,
          yearsRes,
          classroomsRes,
          subjectsRes,
          levelSubjectsRes,
          meRes,
        ] = await Promise.all([
          api.get("/teaching/assignments/"),
          api.get("/teaching/leaderships/"),
          api.get("/people/teachers/"),
          api.get("/academics/years/"),
          api.get("/academics/classrooms/"),
          api.get("/academics/subjects/"),
          api.get("/academics/level-subjects/"),
          mePromise,
        ]);

        setAssignments(assignmentsRes.data);
        setLeaderships(leadershipsRes.data);
        setTeachers(teachersRes.data);
        setYears(yearsRes.data);
        setClassrooms(classroomsRes.data);
        setSubjects(subjectsRes.data);
        setLevelSubjects(levelSubjectsRes.data);
        setMyAccess(meRes.data);
      } else {
        const meRes = await mePromise;
        setMyAccess(meRes.data);
        if (meRes.data?.detail) setError(meRes.data.detail);
      }
    } catch (err) {
      setError(parseError(err, t("teaching.errors.load")));
    } finally {
      if (initial) setLoading(false);
      else setSyncing(false);
    }
  };

  useEffect(() => {
    load({ initial: true });
  }, [role]);

  const activeYear = years.find((year) => year.is_active) || years[0] || null;

  const activeAssignments = useMemo(
    () => assignments.filter((item) => item.is_active),
    [assignments]
  );
  const uniqueClasses = useMemo(
    () => new Set(activeAssignments.map((item) => item.classroom)).size,
    [activeAssignments]
  );
  const scorePermissions = useMemo(
    () => activeAssignments.filter((item) => item.can_enter_scores).length,
    [activeAssignments]
  );

  const removeAssignment = async (item) => {
    if (!window.confirm(t("teaching.assignment.deleteConfirm", {
      teacher: item.teacher_name,
      subject: item.subject_name,
      classroom: item.classroom_name,
    }))) return;

    try {
      await api.delete(`/teaching/assignments/${item.id}/`);
      await load();
    } catch (err) {
      setError(parseError(err, t("teaching.errors.delete")));
    }
  };

  const removeLeadership = async (item) => {
    if (!window.confirm(t("teaching.leadership.deleteConfirm", {
      teacher: item.teacher_name,
      classroom: item.classroom_name,
    }))) return;

    try {
      await api.delete(`/teaching/leaderships/${item.id}/`);
      await load();
    } catch (err) {
      setError(parseError(err, t("teaching.errors.delete")));
    }
  };

  const revokeTeacherAccount = async (teacher) => {
    if (!window.confirm(t("teaching.accounts.revokeConfirm", {
      name: `${teacher.last_name} ${teacher.first_name}`,
    }))) return;

    try {
      await api.delete(`/teaching/teachers/${teacher.id}/account/`);
      await load();
    } catch (err) {
      setError(parseError(err, t("teaching.errors.account")));
    }
  };

  if (loading) {
    return (
      <div className="grid min-h-[300px] place-items-center rounded-3xl border border-slate-200 bg-white">
        <div className="inline-flex items-center gap-2 text-sm text-slate-500">
          <Loader2 size={17} className="animate-spin" />
          {t("teaching.loading")}
        </div>
      </div>
    );
  }

  const tabs = teacherMode
    ? [["mine", t("teaching.tabs.mine"), BookOpenCheck]]
    : [
        ["assignments", t("teaching.tabs.assignments"), BookOpenCheck],
        ["leaderships", t("teaching.tabs.leaderships"), UserRoundCheck],
        ...(canManageAccounts
          ? [["accounts", t("teaching.tabs.accounts"), KeyRound]]
          : []),
      ];

  return (
    <div className="space-y-5">
      <div className="flex flex-col justify-between gap-4 xl:flex-row xl:items-end">
        <div>
          <div className="text-xs font-medium uppercase tracking-[0.18em] text-slate-400">
            {t("teaching.step")}
          </div>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight">
            {teacherMode ? t("teaching.myTitle") : t("teaching.title")}
          </h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">
            {teacherMode ? t("teaching.myDescription") : t("teaching.description")}
          </p>
        </div>

        {syncing && (
          <div className="inline-flex items-center gap-2 text-xs text-slate-400">
            <RefreshCw size={13} className="animate-spin" />
            {t("teaching.syncing")}
          </div>
        )}
      </div>

      {error && (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          {error}
        </div>
      )}

      {!teacherMode && (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {[
            [t("teaching.summary.assignments"), activeAssignments.length, BookOpenCheck],
            [t("teaching.summary.classrooms"), uniqueClasses, Users],
            [t("teaching.summary.scorePermissions"), scorePermissions, ShieldCheck],
            [t("teaching.summary.leaderships"), leaderships.filter((item) => item.is_active).length, UserRoundCheck],
          ].map(([label, value, Icon]) => (
            <div key={label} className="rounded-2xl border border-slate-200 bg-white p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-500">{label}</span>
                <Icon size={17} className="text-slate-400" />
              </div>
              <div className="mt-3 text-2xl font-semibold">{value}</div>
            </div>
          ))}
        </div>
      )}

      <div className="flex gap-1 overflow-x-auto rounded-2xl border border-slate-200 bg-white p-1.5">
        {tabs.map(([id, label, Icon]) => (
          <button
            key={id}
            type="button"
            onClick={() => setTab(id)}
            className={`inline-flex shrink-0 items-center gap-2 rounded-xl px-4 py-2.5 text-sm ${
              tab === id
                ? "bg-slate-950 text-white"
                : "text-slate-600 hover:bg-slate-50"
            }`}
          >
            <Icon size={16} />
            {label}
          </button>
        ))}
      </div>

      {tab === "assignments" && canManage && (
        <section className="rounded-3xl border border-slate-200 bg-white p-6">
          <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
            <div>
              <h2 className="font-semibold">{t("teaching.assignment.title")}</h2>
              <p className="mt-1 text-xs leading-5 text-slate-500">
                {t("teaching.assignment.help")}
              </p>
            </div>
            <button
              type="button"
              onClick={() => setAssignmentDialog({ open: true, item: null })}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-medium text-white"
            >
              <Plus size={16} />
              {t("teaching.assignment.add")}
            </button>
          </div>

          {activeYear && (
            <div className="mt-4 text-xs text-slate-400">
              {t("teaching.activeYear", { name: activeYear.name })}
            </div>
          )}

          <div className="mt-5 space-y-3">
            {!assignments.length && (
              <EmptyState>{t("teaching.assignment.empty")}</EmptyState>
            )}

            {assignments.map((item) => (
              <div
                key={item.id}
                className="grid gap-4 rounded-2xl border border-slate-200 p-4 lg:grid-cols-[1.2fr_1fr_1fr_auto] lg:items-center"
              >
                <div>
                  <div className="font-medium">{item.teacher_name}</div>
                  <div className="mt-1 text-xs text-slate-500">
                    {item.teacher_employee_number}
                  </div>
                </div>

                <div>
                  <div className="text-sm font-medium">{item.subject_name}</div>
                  <div className="mt-1 text-xs text-slate-500">
                    {item.classroom_name} • {item.level_name}
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  <StatusBadge active={item.can_enter_scores}>
                    {item.can_enter_scores
                      ? t("teaching.assignment.scoresAllowed")
                      : t("teaching.assignment.scoresBlocked")}
                  </StatusBadge>
                  <StatusBadge active={item.is_active}>
                    {item.is_active ? t("common.active") : t("teaching.inactive")}
                  </StatusBadge>
                  {item.is_automatic && (
                    <span className="inline-flex items-center rounded-full bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700">
                      {t("teaching.assignment.automatic")}
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-1">
                  {item.is_automatic ? (
                    <span className="max-w-[180px] text-right text-[11px] leading-4 text-slate-400">
                      {t("teaching.assignment.automaticHelp")}
                    </span>
                  ) : (
                    <>
                      <button
                        type="button"
                        onClick={() => setAssignmentDialog({ open: true, item })}
                        className="grid h-9 w-9 place-items-center rounded-xl text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                      >
                        <Pencil size={15} />
                      </button>
                      <button
                        type="button"
                        onClick={() => removeAssignment(item)}
                        className="grid h-9 w-9 place-items-center rounded-xl text-slate-400 hover:bg-rose-50 hover:text-rose-600"
                      >
                        <Trash2 size={15} />
                      </button>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {tab === "leaderships" && canManage && (
        <section className="rounded-3xl border border-slate-200 bg-white p-6">
          <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
            <div>
              <h2 className="font-semibold">{t("teaching.leadership.title")}</h2>
              <p className="mt-1 text-xs leading-5 text-slate-500">
                {t("teaching.leadership.help")}
              </p>
            </div>
            <button
              type="button"
              onClick={() => setLeadershipDialog({ open: true, item: null })}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-medium text-white"
            >
              <Plus size={16} />
              {t("teaching.leadership.add")}
            </button>
          </div>

          <div className="mt-5 space-y-3">
            {!leaderships.length && (
              <EmptyState>{t("teaching.leadership.empty")}</EmptyState>
            )}

            {leaderships.map((item) => (
              <div
                key={item.id}
                className="flex flex-col gap-4 rounded-2xl border border-slate-200 p-4 md:flex-row md:items-center"
              >
                <div className="grid h-11 w-11 shrink-0 place-items-center rounded-2xl bg-slate-100">
                  <UserRoundCheck size={18} />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="font-medium">{item.teacher_name}</div>
                  <div className="mt-1 text-xs text-slate-500">
                    {item.role_label} • {item.classroom_name} • {item.academic_year_name}
                  </div>
                </div>
                <StatusBadge active={item.is_active}>
                  {item.is_active ? t("common.active") : t("teaching.inactive")}
                </StatusBadge>
                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    onClick={() => setLeadershipDialog({ open: true, item })}
                    className="grid h-9 w-9 place-items-center rounded-xl text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                  >
                    <Pencil size={15} />
                  </button>
                  <button
                    type="button"
                    onClick={() => removeLeadership(item)}
                    className="grid h-9 w-9 place-items-center rounded-xl text-slate-400 hover:bg-rose-50 hover:text-rose-600"
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {tab === "accounts" && canManageAccounts && (
        <section className="rounded-3xl border border-slate-200 bg-white p-6">
          <div>
            <h2 className="font-semibold">{t("teaching.accounts.title")}</h2>
            <p className="mt-1 max-w-3xl text-xs leading-5 text-slate-500">
              {t("teaching.accounts.help")}
            </p>
          </div>

          <div className="mt-5 space-y-3">
            {!teachers.length && (
              <EmptyState>{t("teaching.accounts.empty")}</EmptyState>
            )}

            {teachers.map((teacher) => (
              <div
                key={teacher.id}
                className="flex flex-col gap-4 rounded-2xl border border-slate-200 p-4 md:flex-row md:items-center"
              >
                <div className="grid h-11 w-11 shrink-0 place-items-center rounded-2xl bg-slate-100">
                  <KeyRound size={18} />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="font-medium">
                    {teacher.last_name} {teacher.first_name}
                  </div>
                  <div className="mt-1 text-xs text-slate-500">
                    {teacher.employee_number}
                    {teacher.linked_account
                      ? ` • ${teacher.linked_account.email}`
                      : ` • ${t("teaching.accounts.noAccount")}`}
                  </div>
                </div>

                {teacher.linked_account ? (
                  <div className="flex items-center gap-2">
                    <StatusBadge active>{t("teaching.accounts.linked")}</StatusBadge>
                    <button
                      type="button"
                      onClick={() => revokeTeacherAccount(teacher)}
                      className="rounded-xl border border-rose-200 px-3 py-2 text-xs font-medium text-rose-700 hover:bg-rose-50"
                    >
                      {t("teaching.accounts.revoke")}
                    </button>
                  </div>
                ) : (
                  <button
                    type="button"
                    onClick={() => setAccountDialog({ open: true, teacher })}
                    className="rounded-xl bg-slate-950 px-3.5 py-2.5 text-xs font-medium text-white"
                  >
                    {t("teaching.accounts.createOrLink")}
                  </button>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {tab === "mine" && (
        <div className="space-y-5">
          {myAccess.teacher && (
            <section className="rounded-3xl border border-slate-200 bg-white p-6">
              <div className="flex items-center gap-3">
                <div className="grid h-11 w-11 place-items-center rounded-2xl bg-slate-100">
                  <BookOpenCheck size={19} />
                </div>
                <div>
                  <h2 className="font-semibold">
                    {myAccess.teacher.last_name} {myAccess.teacher.first_name}
                  </h2>
                  <p className="text-sm text-slate-500">
                    {myAccess.teacher.employee_number}
                  </p>
                </div>
              </div>
            </section>
          )}

          <section className="rounded-3xl border border-slate-200 bg-white p-6">
            <h2 className="font-semibold">{t("teaching.mine.assignmentsTitle")}</h2>
            <p className="mt-1 text-xs leading-5 text-slate-500">
              {t("teaching.mine.assignmentsHelp")}
            </p>

            <div className="mt-5 grid gap-3 lg:grid-cols-2">
              {!myAccess.assignments?.length && (
                <div className="lg:col-span-2">
                  <EmptyState>{t("teaching.mine.noAssignments")}</EmptyState>
                </div>
              )}

              {myAccess.assignments?.map((item) => (
                <div key={item.id} className="rounded-2xl border border-slate-200 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="font-medium">{item.subject_name}</div>
                      <div className="mt-1 text-sm text-slate-600">
                        {item.classroom_name} • {item.level_name}
                      </div>
                      <div className="mt-1 text-xs text-slate-400">
                        {item.academic_year_name}
                      </div>
                    </div>
                    <ShieldCheck
                      size={18}
                      className={item.can_enter_scores ? "text-emerald-600" : "text-slate-300"}
                    />
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <StatusBadge active={item.can_enter_scores}>
                      {item.can_enter_scores
                        ? t("teaching.mine.canEnterScores")
                        : t("teaching.mine.cannotEnterScores")}
                    </StatusBadge>
                    {item.is_automatic && (
                      <span className="inline-flex items-center rounded-full bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700">
                        {t("teaching.assignment.fromClassTeacher")}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-3xl border border-slate-200 bg-white p-6">
            <h2 className="font-semibold">{t("teaching.mine.leadershipTitle")}</h2>
            <div className="mt-5 space-y-3">
              {!myAccess.leaderships?.length && (
                <EmptyState>{t("teaching.mine.noLeadership")}</EmptyState>
              )}
              {myAccess.leaderships?.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between gap-4 rounded-2xl border border-slate-200 p-4"
                >
                  <div>
                    <div className="font-medium">{item.classroom_name}</div>
                    <div className="mt-1 text-xs text-slate-500">
                      {item.role_label} • {item.academic_year_name}
                    </div>
                  </div>
                  <UserRoundCheck size={18} className="text-slate-400" />
                </div>
              ))}
            </div>
          </section>

          <div className="rounded-2xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm leading-6 text-blue-800">
            {t("teaching.mine.permissionRule")}
          </div>
        </div>
      )}

      {canManage && (
        <>
          <AssignmentDialog
            open={assignmentDialog.open}
            item={assignmentDialog.item}
            years={years}
            teachers={teachers}
            classrooms={classrooms}
            subjects={subjects}
            levelSubjects={levelSubjects}
            onClose={() => setAssignmentDialog({ open: false, item: null })}
            onSaved={() => load()}
          />

          <LeadershipDialog
            open={leadershipDialog.open}
            item={leadershipDialog.item}
            years={years}
            teachers={teachers}
            classrooms={classrooms}
            onClose={() => setLeadershipDialog({ open: false, item: null })}
            onSaved={() => load()}
          />
        </>
      )}

      {canManageAccounts && (
        <TeacherAccountDialog
          open={accountDialog.open}
          teacher={accountDialog.teacher}
          onClose={() => setAccountDialog({ open: false, teacher: null })}
          onSaved={() => load()}
        />
      )}
    </div>
  );
}
