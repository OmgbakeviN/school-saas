import { useState } from "react";
import { BookOpenCheck, Layers3 } from "lucide-react";

import { useI18n } from "../../i18n";
import AcademicsPanel from "./AcademicsPanel";
import CurriculumPanel from "./CurriculumPanel";

export default function AcademicWorkspace({ canManage, onCountsChanged }) {
  const { t } = useI18n();
  const [workspace, setWorkspace] = useState("structure");

  return (
    <div className="space-y-5">
      <div className="inline-flex max-w-full gap-1 overflow-x-auto rounded-2xl border border-slate-200 bg-white p-1.5">
        <button
          type="button"
          onClick={() => setWorkspace("structure")}
          className={`inline-flex shrink-0 items-center gap-2 rounded-xl px-4 py-2.5 text-sm ${
            workspace === "structure"
              ? "bg-slate-950 text-white"
              : "text-slate-600 hover:bg-slate-50"
          }`}
        >
          <Layers3 size={16} />
          {t("academicWorkspace.structure")}
        </button>

        <button
          type="button"
          onClick={() => setWorkspace("curriculum")}
          className={`inline-flex shrink-0 items-center gap-2 rounded-xl px-4 py-2.5 text-sm ${
            workspace === "curriculum"
              ? "bg-slate-950 text-white"
              : "text-slate-600 hover:bg-slate-50"
          }`}
        >
          <BookOpenCheck size={16} />
          {t("academicWorkspace.curriculum")}
        </button>
      </div>

      {workspace === "structure" ? (
        <AcademicsPanel
          canManage={canManage}
          onCountsChanged={onCountsChanged}
        />
      ) : (
        <CurriculumPanel canManage={canManage} />
      )}
    </div>
  );
}
