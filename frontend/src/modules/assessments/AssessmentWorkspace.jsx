import { useEffect, useMemo, useState } from "react";
import { Calculator, CheckCircle2, ClipboardCheck, FileCheck2, Loader2, LockKeyhole, Pencil, Plus, RefreshCw, RotateCcw, Send, SlidersHorizontal } from "lucide-react";
import { useI18n } from "../../i18n";
import api from "../../services/api";
import AssessmentDialog from "./AssessmentDialog";
import GradebookPanel from "./GradebookPanel";

function parseError(error, fallback) {
  return error?.response?.data?.detail || fallback;
}

const statusClass = {
  DRAFT: "bg-slate-100 text-slate-700",
  INPUT: "bg-blue-50 text-blue-700",
  SUBMITTED: "bg-amber-50 text-amber-700",
  VALIDATED: "bg-violet-50 text-violet-700",
  PUBLISHED: "bg-emerald-50 text-emerald-700",
};

export default function AssessmentWorkspace({ role, canManage, isDirection }) {
  const { t } = useI18n();
  const teacherMode = role === "TEACHER";
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [tab, setTab] = useState("assessments");
  const [assessments, setAssessments] = useState([]);
  const [periods, setPeriods] = useState([]);
  const [controls, setControls] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [years, setYears] = useState([]);
  const [classrooms, setClassrooms] = useState([]);
  const [dialog, setDialog] = useState({ open: false, item: null });
  const [gradebookId, setGradebookId] = useState(null);
  const [resultYear, setResultYear] = useState("");
  const [resultClass, setResultClass] = useState("");
  const [resultPeriod, setResultPeriod] = useState("");
  const [resultData, setResultData] = useState(null);

  const load = async ({ initial = false } = {}) => {
    if (initial) setLoading(true); else setSyncing(true);
    setError("");
    try {
      const base = [
        api.get("/assessments/assessments/"),
        api.get("/assessments/period-controls/"),
        api.get("/academics/periods/"),
      ];
      const extra = canManage
        ? [api.get("/teaching/assignments/"), api.get("/academics/years/"), api.get("/academics/classrooms/")]
        : [api.get("/teaching/me/"), api.get("/academics/years/"), api.get("/academics/classrooms/")];
      const [assessmentRes, controlRes, periodRes, teachingRes, yearRes, classRes] = await Promise.all([...base, ...extra]);
      setAssessments(assessmentRes.data);
      setControls(controlRes.data);
      setPeriods(periodRes.data);
      setAssignments(canManage ? teachingRes.data : teachingRes.data.assignments || []);
      setYears(yearRes.data);
      setClassrooms(classRes.data);
      const active = yearRes.data.find((year) => year.is_active) || yearRes.data[0];
      if (active) setResultYear((current) => current || String(active.id));
    } catch (err) {
      setError(parseError(err, t("assessments.errors.load")));
    } finally {
      if (initial) setLoading(false); else setSyncing(false);
    }
  };

  useEffect(() => { load({ initial: true }); }, [role]);

  const saveAssessment = async (payload) => {
    setError("");
    try {
      if (dialog.item) await api.patch(`/assessments/assessments/${dialog.item.id}/`, payload);
      else await api.post("/assessments/assessments/", payload);
      await load();
    } catch (err) {
      setError(parseError(err, t("assessments.errors.saveAssessment")));
      throw err;
    }
  };

  const action = async (item, name) => {
    setError(""); setMessage("");
    try {
      const response = await api.post(`/assessments/assessments/${item.id}/${name}/`, {});
      setMessage(response.data.detail);
      await load();
    } catch (err) {
      setError(parseError(err, t("assessments.errors.workflow")));
    }
  };

  const togglePeriod = async (control) => {
    try {
      await api.patch(`/assessments/period-controls/${control.academic_period}/`, { score_entry_open: !control.score_entry_open });
      await load();
    } catch (err) {
      setError(parseError(err, t("assessments.errors.period")));
    }
  };

  const resultClassrooms = useMemo(() => classrooms.filter((item) => String(item.academic_year) === String(resultYear)), [classrooms, resultYear]);
  const resultPeriods = useMemo(() => periods.filter((item) => String(item.academic_year) === String(resultYear)), [periods, resultYear]);

  const loadResults = async () => {
    if (!resultClass || !resultPeriod) return;
    try {
      const response = await api.get(`/assessments/results/classrooms/${resultClass}/periods/${resultPeriod}/`);
      setResultData(response.data);
    } catch (err) {
      setError(parseError(err, t("assessments.errors.results")));
    }
  };

  const recalc = async () => {
    try {
      const response = await api.post(`/assessments/years/${resultYear}/recalculate-averages/`, resultClass ? { classroom: Number(resultClass) } : {});
      setMessage(t("assessments.results.recalculated", response.data));
    } catch (err) {
      setError(parseError(err, t("assessments.errors.results")));
    }
  };

  if (loading) return <div className="grid min-h-[300px] place-items-center rounded-3xl border border-slate-200 bg-white"><Loader2 className="animate-spin" size={20} /></div>;
  if (gradebookId) return <GradebookPanel assessmentId={gradebookId} onBack={() => setGradebookId(null)} onSaved={() => load()} />;

  const tabs = [
    ["assessments", teacherMode ? t("assessments.tabs.mine") : t("assessments.tabs.assessments"), ClipboardCheck],
    ...(canManage ? [["periods", t("assessments.tabs.periods"), SlidersHorizontal], ["results", t("assessments.tabs.results"), Calculator]] : []),
  ];

  return (
    <div className="space-y-5">
      <div className="flex flex-col justify-between gap-4 xl:flex-row xl:items-end">
        <div>
          <div className="text-xs font-medium uppercase tracking-[0.18em] text-slate-400">{t("assessments.step")}</div>
          <h1 className="mt-2 text-2xl font-semibold">{teacherMode ? t("assessments.myTitle") : t("assessments.title")}</h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">{teacherMode ? t("assessments.myDescription") : t("assessments.description")}</p>
        </div>
        {syncing && <span className="inline-flex items-center gap-2 text-xs text-slate-400"><RefreshCw size={13} className="animate-spin" />{t("assessments.syncing")}</span>}
      </div>

      {error && <div className="rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>}
      {message && <div className="rounded-2xl bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{message}</div>}

      <div className="flex gap-1 overflow-x-auto rounded-2xl border border-slate-200 bg-white p-1.5">
        {tabs.map(([id, label, Icon]) => <button key={id} onClick={() => setTab(id)} className={`inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm ${tab === id ? "bg-slate-950 text-white" : "text-slate-600 hover:bg-slate-50"}`}><Icon size={16} />{label}</button>)}
      </div>

      {tab === "assessments" && (
        <section className="rounded-3xl border border-slate-200 bg-white p-6">
          <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
            <div><h2 className="font-semibold">{t("assessments.list.title")}</h2><p className="mt-1 text-xs text-slate-500">{t("assessments.list.help")}</p></div>
            <button onClick={() => setDialog({ open: true, item: null })} className="inline-flex items-center gap-2 rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-medium text-white"><Plus size={16} />{t("assessments.list.add")}</button>
          </div>
          <div className="mt-5 space-y-3">
            {!assessments.length && <div className="rounded-2xl bg-slate-50 p-8 text-center text-sm text-slate-500">{t("assessments.list.empty")}</div>}
            {assessments.map((item) => (
              <div key={item.id} className="grid gap-4 rounded-2xl border border-slate-200 p-4 xl:grid-cols-[1.2fr_1fr_auto] xl:items-center">
                <div><div className="font-medium">{item.title}</div><div className="mt-1 text-xs text-slate-500">{item.subject_name} • {item.classroom_name} • {item.period_name}</div><div className="mt-1 text-xs text-slate-400">{item.teacher_name} • /{item.max_score} • ×{item.weight}</div></div>
                <div><span className={`rounded-full px-2.5 py-1 text-xs font-medium ${statusClass[item.status]}`}>{t(`assessments.status.${item.status.toLowerCase()}`)}</span></div>
                <div className="flex flex-wrap items-center justify-end gap-2">
                  {item.can_edit && <button onClick={() => setDialog({ open: true, item })} className="grid h-9 w-9 place-items-center rounded-xl hover:bg-slate-100"><Pencil size={15} /></button>}
                  {item.status === "DRAFT" && <button onClick={() => action(item, "open")} className="rounded-xl border border-slate-200 px-3 py-2 text-xs">{t("assessments.actions.open")}</button>}
                  {item.status === "INPUT" && <button onClick={() => setGradebookId(item.id)} className="rounded-xl bg-slate-950 px-3 py-2 text-xs text-white">{t("assessments.actions.enterGrades")}</button>}
                  {item.status === "INPUT" && <button onClick={() => action(item, "submit")} className="inline-flex items-center gap-1 rounded-xl border border-slate-200 px-3 py-2 text-xs"><Send size={13}/>{t("assessments.actions.submit")}</button>}
                  {item.status === "SUBMITTED" && isDirection && <button onClick={() => action(item, "validate")} className="inline-flex items-center gap-1 rounded-xl bg-violet-50 px-3 py-2 text-xs text-violet-700"><CheckCircle2 size={13}/>{t("assessments.actions.validate")}</button>}
                  {item.status === "VALIDATED" && isDirection && <button onClick={() => action(item, "publish")} className="inline-flex items-center gap-1 rounded-xl bg-emerald-50 px-3 py-2 text-xs text-emerald-700"><LockKeyhole size={13}/>{t("assessments.actions.publish")}</button>}
                  {["SUBMITTED", "VALIDATED", "PUBLISHED"].includes(item.status) && isDirection && <button onClick={() => action(item, "reopen")} className="inline-flex items-center gap-1 rounded-xl border border-slate-200 px-3 py-2 text-xs"><RotateCcw size={13}/>{t("assessments.actions.reopen")}</button>}
                  {item.status !== "DRAFT" && <button onClick={() => setGradebookId(item.id)} className="rounded-xl border border-slate-200 px-3 py-2 text-xs">{t("assessments.actions.viewGrades")}</button>}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {tab === "periods" && canManage && (
        <section className="rounded-3xl border border-slate-200 bg-white p-6">
          <h2 className="font-semibold">{t("assessments.periods.title")}</h2><p className="mt-1 text-xs text-slate-500">{t("assessments.periods.help")}</p>
          <div className="mt-5 grid gap-3 md:grid-cols-2">
            {controls.map((control) => <div key={control.id} className="flex items-center justify-between gap-4 rounded-2xl border border-slate-200 p-4"><div><div className="font-medium">{control.period_name}</div><div className="mt-1 text-xs text-slate-500">{control.academic_year_name}</div></div><button onClick={() => togglePeriod(control)} className={`rounded-xl px-3 py-2 text-xs font-medium ${control.score_entry_open ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-600"}`}>{control.score_entry_open ? t("assessments.periods.open") : t("assessments.periods.closed")}</button></div>)}
          </div>
        </section>
      )}

      {tab === "results" && canManage && (
        <section className="rounded-3xl border border-slate-200 bg-white p-6">
          <div><h2 className="font-semibold">{t("assessments.results.title")}</h2><p className="mt-1 text-xs text-slate-500">{t("assessments.results.help")}</p></div>
          <div className="mt-5 grid gap-3 md:grid-cols-3">
            <select className="rounded-xl border border-slate-200 px-3 py-2.5 text-sm" value={resultYear} onChange={(e) => {setResultYear(e.target.value); setResultClass(""); setResultPeriod("");}}><option value="">{t("common.choose")}</option>{years.map((year) => <option key={year.id} value={year.id}>{year.name}</option>)}</select>
            <select className="rounded-xl border border-slate-200 px-3 py-2.5 text-sm" value={resultClass} onChange={(e) => setResultClass(e.target.value)}><option value="">{t("common.choose")}</option>{resultClassrooms.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select>
            <select className="rounded-xl border border-slate-200 px-3 py-2.5 text-sm" value={resultPeriod} onChange={(e) => setResultPeriod(e.target.value)}><option value="">{t("common.choose")}</option>{resultPeriods.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select>
          </div>
          <div className="mt-4 flex flex-wrap gap-2"><button onClick={loadResults} disabled={!resultClass || !resultPeriod} className="rounded-xl bg-slate-950 px-4 py-2.5 text-sm text-white disabled:opacity-40">{t("assessments.results.calculate")}</button><button onClick={recalc} disabled={!resultYear} className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm disabled:opacity-40">{t("assessments.results.recalculateYear")}</button></div>
          {resultData && <div className="mt-5 overflow-x-auto"><table className="w-full min-w-[700px] text-left text-sm"><thead className="text-xs uppercase text-slate-400"><tr><th className="px-3 py-3">{t("assessments.gradebook.student")}</th><th className="px-3 py-3">{t("assessments.results.subjects")}</th><th className="px-3 py-3">{t("assessments.results.average")}</th></tr></thead><tbody className="divide-y divide-slate-100">{resultData.students.map((student) => <tr key={student.enrollment_id}><td className="px-3 py-3"><div className="font-medium">{student.student_name}</div><div className="text-xs text-slate-400">{student.matricule}</div></td><td className="px-3 py-3"><div className="flex flex-wrap gap-1.5">{student.subjects.map((subject) => <span key={subject.subject_id} className="rounded-lg bg-slate-50 px-2 py-1 text-xs">{subject.subject_name}: {subject.average}/{subject.max_score}</span>)}</div></td><td className="px-3 py-3 font-semibold">{student.overall_average ?? "—"}</td></tr>)}</tbody></table></div>}
        </section>
      )}

      <AssessmentDialog open={dialog.open} item={dialog.item} assignments={assignments} periods={periods} onClose={() => setDialog({ open: false, item: null })} onSave={saveAssessment} />
    </div>
  );
}
