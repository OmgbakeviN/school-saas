export default function Field({ label, hint, error, children }) {
  return (
    <label className="block">
      <div className="mb-1.5 flex items-end justify-between gap-3">
        <span className="text-sm font-medium text-slate-800">{label}</span>
        {hint ? <span className="text-xs text-slate-400">{hint}</span> : null}
      </div>
      {children}
      {error ? <div className="mt-1.5 text-xs text-rose-600">{error}</div> : null}
    </label>
  );
}
