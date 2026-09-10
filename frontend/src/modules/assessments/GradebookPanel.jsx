import { useEffect, useState } from "react";
import { ArrowLeft, Loader2, Save } from "lucide-react";
import { useI18n } from "../../i18n";
import api from "../../services/api";

const inputClass =
  "w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-slate-400 focus:ring-4 focus:ring-slate-100";

function parseError(error, fallback) {
  return error?.response?.data?.detail || fallback;
}

export default function GradebookPanel({ assessmentId, onBack, onSaved }) {
  const { t } = useI18n();
  const [data, setData] = useState(null);
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await api.get(`/assessments/assessments/${assessmentId}/gradebook/`);
      setData(response.data);
      setRows(
        response.data.rows.map((row) => ({
          ...row,
          score: row.score ?? "",
        }))
      );
    } catch (err) {
      setError(parseError(err, t("assessments.errors.gradebook")));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [assessmentId]);

  const update = (index, patch) => {
    setRows((current) =>
      current.map((row, rowIndex) =>
        rowIndex === index ? { ...row, ...patch } : row
      )
    );
  };

  const save = async () => {
    setSaving(true);
    setError("");
    setMessage("");
    try {
      const payload = {
        grades: rows.map((row) => ({
          enrollment: row.enrollment_id,
          score: row.is_absent || row.is_exempt || row.score === "" ? null : row.score,
          is_absent: row.is_absent,
          is_exempt: row.is_exempt,
          comment: row.comment || "",
        })),
      };
      const response = await api.put(
        `/assessments/assessments/${assessmentId}/gradebook/`,
        payload
      );
      setData(response.data);
      setRows(response.data.rows.map((row) => ({ ...row, score: row.score ?? "" })));
      setMessage(t("assessments.gradebook.saved"));
      await onSaved?.();
    } catch (err) {
      setError(parseError(err, t("assessments.errors.saveGrades")));
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="grid min-h-[260px] place-items-center rounded-3xl border border-slate-200 bg-white"><Loader2 className="animate-spin" size={20} /></div>;
  }

  if (!data) return null;

  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-6">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-start">
        <div>
          <button type="button" onClick={onBack} className="mb-4 inline-flex items-center gap-2 text-sm text-slate-500 hover:text-slate-900">
            <ArrowLeft size={16} /> {t("assessments.gradebook.back")}
          </button>
          <h2 className="text-xl font-semibold">{data.assessment.title}</h2>
          <p className="mt-1 text-sm text-slate-500">
            {data.assessment.subject_name} • {data.assessment.classroom_name} • {data.assessment.period_name} • /{data.assessment.max_score}
          </p>
        </div>
        <button
          type="button"
          onClick={save}
          disabled={saving || !data.can_edit}
          className="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-medium text-white disabled:opacity-40"
        >
          {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
          {t("assessments.gradebook.save")}
        </button>
      </div>

      {!data.can_edit && (
        <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          {t("assessments.gradebook.locked")}
        </div>
      )}
      {error && <div className="mt-4 rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>}
      {message && <div className="mt-4 rounded-2xl bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{message}</div>}

      <div className="mt-5 overflow-x-auto">
        <table className="w-full min-w-[820px] text-left text-sm">
          <thead className="text-xs uppercase tracking-wide text-slate-400">
            <tr>
              <th className="px-3 py-3">{t("assessments.gradebook.student")}</th>
              <th className="px-3 py-3">{t("assessments.gradebook.score")}</th>
              <th className="px-3 py-3">ABS</th>
              <th className="px-3 py-3">{t("assessments.gradebook.exempt")}</th>
              <th className="px-3 py-3">{t("assessments.gradebook.comment")}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rows.map((row, index) => (
              <tr key={row.enrollment_id}>
                <td className="px-3 py-3">
                  <div className="font-medium">{row.student_name}</div>
                  <div className="text-xs text-slate-400">{row.matricule}</div>
                </td>
                <td className="px-3 py-3 w-36">
                  <input
                    type="number"
                    min="0"
                    max={data.assessment.max_score}
                    step="0.001"
                    disabled={!data.can_edit || row.is_absent || row.is_exempt}
                    className={inputClass}
                    value={row.score}
                    onChange={(e) => update(index, { score: e.target.value })}
                  />
                </td>
                <td className="px-3 py-3">
                  <input type="checkbox" disabled={!data.can_edit} checked={row.is_absent} onChange={(e) => update(index, { is_absent: e.target.checked, is_exempt: false, score: e.target.checked ? "" : row.score })} />
                </td>
                <td className="px-3 py-3">
                  <input type="checkbox" disabled={!data.can_edit} checked={row.is_exempt} onChange={(e) => update(index, { is_exempt: e.target.checked, is_absent: false, score: e.target.checked ? "" : row.score })} />
                </td>
                <td className="px-3 py-3">
                  <input disabled={!data.can_edit} className={inputClass} value={row.comment || ""} onChange={(e) => update(index, { comment: e.target.value })} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
