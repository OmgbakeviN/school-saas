import { useEffect, useState } from "react";
import { Building2 } from "lucide-react";

export default function SchoolIdentity({ school, compact = false }) {
  const [logoFailed, setLogoFailed] = useState(false);
  const size = compact ? "h-9 w-9" : "h-12 w-12";

  useEffect(() => {
    setLogoFailed(false);
  }, [school?.logo]);

  const showLogo = Boolean(school?.logo) && !logoFailed;

  return (
    <div className="flex min-w-0 items-center gap-3">
      <div
        className={`${size} grid shrink-0 place-items-center overflow-hidden rounded-2xl text-white shadow-sm`}
        style={{
          backgroundColor:
            school?.primary_color || "var(--school-primary, #144dd2)",
        }}
      >
        {showLogo ? (
          <img
            src={school.logo}
            alt={school?.name ? `Logo ${school.name}` : "Logo établissement"}
            className="h-full w-full bg-white object-contain p-1"
            onError={() => setLogoFailed(true)}
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
          <div className="truncate text-xs text-slate-500">
            {school.motto}
          </div>
        )}
      </div>
    </div>
  );
}
