import { CheckSquare2, Square } from "lucide-react";

export default function LevelCheckboxSelector({
  levels,
  assignments,
  subjectId,
  value,
  onChange,
  t,
}) {
  const selected = new Set(value.map(Number));

  const grouped = levels.reduce((acc, level) => {
    const key = `${level.section_name}__${level.cycle_name}`;
    if (!acc[key]) {
      acc[key] = {
        section: level.section_name,
        cycle: level.cycle_name,
        levels: [],
      };
    }
    acc[key].levels.push(level);
    return acc;
  }, {});

  const toggle = (levelId) => {
    const id = Number(levelId);
    const next = new Set(selected);

    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
    }

    onChange(Array.from(next));
  };

  const selectAll = () => {
    onChange(levels.map((level) => Number(level.id)));
  };

  const clear = () => onChange([]);

  const isAlreadyAssigned = (levelId) =>
    assignments.some(
      (assignment) =>
        Number(assignment.level) === Number(levelId) &&
        Number(assignment.subject) === Number(subjectId)
    );

  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50/70 p-3">
      <div className="flex flex-col justify-between gap-2 border-b border-slate-200 pb-3 sm:flex-row sm:items-center">
        <div>
          <div className="text-sm font-medium text-slate-800">
            {t("curriculum.subjects.levels")}
          </div>
          <div className="mt-0.5 text-xs text-slate-500">
            {t("curriculum.subjects.levelSelectionHelp")}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-full bg-white px-2.5 py-1 text-xs font-medium text-slate-600">
            {t("curriculum.subjects.selectedCount", {
              count: selected.size,
            })}
          </span>
          <button
            type="button"
            onClick={selectAll}
            className="rounded-lg px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:bg-white"
          >
            {t("curriculum.subjects.selectAll")}
          </button>
          <button
            type="button"
            onClick={clear}
            className="rounded-lg px-2.5 py-1.5 text-xs font-medium text-slate-500 hover:bg-white"
          >
            {t("curriculum.subjects.clearSelection")}
          </button>
        </div>
      </div>

      <div className="mt-3 max-h-72 space-y-3 overflow-y-auto pr-1">
        {!levels.length && (
          <div className="px-2 py-4 text-center text-sm text-slate-500">
            {t("curriculum.subjects.noLevels")}
          </div>
        )}

        {Object.values(grouped).map((group) => (
          <div
            key={`${group.section}-${group.cycle}`}
            className="rounded-xl border border-slate-200 bg-white p-3"
          >
            <div className="mb-2 text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">
              {group.section} • {group.cycle}
            </div>

            <div className="grid gap-2 sm:grid-cols-2">
              {group.levels.map((level) => {
                const checked = selected.has(Number(level.id));
                const assigned = subjectId
                  ? isAlreadyAssigned(level.id)
                  : false;

                return (
                  <label
                    key={level.id}
                    className={`flex cursor-pointer items-center gap-3 rounded-xl border px-3 py-2.5 text-sm transition ${
                      checked
                        ? "border-slate-900 bg-slate-950 text-white"
                        : "border-slate-200 bg-white text-slate-700 hover:border-slate-300"
                    }`}
                  >
                    <input
                      type="checkbox"
                      className="sr-only"
                      checked={checked}
                      onChange={() => toggle(level.id)}
                    />

                    {checked ? (
                      <CheckSquare2 size={17} className="shrink-0" />
                    ) : (
                      <Square size={17} className="shrink-0 text-slate-400" />
                    )}

                    <span className="min-w-0 flex-1 truncate">
                      {level.name}
                    </span>

                    {assigned && (
                      <span
                        className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                          checked
                            ? "bg-white/15 text-white"
                            : "bg-amber-50 text-amber-700"
                        }`}
                      >
                        {t("curriculum.subjects.alreadyAssigned")}
                      </span>
                    )}
                  </label>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
