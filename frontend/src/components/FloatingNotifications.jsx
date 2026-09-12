import { useCallback, useEffect, useRef, useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  Info,
  TriangleAlert,
  X,
} from "lucide-react";
import { TOAST_EVENT_NAME } from "../lib/toast";

const typeMeta = {
  success: {
    icon: CheckCircle2,
    label: "Succès",
    classes: "toast-success",
  },
  error: {
    icon: AlertCircle,
    label: "Erreur",
    classes: "toast-error",
  },
  warning: {
    icon: TriangleAlert,
    label: "Attention",
    classes: "toast-warning",
  },
  info: {
    icon: Info,
    label: "Information",
    classes: "toast-info",
  },
};

function detectLegacyNotification(element) {
  if (!(element instanceof HTMLElement)) return null;
  if (element.closest("[data-toast-root='true']")) return null;
  if (element.dataset.toastCaptured === "true") return null;
  if (element.classList.contains("rounded-full")) return null;

  const text = element.textContent?.trim();
  if (!text || text.length > 700) return null;

  const classes = element.classList;
  const isMessageBox =
    classes.contains("text-sm") &&
    (classes.contains("py-3") ||
      classes.contains("p-3") ||
      classes.contains("p-4"));

  if (!isMessageBox) return null;

  if (
    classes.contains("bg-emerald-50") &&
    (classes.contains("text-emerald-700") ||
      classes.contains("text-emerald-800") ||
      classes.contains("text-emerald-900"))
  ) {
    return { type: "success", message: text };
  }

  if (
    classes.contains("bg-rose-50") &&
    (classes.contains("text-rose-700") ||
      classes.contains("text-rose-800") ||
      classes.contains("text-rose-900"))
  ) {
    return { type: "error", message: text };
  }

  return null;
}

export default function FloatingNotifications() {
  const [toasts, setToasts] = useState([]);
  const timers = useRef(new Map());

  const dismiss = useCallback((id) => {
    const timer = timers.current.get(id);
    if (timer) {
      window.clearTimeout(timer);
      timers.current.delete(id);
    }
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const push = useCallback(
    ({ type = "info", message, title = "", duration = 4200 }) => {
      const normalizedMessage = String(message || "").trim();
      if (!normalizedMessage) return;

      const id = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
      const toast = {
        id,
        type: typeMeta[type] ? type : "info",
        message: normalizedMessage,
        title,
      };

      setToasts((current) => {
        const duplicate = current.find(
          (item) =>
            item.type === toast.type && item.message === toast.message
        );
        if (duplicate) return current;
        return [...current.slice(-3), toast];
      });

      const timer = window.setTimeout(() => dismiss(id), duration);
      timers.current.set(id, timer);
    },
    [dismiss]
  );

  useEffect(() => {
    const handler = (event) => push(event.detail || {});
    window.addEventListener(TOAST_EVENT_NAME, handler);
    return () => window.removeEventListener(TOAST_EVENT_NAME, handler);
  }, [push]);

  useEffect(() => {
    const capture = (root) => {
      const nodes = [];
      if (root instanceof HTMLElement) nodes.push(root);
      if (root?.querySelectorAll) {
        root
          .querySelectorAll(
            ".bg-emerald-50.text-emerald-700, .bg-emerald-50.text-emerald-800, .bg-emerald-50.text-emerald-900, .bg-rose-50.text-rose-700, .bg-rose-50.text-rose-800, .bg-rose-50.text-rose-900"
          )
          .forEach((node) => nodes.push(node));
      }

      nodes.forEach((node) => {
        const legacy = detectLegacyNotification(node);
        if (!legacy) return;

        node.dataset.toastCaptured = "true";
        node.setAttribute("aria-hidden", "true");
        node.style.display = "none";
        push(legacy);
      });
    };

    capture(document.body);

    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => capture(node));
      });
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });

    return () => observer.disconnect();
  }, [push]);

  useEffect(
    () => () => {
      timers.current.forEach((timer) => window.clearTimeout(timer));
      timers.current.clear();
    },
    []
  );

  return (
    <div
      data-toast-root="true"
      className="pointer-events-none fixed inset-x-0 top-3 z-[100] flex flex-col items-center gap-2 px-3 sm:inset-x-auto sm:right-4 sm:top-4 sm:w-[min(390px,calc(100vw-2rem))] sm:items-stretch sm:px-0"
      aria-live="polite"
      aria-atomic="false"
    >
      {toasts.map((toast) => {
        const meta = typeMeta[toast.type] || typeMeta.info;
        const Icon = meta.icon;

        return (
          <div
            key={toast.id}
            className={`toast-card pointer-events-auto w-full overflow-hidden rounded-2xl border bg-white/95 shadow-2xl backdrop-blur-xl ${meta.classes}`}
            role={toast.type === "error" ? "alert" : "status"}
          >
            <div className="flex gap-3 p-3.5 sm:p-4">
              <div className="toast-icon grid h-9 w-9 shrink-0 place-items-center rounded-xl">
                <Icon size={18} />
              </div>

              <div className="min-w-0 flex-1 pt-0.5">
                <div className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">
                  {toast.title || meta.label}
                </div>
                <div className="mt-1 break-words text-sm font-medium leading-5 text-slate-800">
                  {toast.message}
                </div>
              </div>

              <button
                type="button"
                onClick={() => dismiss(toast.id)}
                className="grid h-8 w-8 shrink-0 place-items-center rounded-lg text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
                aria-label="Fermer la notification"
              >
                <X size={16} />
              </button>
            </div>
            <div className="toast-progress h-1 origin-left" />
          </div>
        );
      })}
    </div>
  );
}
