import { useState } from "react";
import { api } from "../api.js";
import { ErrorMessage, Field, fmt, useLoad } from "../ui.jsx";

function Policies() {
  const { data, error, reload } = useLoad(() => api.policies(), []);
  const [form, setForm] = useState({ title: "", category: "", rule_text: "" });
  const [err, setErr] = useState("");
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function add(e) {
    e.preventDefault();
    setErr("");
    try { await api.createPolicy(form); setForm({ title: "", category: "", rule_text: "" }); reload(); }
    catch (x) { setErr(x.message); }
  }
  return (
    <section>
      <h2>Policies</h2>
      <ErrorMessage error={error} />
      <ul className="plain">
        {data?.map((p) => <li key={p.id}><strong>{p.title}</strong> <span className="muted">({p.category})</span><br />{p.rule_text}</li>)}
      </ul>
      <form onSubmit={add} className="stack">
        <h3>Add a policy</h3>
        <Field id="p-title" label="Title"><input id="p-title" required maxLength={200} value={form.title} onChange={set("title")} /></Field>
        <Field id="p-cat" label="Category"><input id="p-cat" required maxLength={50} value={form.category} onChange={set("category")} /></Field>
        <Field id="p-rule" label="Rule"><textarea id="p-rule" required maxLength={2000} rows={3} value={form.rule_text} onChange={set("rule_text")} /></Field>
        <ErrorMessage error={err} />
        <button className="secondary">Add policy</button>
      </form>
    </section>
  );
}

function Users() {
  const { data, error, reload } = useLoad(() => api.users(), []);
  const blank = { name: "", email: "", password: "", role: "engineer" };
  const [form, setForm] = useState(blank);
  const [err, setErr] = useState("");
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function add(e) {
    e.preventDefault();
    setErr("");
    try { await api.createUser(form); setForm(blank); reload(); } catch (x) { setErr(x.message); }
  }
  return (
    <section>
      <h2>Users</h2>
      <ErrorMessage error={error} />
      <ul className="plain">{data?.map((u) => <li key={u.id}>{u.name}, {u.email} ({u.role})</li>)}</ul>
      <form onSubmit={add} className="stack">
        <h3>Add a user</h3>
        <Field id="u-name" label="Name"><input id="u-name" required maxLength={100} value={form.name} onChange={set("name")} /></Field>
        <Field id="u-email" label="Email"><input id="u-email" type="email" required value={form.email} onChange={set("email")} /></Field>
        <Field id="u-pass" label="Temporary password" hint="12 to 72 characters.">
          <input id="u-pass" type="password" required minLength={12} maxLength={72} autoComplete="new-password"
                 value={form.password} onChange={set("password")} aria-describedby="u-pass-hint" />
        </Field>
        <Field id="u-role" label="Role">
          <select id="u-role" value={form.role} onChange={set("role")}>
            <option value="engineer">Engineer</option><option value="approver">Approver</option><option value="admin">Admin</option>
          </select>
        </Field>
        <ErrorMessage error={err} />
        <button className="secondary">Add user</button>
      </form>
    </section>
  );
}

function Audit() {
  const { loading, data, error } = useLoad(() => api.audit(), []);
  return (
    <section>
      <h2>Audit log</h2>
      <p className="hint">Append-only. Shows the latest 100 events.</p>
      <ErrorMessage error={error} />
      {loading && <p role="status">Loading…</p>}
      {data && (
        <div className="scroll">
          <table>
            <caption className="sr">Audit log</caption>
            <thead><tr><th scope="col">When</th><th scope="col">Actor</th><th scope="col">Action</th><th scope="col">Target</th><th scope="col">Details</th></tr></thead>
            <tbody>
              {data.map((e) => (
                <tr key={e.id}>
                  <td>{fmt(e.created_at)}</td><td>{e.actor_id ?? "none"}</td><td>{e.action}</td>
                  <td>{e.entity}{e.entity_id ? ` #${e.entity_id}` : ""}</td><td className="mono">{JSON.stringify(e.details)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

export default function Admin() {
  return (<><h1>Administration</h1><Policies /><Users /><Audit /></>);
}
