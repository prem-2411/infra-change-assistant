import { useState } from "react";
import { api } from "../api.js";
import { ErrorMessage, Field, TYPE_LABELS } from "../ui.jsx";

export default function RequestForm({ onCreated }) {
  const [form, setForm] = useState({ type: "add_server", target: "", risk_level: "low", justification: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const created = await api.createRequest(form);
      onCreated(created.id);
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  return (
    <section>
      <h1>New change request</h1>
      <form onSubmit={submit} className="stack">
        <Field id="type" label="What do you want to change?">
          <select id="type" value={form.type} onChange={set("type")}>
            {Object.entries(TYPE_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </Field>
        <Field id="target" label="Target system" hint="For example prod-api-node-09 or staging-db-02:5432.">
          <input id="target" required maxLength={200} value={form.target} onChange={set("target")}
                 aria-describedby="target-hint" />
        </Field>
        <Field id="risk" label="Your risk estimate" hint="The AI judges risk independently of this.">
          <select id="risk" value={form.risk_level} onChange={set("risk_level")} aria-describedby="risk-hint">
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </Field>
        <Field id="justification" label="Justification"
               hint="Say why, the environment, who approved it, and your rollback plan and change window. At least 10 characters.">
          <textarea id="justification" required minLength={10} maxLength={2000} rows={6}
                    value={form.justification} onChange={set("justification")} aria-describedby="justification-hint" />
        </Field>
        <ErrorMessage error={error} />
        <button className="primary" disabled={busy}>{busy ? "Submitting…" : "Submit request"}</button>
      </form>
    </section>
  );
}
