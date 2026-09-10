import { X } from "lucide-react";
import { useEffect } from "react";

export default function Dialog({
  open,
  title,
  description,
  onClose,
  children,
  footer,
  maxWidth = "max-w-xl",
}) {
  useEffect(() => {
    if (!open) return undefined;

    const onKeyDown = (event) => {
      if (event.key === "Escape") {
        onClose?.();
      }
    };

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", onKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 p-4 backdrop-blur-sm"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onClose?.();
        }
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={`max-h-[90vh] w-full ${maxWidth} overflow-hidden rounded-3xl border border-white/60 bg-white shadow-2xl`}
      >
        <div className="flex items-start justify-between gap-5 border-b border-slate-100 px-6 py-5">
          <div className="min-w-0">
            <h2 className="text-lg font-semibold tracking-tight text-slate-950">
              {title}
            </h2>
            {description && (
              <p className="mt-1 text-sm leading-6 text-slate-500">
                {description}
              </p>
            )}
          </div>

          <button
            type="button"
            onClick={onClose}
            className="grid h-9 w-9 shrink-0 place-items-center rounded-xl text-slate-400 hover:bg-slate-100 hover:text-slate-700"
            aria-label="Close"
          >
            <X size={17} />
          </button>
        </div>

        <div className="max-h-[65vh] overflow-y-auto px-6 py-5">
          {children}
        </div>

        {footer && (
          <div className="border-t border-slate-100 bg-slate-50/70 px-6 py-4">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}
