import { Building2 } from "lucide-react";

export default function SchoolIdentity({ school, compact = false }) {
  const size = compact ? "h-9 w-9" : "h-12 w-12";

  return (
    <div className="flex min-w-0 items-center gap-3">
      <div
        className={`${size} grid shrink-0 place-items-center overflow-hidden rounded-2xl text-white`}
        style={{ backgroundColor: school?.primary_color || "#0f172a" }}
      >
        {school?.logo ? (
          <img
            src={school.logo}
            alt=""
            className="h-full w-full object-cover"
          />
        ) : (
          <Building2 size={compact ? 17 : 21} />
        )}
      </div>

      <div className="min-w-0">
        <div className="truncate font-semibold tracking-tight">
          {school?.name || "Établissement"}
        </div>
        {!compact && school?.motto && (
          <div className="truncate text-xs text-slate-500">{school.motto}</div>
        )}
      </div>
    </div>
  );
}
