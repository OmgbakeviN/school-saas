import { useEffect, useMemo, useState } from "react";
import {
  Banknote,
  CheckCircle2,
  Download,
  FileText,
  Loader2,
  Plus,
  ReceiptText,
  RefreshCw,
  Search,
  Settings2,
  WalletCards,
} from "lucide-react";

import { useI18n } from "../../i18n";
import api from "../../services/api";


const inputClass =
  "w-full rounded-xl border border-slate-200 bg-white px-3.5 py-3 text-sm outline-none focus:border-slate-400 focus:ring-4 focus:ring-slate-100";

const primaryButton =
  "inline-flex items-center justify-center gap-2 rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-medium text-white disabled:opacity-40";

function money(value, currency = "XAF") {
  const number = Number(value || 0);
  return `${new Intl.NumberFormat("fr-FR", {
    maximumFractionDigits: 0,
  }).format(number)} ${currency}`;
}

function parseError(error, fallback) {
  const data = error?.response?.data;
  if (!data) return fallback;
  if (data.detail) return String(data.detail);

  const first = Object.values(data)[0];
  if (Array.isArray(first)) return String(first[0]);
  if (first && typeof first === "object") {
    const nested = Object.values(first)[0];
    if (Array.isArray(nested)) return String(nested[0]);
  }
  return fallback;
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

function StatusBadge({ status, t }) {
  const labels = {
    PAID: t("finance.status.paid"),
    PARTIAL: t("finance.status.partial"),
    UNPAID: t("finance.status.unpaid"),
  };

  const classes = {
    PAID: "bg-emerald-50 text-emerald-700",
    PARTIAL: "bg-amber-50 text-amber-700",
    UNPAID: "bg-rose-50 text-rose-700",
  };

  return (
    <span
      className={`rounded-full px-2.5 py-1 text-xs font-medium ${
        classes[status] || "bg-slate-100 text-slate-600"
      }`}
    >
      {labels[status] || status}
    </span>
  );
}

function Metric({ label, value, help }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4">
      <div className="text-xs font-medium uppercase tracking-[0.12em] text-slate-400">
        {label}
      </div>
      <div className="mt-2 text-2xl font-semibold">{value}</div>
      {help && <div className="mt-1 text-xs text-slate-500">{help}</div>}
    </div>
  );
}

