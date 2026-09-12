const EVENT_NAME = "be-wise-toast";

function emitToast(type, message, options = {}) {
  const text = String(message || "").trim();
  if (!text || typeof window === "undefined") return;

  window.dispatchEvent(
    new CustomEvent(EVENT_NAME, {
      detail: {
        type,
        message: text,
        title: options.title || "",
        duration: options.duration ?? 4200,
      },
    })
  );
}

export function notifySuccess(message, options) {
  emitToast("success", message, options);
}

export function notifyError(message, options) {
  emitToast("error", message, options);
}

export function notifyInfo(message, options) {
  emitToast("info", message, options);
}

export function notifyWarning(message, options) {
  emitToast("warning", message, options);
}

export { EVENT_NAME as TOAST_EVENT_NAME };
