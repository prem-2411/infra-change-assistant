import { api } from "../api.js";
import { ErrorMessage, STATUS_LABELS, useLoad } from "../ui.jsx";

const mins = (s) => (s == null ? "No decisions yet" : s < 120 ? `${Math.round(s)} seconds` : `${(s / 60).toFixed(1)} minutes`);

function Counts({ title, counts, labels = {} }) {
  const entries = Object.entries(counts);
  return (
    <section className="panel">
      <h2>{title}</h2>
      {entries.length === 0 ? <p className="empty">Nothing yet.</p> : (
        <dl className="counts">
          {entries.map(([k, v]) => <div key={k}><dt>{labels[k] ?? k}</dt><dd>{v}</dd></div>)}
        </dl>
      )}
    </section>
  );
}

export default function Insights({ user }) {
  const dash = useLoad(() => api.dashboard(), []);
  const metrics = useLoad(() => (user.role === "admin" ? api.metrics() : Promise.resolve(null)), [user.role]);
  const d = dash.data;

  return (
    <section>
      <h1>Dashboard</h1>
      <ErrorMessage error={dash.error || metrics.error} />
      {dash.loading && <p role="status">Loading…</p>}
      {d && (
        <>
          <p className="big">{d.total} requests. Average time to decision: {mins(d.avg_review_seconds)}.</p>
          <div className="grid">
            <Counts title="By status" counts={d.by_status} labels={STATUS_LABELS} />
            <Counts title="Risk claimed by requesters" counts={d.by_claimed_risk} />
            <Counts title="Risk found by the AI review" counts={d.by_ai_risk} />
          </div>
        </>
      )}
      {metrics.data && (
        <>
          <h2>Service health</h2>
          <dl className="counts metrics">
            {Object.entries(metrics.data).map(([k, v]) => <div key={k}><dt>{k.replaceAll("_", " ")}</dt><dd>{v}</dd></div>)}
          </dl>
        </>
      )}
    </section>
  );
}
