import { useEffect, useState } from "react";
import { Loader2, Plus, Trash2, UserRoundCog } from "lucide-react";
import Field from "../../components/Field";
import { useI18n } from "../../i18n";
import api from "../../services/api";

const inputClass =
  "w-full rounded-xl border border-slate-200 bg-white px-3.5 py-3 text-sm outline-none focus:border-slate-400 focus:ring-4 focus:ring-slate-100";

const emptyForm = { first_name: "", last_name: "", email: "", password: "", role: "MANAGER" };

export default function MembersPanel() {
  const { t } = useI18n();
  const [members, setMembers] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await api.get("/tenant/members/");
      setMembers(data);
    } catch (err) {
      setError(err?.response?.data?.detail || t("members.loadError"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const create = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      const { data } = await api.post("/tenant/members/", form);
      setMembers((items) => [...items, data]);
      setForm(emptyForm);
      setShowForm(false);
    } catch (err) {
      const payload = err?.response?.data;
      const first = payload && Object.values(payload)[0];
      setError(Array.isArray(first) ? first[0] : payload?.detail || t("members.createError"));
    } finally {
      setSaving(false);
    }
  };

  const updateRole = async (member, role) => {
    const { data } = await api.patch(`/tenant/members/${member.id}/`, { role });
    setMembers((items) => items.map((item) => item.id === member.id ? data : item));
  };

  const remove = async (member) => {
    const name = `${member.first_name} ${member.last_name}`.trim();
    if (!window.confirm(t("members.removeConfirm", { name }))) return;
    await api.delete(`/tenant/members/${member.id}/`);
    setMembers((items) => items.filter((item) => item.id !== member.id));
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h2 className="text-xl font-semibold tracking-tight">{t("members.title")}</h2>
          <p className="mt-1 text-sm text-slate-500">{t("members.subtitle")}</p>
        </div>
        <button onClick={() => setShowForm((v) => !v)} className="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-medium text-white">
          <Plus size={16} /> {t("members.add")}
        </button>
      </div>

      {showForm && (
        <form onSubmit={create} className="rounded-3xl border border-slate-200 bg-white p-6">
          <div className="grid gap-5 sm:grid-cols-2">
            <Field label={t("members.firstName")}><input required className={inputClass} value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} /></Field>
            <Field label={t("members.lastName")}><input required className={inputClass} value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} /></Field>
            <Field label={t("members.email")}><input required type="email" className={inputClass} value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></Field>
            <Field label={t("members.initialPassword")}><input required minLength={8} type="password" className={inputClass} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} /></Field>
            <div className="sm:col-span-2">
              <Field label={t("members.role")}>
                <select className={inputClass} value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
                  <option value="DIRECTOR">{t("members.director")}</option><option value="MANAGER">{t("members.manager")}</option><option value="ACCOUNTANT">{t("members.accountant")}</option>
                </select>
              </Field>
            </div>
          </div>
          <div className="mt-6 flex justify-end">
            <button disabled={saving} className="inline-flex items-center gap-2 rounded-xl bg-slate-950 px-5 py-3 text-sm font-medium text-white disabled:opacity-50">
              {saving && <Loader2 className="animate-spin" size={16} />} {t("members.create")}
            </button>
          </div>
        </form>
      )}

      {error && <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>}

      <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white">
        {loading ? (
          <div className="p-8 text-sm text-slate-500">{t("members.loading")}</div>
        ) : (
          <div className="divide-y divide-slate-100">
            {members.map((member) => {
              const owner = member.role === "OWNER";
              return (
                <div key={member.id} className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center">
                  <div className="grid h-10 w-10 shrink-0 place-items-center rounded-2xl bg-slate-100"><UserRoundCog size={18} /></div>
                  <div className="min-w-0 flex-1">
                    <div className="font-medium">{member.first_name} {member.last_name}</div>
                    <div className="truncate text-sm text-slate-500">{member.email}</div>
                  </div>
                  <select disabled={owner} className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm disabled:bg-slate-50 disabled:text-slate-400" value={member.role} onChange={(e) => updateRole(member, e.target.value)}>
                    {owner && <option value="OWNER">{t("members.owner")}</option>}
                    <option value="DIRECTOR">{t("members.director")}</option><option value="MANAGER">{t("members.manager")}</option><option value="TEACHER">{t("members.teacher")}</option><option value="ACCOUNTANT">{t("members.accountant")}</option>
                  </select>
                  {!owner && (
                    <button onClick={() => remove(member)} className="grid h-9 w-9 place-items-center rounded-xl text-slate-400 hover:bg-rose-50 hover:text-rose-600" title={t("members.remove")}><Trash2 size={16} /></button>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
