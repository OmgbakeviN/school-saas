import { GraduationCap } from "lucide-react";
import { useI18n } from "../i18n";

export default function Brand() {
  const { t } = useI18n();

  return (
    <div className="flex items-center gap-3">
      <div className="grid h-10 w-10 place-items-center rounded-2xl bg-slate-950 text-white shadow-soft">
        <GraduationCap size={21} />
      </div>
      <div>
        <div className="font-semibold tracking-tight">{t("brand.name")}</div>
        <div className="text-xs text-slate-500">{t("brand.subtitle")}</div>
      </div>
    </div>
  );
}