function PaymentDialog({
  open,
  account,
  onClose,
  onSaved,
  t,
}) {
  const [form, setForm] = useState({
    amount: "",
    method: "CASH",
    reference: "",
    notes: "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (open && account) {
      setForm({
        amount: "",
        method: "CASH",
        reference: "",
        notes: "",
      });
      setError("");
    }
  }, [open, account]);

  if (!open || !account) return null;

  const submit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError("");

    try {
      const { data } = await api.post(
        "/finance/payments/record/",
        {
          tuition_account: account.id,
          amount: form.amount,
          method: form.method,
          reference: form.reference,
          notes: form.notes,
        }
      );

      await onSaved(data);
      onClose();
    } catch (err) {
      setError(parseError(err, t("finance.errors.payment")));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 p-2 sm:p-4">
      <form
        onSubmit={submit}
        className="flex max-h-[calc(100dvh-1rem)] w-full max-w-xl flex-col overflow-hidden rounded-3xl bg-white shadow-2xl sm:max-h-[calc(100dvh-2rem)]"
      >
        <div className="flex shrink-0 items-start justify-between gap-4 border-b border-slate-100 px-5 py-4 sm:px-6 sm:py-5">
          <div className="min-w-0">
            <h3 className="text-lg font-semibold">
              {t("finance.payment.title")}
            </h3>
            <p className="mt-1 truncate text-sm text-slate-500">
              {account.student_name} • {account.classroom_name}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="shrink-0 rounded-xl px-3 py-2 text-sm text-slate-500 hover:bg-slate-100"
          >
            ✕
          </button>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-5 py-4 sm:px-6 sm:py-5">
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-2xl bg-slate-50 p-3">
              <div className="text-xs text-slate-400">
                {t("finance.fields.expected")}
              </div>
              <div className="mt-1 font-semibold">
                {money(account.expected_amount, account.currency)}
              </div>
            </div>
            <div className="rounded-2xl bg-slate-50 p-3">
              <div className="text-xs text-slate-400">
                {t("finance.fields.paid")}
              </div>
              <div className="mt-1 font-semibold">
                {money(account.paid_amount, account.currency)}
              </div>
            </div>
            <div className="rounded-2xl bg-slate-950 p-3 text-white">
              <div className="text-xs text-slate-300">
                {t("finance.fields.balance")}
              </div>
              <div className="mt-1 font-semibold">
                {money(account.balance, account.currency)}
              </div>
            </div>
          </div>

          {error && (
            <div className="mt-4 rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-700">
              {error}
            </div>
          )}

          {!!account.installments?.length && (
            <div className="mt-4 rounded-2xl border border-slate-200 p-3">
              <div className="text-xs font-medium text-slate-500">
                {t("finance.payment.installments")}
              </div>
              <div className="mt-2 max-h-48 space-y-2 overflow-y-auto overscroll-contain pr-1">
                {account.installments.map((item) => (
                  <div
                    key={item.id}
                    className="flex items-center justify-between gap-3 rounded-xl bg-slate-50 px-3 py-2 text-xs"
                  >
                    <div>
                      <div className="font-medium">{item.name}</div>
                      {item.due_date && (
                        <div className="mt-0.5 text-slate-400">
                          {t("finance.payment.due")}: {item.due_date}
                        </div>
                      )}
                    </div>
                    <div className="text-right">
                      <div>
                        {money(item.paid, account.currency)} /{" "}
                        {money(item.amount, account.currency)}
                      </div>
                      <div className="mt-0.5 text-slate-400">
                        {t("finance.fields.balance")}:{" "}
                        {money(item.remaining, account.currency)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="mt-5 space-y-4">
            <label className="block">
              <span className="text-xs font-medium text-slate-500">
                {t("finance.payment.amount")}
              </span>
              <input
                required
                min="1"
                step="1"
                type="number"
                className={`${inputClass} mt-2`}
                value={form.amount}
                onChange={(event) =>
                  setForm({ ...form, amount: event.target.value })
                }
                placeholder={String(
                  Math.max(0, Number(account.balance || 0))
                )}
              />
            </label>

            <label className="block">
              <span className="text-xs font-medium text-slate-500">
                {t("finance.payment.method")}
              </span>
              <select
                className={`${inputClass} mt-2`}
                value={form.method}
                onChange={(event) =>
                  setForm({ ...form, method: event.target.value })
                }
              >
                <option value="CASH">
                  {t("finance.methods.cash")}
                </option>
                <option value="MOBILE_MONEY">
                  {t("finance.methods.mobileMoney")}
                </option>
                <option value="BANK_TRANSFER">
                  {t("finance.methods.bank")}
                </option>
                <option value="CARD">
                  {t("finance.methods.card")}
                </option>
                <option value="OTHER">
                  {t("finance.methods.other")}
                </option>
              </select>
            </label>

            <label className="block">
              <span className="text-xs font-medium text-slate-500">
                {t("finance.payment.reference")}
              </span>
              <input
                className={`${inputClass} mt-2`}
                value={form.reference}
                onChange={(event) =>
                  setForm({
                    ...form,
                    reference: event.target.value,
                  })
                }
                placeholder={t("finance.payment.referencePlaceholder")}
              />
            </label>

            <label className="block">
              <span className="text-xs font-medium text-slate-500">
                {t("finance.payment.notes")}
              </span>
              <textarea
                rows={3}
                className={`${inputClass} mt-2 resize-y`}
                value={form.notes}
                onChange={(event) =>
                  setForm({ ...form, notes: event.target.value })
                }
              />
            </label>
          </div>
        </div>

        <div className="flex shrink-0 justify-end gap-2 border-t border-slate-100 bg-white px-5 py-4 sm:px-6">
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-medium"
          >
            {t("common.cancel")}
          </button>
          <button
            className={primaryButton}
            disabled={saving}
          >
            {saving ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <ReceiptText size={16} />
            )}
            {t("finance.payment.save")}
          </button>
        </div>
      </form>
    </div>
  );
}

export default function FinanceWorkspace({ role }) {
  const { t } = useI18n();

  const canConfigure = ["OWNER", "DIRECTOR", "MANAGER"].includes(
    role
  );

  const [tab, setTab] = useState("dashboard");
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [saving, setSaving] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const [options, setOptions] = useState({
    years: [],
    levels: [],
    classrooms: [],
  });
  const [dashboard, setDashboard] = useState(null);
  const [plans, setPlans] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [payments, setPayments] = useState([]);

  const [yearId, setYearId] = useState("");
  const [classroomId, setClassroomId] = useState("");
  const [search, setSearch] = useState("");
  const [paymentStatus, setPaymentStatus] = useState("");

  const [planForm, setPlanForm] = useState({
    name: "",
    academic_year: "",
    scope: "LEVEL",
    level: "",
    classroom: "",
    currency: "XAF",
    notes: "",
  });

  const [installmentForm, setInstallmentForm] = useState({
    plan: "",
    name: "",
    amount: "",
    due_date: "",
    order: 1,
  });

  const [paymentDialog, setPaymentDialog] = useState({
    open: false,
    account: null,
  });

  const classrooms = useMemo(
    () =>
      options.classrooms.filter(
        (item) =>
          !yearId ||
          String(item.academic_year) === String(yearId)
      ),
    [options.classrooms, yearId]
  );

  const load = async ({ initial = false } = {}) => {
    if (initial) setLoading(true);
    else setSyncing(true);

    setError("");

    try {
      const { data: optionData } = await api.get(
        "/finance/options/"
      );
      setOptions(optionData);

      const active =
        optionData.years.find((item) => item.is_active) ||
        optionData.years[0];
      const effectiveYear = yearId || (active ? String(active.id) : "");

      if (!yearId && active) {
        setYearId(String(active.id));
        setPlanForm((current) => ({
          ...current,
          academic_year:
            current.academic_year || String(active.id),
        }));
      }

      const params = new URLSearchParams();
      if (effectiveYear) {
        params.set("academic_year", effectiveYear);
      }
      if (classroomId) {
        params.set("classroom", classroomId);
      }

      const [dashboardRes, plansRes, accountsRes, paymentsRes] =
        await Promise.all([
          api.get(`/finance/dashboard/?${params.toString()}`),
          api.get(
            `/finance/plans/?${
              effectiveYear
                ? `academic_year=${effectiveYear}`
                : ""
            }`
          ),
          api.get(`/finance/accounts/?${params.toString()}`),
          api.get(`/finance/payments/?${params.toString()}`),
        ]);

      setDashboard(dashboardRes.data);
      setPlans(plansRes.data);
      setAccounts(accountsRes.data);
      setPayments(paymentsRes.data);
    } catch (err) {
      setError(parseError(err, t("finance.errors.load")));
    } finally {
      if (initial) setLoading(false);
      else setSyncing(false);
    }
  };

  useEffect(() => {
    load({ initial: true });
  }, [role]);

  const reloadFiltered = async () => {
    setSyncing(true);
    setError("");

    try {
      const params = new URLSearchParams();
      if (yearId) params.set("academic_year", yearId);
      if (classroomId) params.set("classroom", classroomId);
      if (search) params.set("search", search);
      if (paymentStatus) {
        params.set("payment_status", paymentStatus);
      }

      const paymentParams = new URLSearchParams();
      if (yearId) paymentParams.set("academic_year", yearId);
      if (classroomId) {
        paymentParams.set("classroom", classroomId);
      }
      if (search) paymentParams.set("search", search);

      const dashboardParams = new URLSearchParams();
      if (yearId) dashboardParams.set("academic_year", yearId);
      if (classroomId) {
        dashboardParams.set("classroom", classroomId);
      }

      const [dashboardRes, accountsRes, paymentsRes] =
        await Promise.all([
          api.get(
            `/finance/dashboard/?${dashboardParams.toString()}`
          ),
          api.get(`/finance/accounts/?${params.toString()}`),
          api.get(
            `/finance/payments/?${paymentParams.toString()}`
          ),
        ]);

      setDashboard(dashboardRes.data);
      setAccounts(accountsRes.data);
      setPayments(paymentsRes.data);
    } catch (err) {
      setError(parseError(err, t("finance.errors.load")));
    } finally {
      setSyncing(false);
    }
  };

  useEffect(() => {
    if (!loading) {
      reloadFiltered();
    }
  }, [yearId, classroomId, paymentStatus]);

  const createPlan = async (event) => {
    event.preventDefault();
    setSaving("plan");
    setError("");
    setMessage("");

    try {
      const payload = {
        name: planForm.name,
        academic_year: Number(planForm.academic_year),
        currency: planForm.currency,
        notes: planForm.notes,
        level:
          planForm.scope === "LEVEL" && planForm.level
            ? Number(planForm.level)
            : null,
        classroom:
          planForm.scope === "CLASSROOM" &&
          planForm.classroom
            ? Number(planForm.classroom)
            : null,
      };

      const { data } = await api.post(
        "/finance/plans/",
        payload
      );

      setMessage(t("finance.messages.planCreated"));
      setPlanForm({
        name: "",
        academic_year: planForm.academic_year,
        scope: "LEVEL",
        level: "",
        classroom: "",
        currency: "XAF",
        notes: "",
      });
      setInstallmentForm((current) => ({
        ...current,
        plan: String(data.id),
      }));
      await load();
    } catch (err) {
      setError(parseError(err, t("finance.errors.plan")));
    } finally {
      setSaving("");
    }
  };

  const addInstallment = async (event) => {
    event.preventDefault();
    setSaving("installment");
    setError("");
    setMessage("");

    try {
      await api.post(
        `/finance/plans/${installmentForm.plan}/installments/`,
        {
          name: installmentForm.name,
          amount: installmentForm.amount,
          due_date: installmentForm.due_date || null,
          order: Number(installmentForm.order),
          is_active: true,
        }
      );

      setMessage(t("finance.messages.installmentCreated"));
      setInstallmentForm((current) => ({
        ...current,
        name: "",
        amount: "",
        due_date: "",
        order: Number(current.order) + 1,
      }));
      await load();
    } catch (err) {
      setError(
        parseError(err, t("finance.errors.installment"))
      );
    } finally {
      setSaving("");
    }
  };

  const assignPlan = async (plan) => {
    const confirmed = window.confirm(
      t("finance.plan.assignConfirm")
    );
    if (!confirmed) return;

    setSaving(`assign-${plan.id}`);
    setError("");
    setMessage("");

    try {
      const { data } = await api.post(
        `/finance/plans/${plan.id}/assign/`,
        {}
      );
      setMessage(
        t("finance.messages.planAssigned", {
          created: data.created,
          updated: data.updated,
          unchanged: data.unchanged,
          conflicts: data.conflicts.length,
        })
      );
      await load();
    } catch (err) {
      setError(parseError(err, t("finance.errors.assign")));
    } finally {
      setSaving("");
    }
  };

  const afterPayment = async (data) => {
    setMessage(
      t("finance.messages.paymentSaved", {
        receipt: data.payment.receipt_number,
      })
    );
    await reloadFiltered();
  };

  const downloadReceipt = async (payment) => {
    setSaving(`receipt-${payment.id}`);
    setError("");

    try {
      const { data } = await api.get(
        `/finance/payments/${payment.id}/receipt/`,
        { responseType: "blob" }
      );

      downloadBlob(
        data,
        `${payment.receipt_number}.pdf`
      );
    } catch (err) {
      setError(parseError(err, t("finance.errors.receipt")));
    } finally {
      setSaving("");
    }
  };

  if (loading) {
    return (
      <div className="grid min-h-[300px] place-items-center rounded-3xl border border-slate-200 bg-white">
        <div className="inline-flex items-center gap-2 text-sm text-slate-500">
          <Loader2 size={18} className="animate-spin" />
          {t("finance.loading")}
        </div>
      </div>
    );
  }

  const tabs = [
    ["dashboard", t("finance.tabs.dashboard"), WalletCards],
    ["accounts", t("finance.tabs.accounts"), Banknote],
    ["payments", t("finance.tabs.payments"), ReceiptText],
    ...(canConfigure
      ? [["plans", t("finance.tabs.plans"), Settings2]]
      : []),
  ];

  return (
    <div className="space-y-5">
      <PaymentDialog
        open={paymentDialog.open}
        account={paymentDialog.account}
        t={t}
        onClose={() =>
          setPaymentDialog({ open: false, account: null })
        }
        onSaved={afterPayment}
      />

      <div className="flex flex-col justify-between gap-4 xl:flex-row xl:items-end">
        <div>
          <div className="text-xs font-medium uppercase tracking-[0.18em] text-slate-400">
            {t("finance.step")}
          </div>
          <h1 className="mt-2 text-2xl font-semibold">
            {t("finance.title")}
          </h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">
            {t("finance.description")}
          </p>
        </div>

        {syncing && (
          <span className="inline-flex items-center gap-2 text-xs text-slate-400">
            <RefreshCw size={13} className="animate-spin" />
            {t("finance.syncing")}
          </span>
        )}
      </div>

      {error && (
        <div className="rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {error}
        </div>
      )}

      {message && (
        <div className="rounded-2xl bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          {message}
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

      {tab !== "plans" && (
        <section className="rounded-3xl border border-slate-200 bg-white p-5">
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <select
              className={inputClass}
              value={yearId}
              onChange={(event) => {
                setYearId(event.target.value);
                setClassroomId("");
              }}
            >
              <option value="">{t("finance.filters.allYears")}</option>
              {options.years.map((year) => (
                <option key={year.id} value={year.id}>
                  {year.name}
                </option>
              ))}
            </select>

            <select
              className={inputClass}
              value={classroomId}
              onChange={(event) =>
                setClassroomId(event.target.value)
              }
            >
              <option value="">
                {t("finance.filters.allClasses")}
              </option>
              {classrooms.map((classroom) => (
                <option key={classroom.id} value={classroom.id}>
                  {classroom.name} • {classroom.level_name}
                </option>
              ))}
            </select>

            {(tab === "accounts" || tab === "payments") && (
              <div className="relative">
                <Search
                  size={16}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
                />
                <input
                  className={`${inputClass} pl-9`}
                  value={search}
                  onChange={(event) =>
                    setSearch(event.target.value)
                  }
                  onKeyDown={(event) => {
                    if (event.key === "Enter") {
                      reloadFiltered();
                    }
                  }}
                  placeholder={t("finance.filters.search")}
                />
              </div>
            )}

            {tab === "accounts" && (
              <select
                className={inputClass}
                value={paymentStatus}
                onChange={(event) =>
                  setPaymentStatus(event.target.value)
                }
              >
                <option value="">
                  {t("finance.filters.allStatuses")}
                </option>
                <option value="PAID">
                  {t("finance.status.paid")}
                </option>
                <option value="PARTIAL">
                  {t("finance.status.partial")}
                </option>
                <option value="UNPAID">
                  {t("finance.status.unpaid")}
                </option>
              </select>
            )}

            {(tab === "accounts" || tab === "payments") && (
              <button
                type="button"
                onClick={reloadFiltered}
                className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-medium hover:bg-slate-50"
              >
                <Search size={16} />
                {t("finance.filters.apply")}
              </button>
            )}
          </div>
        </section>
      )}

      {tab === "dashboard" && dashboard && (
        <div className="space-y-5">
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <Metric
              label={t("finance.dashboard.expected")}
              value={money(dashboard.expected_total)}
            />
            <Metric
              label={t("finance.dashboard.collected")}
              value={money(dashboard.collected_total)}
              help={`${dashboard.collection_rate}%`}
            />
            <Metric
              label={t("finance.dashboard.outstanding")}
              value={money(dashboard.outstanding_total)}
            />
            <Metric
              label={t("finance.dashboard.today")}
              value={money(dashboard.payments_today)}
            />
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-5">
              <div className="text-xs font-medium text-emerald-700">
                {t("finance.status.paid")}
              </div>
              <div className="mt-2 text-3xl font-semibold text-emerald-900">
                {dashboard.paid_count}
              </div>
            </div>

            <div className="rounded-2xl border border-amber-200 bg-amber-50 p-5">
              <div className="text-xs font-medium text-amber-700">
                {t("finance.status.partial")}
              </div>
              <div className="mt-2 text-3xl font-semibold text-amber-900">
                {dashboard.partial_count}
              </div>
            </div>

            <div className="rounded-2xl border border-rose-200 bg-rose-50 p-5">
              <div className="text-xs font-medium text-rose-700">
                {t("finance.status.unpaid")}
              </div>
              <div className="mt-2 text-3xl font-semibold text-rose-900">
                {dashboard.unpaid_count}
              </div>
            </div>
          </div>
        </div>
      )}

      {tab === "accounts" && (
        <section className="rounded-3xl border border-slate-200 bg-white p-6">
          <div>
            <h2 className="font-semibold">
              {t("finance.accounts.title")}
            </h2>
            <p className="mt-1 text-xs text-slate-500">
              {t("finance.accounts.help")}
            </p>
          </div>

          <div className="mt-5 overflow-x-auto">
            <table className="w-full min-w-[940px] text-left text-sm">
              <thead className="text-xs uppercase text-slate-400">
                <tr>
                  <th className="px-3 py-3">
                    {t("finance.fields.student")}
                  </th>
                  <th className="px-3 py-3">
                    {t("finance.fields.classroom")}
                  </th>
                  <th className="px-3 py-3">
                    {t("finance.fields.plan")}
                  </th>
                  <th className="px-3 py-3">
                    {t("finance.fields.expected")}
                  </th>
                  <th className="px-3 py-3">
                    {t("finance.fields.paid")}
                  </th>
                  <th className="px-3 py-3">
                    {t("finance.fields.balance")}
                  </th>
                  <th className="px-3 py-3">
                    {t("finance.fields.status")}
                  </th>
                  <th className="px-3 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {accounts.map((account) => (
                  <tr key={account.id}>
                    <td className="px-3 py-3">
                      <div className="font-medium">
                        {account.student_name}
                      </div>
                      <div className="text-xs text-slate-400">
                        {account.matricule}
                      </div>
                    </td>
                    <td className="px-3 py-3">
                      {account.classroom_name}
                    </td>
                    <td className="px-3 py-3">
                      {account.plan_name}
                    </td>
                    <td className="px-3 py-3">
                      {money(
                        account.expected_amount,
                        account.currency
                      )}
                    </td>
                    <td className="px-3 py-3 font-medium">
                      {money(
                        account.paid_amount,
                        account.currency
                      )}
                    </td>
                    <td className="px-3 py-3 font-semibold">
                      {money(
                        account.balance,
                        account.currency
                      )}
                    </td>
                    <td className="px-3 py-3">
                      <StatusBadge
                        status={account.payment_status}
                        t={t}
                      />
                    </td>
                    <td className="px-3 py-3 text-right">
                      <button
                        type="button"
                        disabled={Number(account.balance) <= 0}
                        onClick={() =>
                          setPaymentDialog({
                            open: true,
                            account,
                          })
                        }
                        className="inline-flex items-center gap-1.5 rounded-xl bg-slate-950 px-3 py-2 text-xs font-medium text-white disabled:opacity-30"
                      >
                        <Plus size={14} />
                        {t("finance.accounts.pay")}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {!accounts.length && (
              <div className="py-12 text-center text-sm text-slate-500">
                {t("finance.accounts.empty")}
              </div>
            )}
          </div>
        </section>
      )}

      {tab === "payments" && (
        <section className="rounded-3xl border border-slate-200 bg-white p-6">
          <div>
            <h2 className="font-semibold">
              {t("finance.payments.title")}
            </h2>
            <p className="mt-1 text-xs text-slate-500">
              {t("finance.payments.help")}
            </p>
          </div>

          <div className="mt-5 overflow-x-auto">
            <table className="w-full min-w-[900px] text-left text-sm">
              <thead className="text-xs uppercase text-slate-400">
                <tr>
                  <th className="px-3 py-3">
                    {t("finance.fields.receipt")}
                  </th>
                  <th className="px-3 py-3">
                    {t("finance.fields.student")}
                  </th>
                  <th className="px-3 py-3">
                    {t("finance.fields.amount")}
                  </th>
                  <th className="px-3 py-3">
                    {t("finance.fields.method")}
                  </th>
                  <th className="px-3 py-3">
                    {t("finance.fields.date")}
                  </th>
                  <th className="px-3 py-3">
                    {t("finance.fields.reference")}
                  </th>
                  <th className="px-3 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {payments.map((payment) => (
                  <tr key={payment.id}>
                    <td className="px-3 py-3 font-mono text-xs">
                      {payment.receipt_number}
                    </td>
                    <td className="px-3 py-3">
                      <div className="font-medium">
                        {payment.student_name}
                      </div>
                      <div className="text-xs text-slate-400">
                        {payment.classroom_name}
                      </div>
                    </td>
                    <td className="px-3 py-3 font-semibold">
                      {money(payment.amount, payment.currency)}
                    </td>
                    <td className="px-3 py-3">
                      {payment.method_label}
                    </td>
                    <td className="px-3 py-3">
                      {new Date(payment.paid_at).toLocaleString()}
                    </td>
                    <td className="px-3 py-3">
                      {payment.reference || "—"}
                    </td>
                    <td className="px-3 py-3 text-right">
                      <button
                        type="button"
                        onClick={() => downloadReceipt(payment)}
                        className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 px-3 py-2 text-xs font-medium hover:bg-slate-50"
                      >
                        <Download size={14} />
                        PDF
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {!payments.length && (
              <div className="py-12 text-center text-sm text-slate-500">
                {t("finance.payments.empty")}
              </div>
            )}
          </div>
        </section>
      )}

      {tab === "plans" && canConfigure && (
        <div className="grid gap-5 xl:grid-cols-[.85fr_1.15fr]">
          <div className="space-y-5">
            <form
              onSubmit={createPlan}
              className="rounded-3xl border border-slate-200 bg-white p-6"
            >
              <h2 className="font-semibold">
                {t("finance.plan.create")}
              </h2>

              <div className="mt-5 space-y-4">
                <input
                  required
                  className={inputClass}
                  value={planForm.name}
                  onChange={(event) =>
                    setPlanForm({
                      ...planForm,
                      name: event.target.value,
                    })
                  }
                  placeholder={t("finance.plan.namePlaceholder")}
                />

                <select
                  required
                  className={inputClass}
                  value={planForm.academic_year}
                  onChange={(event) =>
                    setPlanForm({
                      ...planForm,
                      academic_year: event.target.value,
                      classroom: "",
                    })
                  }
                >
                  <option value="">
                    {t("common.choose")}
                  </option>
                  {options.years.map((year) => (
                    <option key={year.id} value={year.id}>
                      {year.name}
                    </option>
                  ))}
                </select>

                <select
                  className={inputClass}
                  value={planForm.scope}
                  onChange={(event) =>
                    setPlanForm({
                      ...planForm,
                      scope: event.target.value,
                      level: "",
                      classroom: "",
                    })
                  }
                >
                  <option value="LEVEL">
                    {t("finance.plan.scopeLevel")}
                  </option>
                  <option value="CLASSROOM">
                    {t("finance.plan.scopeClass")}
                  </option>
                  <option value="SCHOOL">
                    {t("finance.plan.scopeYear")}
                  </option>
                </select>

                {planForm.scope === "LEVEL" && (
                  <select
                    required
                    className={inputClass}
                    value={planForm.level}
                    onChange={(event) =>
                      setPlanForm({
                        ...planForm,
                        level: event.target.value,
                      })
                    }
                  >
                    <option value="">
                      {t("common.choose")}
                    </option>
                    {options.levels.map((level) => (
                      <option key={level.id} value={level.id}>
                        {level.name} • {level.cycle_name}
                      </option>
                    ))}
                  </select>
                )}

                {planForm.scope === "CLASSROOM" && (
                  <select
                    required
                    className={inputClass}
                    value={planForm.classroom}
                    onChange={(event) =>
                      setPlanForm({
                        ...planForm,
                        classroom: event.target.value,
                      })
                    }
                  >
                    <option value="">
                      {t("common.choose")}
                    </option>
                    {options.classrooms
                      .filter(
                        (item) =>
                          String(item.academic_year) ===
                          String(planForm.academic_year)
                      )
                      .map((classroom) => (
                        <option
                          key={classroom.id}
                          value={classroom.id}
                        >
                          {classroom.name} •{" "}
                          {classroom.level_name}
                        </option>
                      ))}
                  </select>
                )}

                <button
                  className={primaryButton}
                  disabled={saving === "plan"}
                >
                  <Plus size={16} />
                  {t("finance.plan.createButton")}
                </button>
              </div>
            </form>

            <form
              onSubmit={addInstallment}
              className="rounded-3xl border border-slate-200 bg-white p-6"
            >
              <h2 className="font-semibold">
                {t("finance.installment.create")}
              </h2>

              <div className="mt-5 space-y-4">
                <select
                  required
                  className={inputClass}
                  value={installmentForm.plan}
                  onChange={(event) =>
                    setInstallmentForm({
                      ...installmentForm,
                      plan: event.target.value,
                    })
                  }
                >
                  <option value="">
                    {t("common.choose")}
                  </option>
                  {plans.map((plan) => (
                    <option key={plan.id} value={plan.id}>
                      {plan.name}
                    </option>
                  ))}
                </select>

                <input
                  required
                  className={inputClass}
                  value={installmentForm.name}
                  onChange={(event) =>
                    setInstallmentForm({
                      ...installmentForm,
                      name: event.target.value,
                    })
                  }
                  placeholder={t(
                    "finance.installment.namePlaceholder"
                  )}
                />

                <input
                  required
                  min="1"
                  step="1"
                  type="number"
                  className={inputClass}
                  value={installmentForm.amount}
                  onChange={(event) =>
                    setInstallmentForm({
                      ...installmentForm,
                      amount: event.target.value,
                    })
                  }
                  placeholder={t(
                    "finance.installment.amountPlaceholder"
                  )}
                />

                <input
                  type="date"
                  className={inputClass}
                  value={installmentForm.due_date}
                  onChange={(event) =>
                    setInstallmentForm({
                      ...installmentForm,
                      due_date: event.target.value,
                    })
                  }
                />

                <input
                  required
                  min="1"
                  type="number"
                  className={inputClass}
                  value={installmentForm.order}
                  onChange={(event) =>
                    setInstallmentForm({
                      ...installmentForm,
                      order: event.target.value,
                    })
                  }
                />

                <button
                  className={primaryButton}
                  disabled={saving === "installment"}
                >
                  <Plus size={16} />
                  {t("finance.installment.addButton")}
                </button>
              </div>
            </form>
          </div>

          <section className="rounded-3xl border border-slate-200 bg-white p-6">
            <div>
              <h2 className="font-semibold">
                {t("finance.plan.list")}
              </h2>
              <p className="mt-1 text-xs text-slate-500">
                {t("finance.plan.help")}
              </p>
            </div>

            <div className="mt-5 space-y-4">
              {plans.map((plan) => (
                <div
                  key={plan.id}
                  className="rounded-2xl border border-slate-200 p-4"
                >
                  <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
                    <div>
                      <div className="font-medium">
                        {plan.name}
                      </div>
                      <div className="mt-1 text-xs text-slate-500">
                        {plan.academic_year_name}
                        {" • "}
                        {plan.classroom_name ||
                          plan.level_name ||
                          t("finance.plan.wholeYear")}
                      </div>
                    </div>

                    <div className="text-right">
                      <div className="text-lg font-semibold">
                        {money(plan.total_amount, plan.currency)}
                      </div>
                      <div className="text-xs text-slate-400">
                        {t("finance.plan.accounts", {
                          count: plan.assigned_accounts_count,
                        })}
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 space-y-2">
                    {plan.installments.map((item) => (
                      <div
                        key={item.id}
                        className="flex items-center justify-between rounded-xl bg-slate-50 px-3 py-2 text-sm"
                      >
                        <span>
                          {item.order}. {item.name}
                          {item.due_date
                            ? ` • ${item.due_date}`
                            : ""}
                        </span>
                        <span className="font-medium">
                          {money(item.amount, plan.currency)}
                        </span>
                      </div>
                    ))}

                    {!plan.installments.length && (
                      <div className="rounded-xl bg-amber-50 px-3 py-2 text-xs text-amber-700">
                        {t("finance.plan.noInstallments")}
                      </div>
                    )}
                  </div>

                  <div className="mt-4 flex justify-end">
                    <button
                      type="button"
                      onClick={() => assignPlan(plan)}
                      disabled={
                        !plan.installments.length ||
                        saving === `assign-${plan.id}`
                      }
                      className="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-xs font-medium hover:bg-slate-50 disabled:opacity-40"
                    >
                      <CheckCircle2 size={14} />
                      {t("finance.plan.assign")}
                    </button>
                  </div>
                </div>
              ))}

              {!plans.length && (
                <div className="rounded-2xl bg-slate-50 p-8 text-center text-sm text-slate-500">
                  {t("finance.plan.empty")}
                </div>
              )}
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
