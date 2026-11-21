import { useEffect, useState } from "react";

export const TYPE_LABELS = {
  add_server: "Add a server",
  open_port: "Open a port",
  grant_access: "Grant access",
  change_config: "Change a configuration",
};
export const STATUS_LABELS = {
  submitted: "Submitted",
  reviewed: "AI reviewed",
  manual_review: "Manual review needed",
  approved: "Approved",
  rejected: "Rejected",
};
export const fmt = (iso) => (iso ? new Date(iso).toLocaleString() : "");

export function Risk({ level }) {
  if (!level) return <span className="muted">Not reviewed</span>;
  return <span className={`risk risk-${level}`}>{level} risk</span>;
}

export function Status({ value }) {
  return <span className={`status status-${value}`}>{STATUS_LABELS[value] ?? value}</span>;
}

export function ErrorMessage({ error }) {
  return error ? <p role="alert" className="error">{error}</p> : null;
}

export function Field({ id, label, hint, children }) {
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      {hint && <p id={`${id}-hint`} className="hint">{hint}</p>}
      {children}
    </div>
  );
}

// Small data-loading hook with loading and error states.
export function useLoad(fn, deps) {
  const [state, setState] = useState({ loading: true, data: null, error: "" });
  const [tick, setTick] = useState(0);
  useEffect(() => {
    let live = true;
    setState((s) => ({ ...s, loading: true, error: "" }));
    fn()
      .then((data) => live && setState({ loading: false, data, error: "" }))
      .catch((e) => live && setState({ loading: false, data: null, error: e.message }));
    return () => { live = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);
  return { ...state, reload: () => setTick((t) => t + 1) };
}
