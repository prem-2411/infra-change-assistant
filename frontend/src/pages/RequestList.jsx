import { useState } from "react";
import { api } from "../api.js";
import { ErrorMessage, fmt, Risk, Status, STATUS_LABELS, TYPE_LABELS, useLoad } from "../ui.jsx";

export default function RequestList({ user, onOpen }) {
  const [status, setStatus] = useState("");
  const { loading, data, error } = useLoad(() => api.listRequests(status), [status]);
  const title = user.role === "engineer" ? "My requests" : user.role === "approver" ? "Approval queue" : "All requests";

  return (
    <section>
      <h1>{title}</h1>
      <div className="toolbar">
        <label htmlFor="status">Show</label>
        <select id="status" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All statuses</option>
          {Object.entries(STATUS_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
      </div>
      <ErrorMessage error={error} />
      {loading && <p role="status">Loading requests…</p>}
      {!loading && !error && data?.length === 0 && (
        <p className="empty">
          {user.role === "engineer" ? "You have no requests yet. Use New request to submit one." : "No requests match this filter."}
        </p>
      )}
      {data?.length > 0 && (
        <div className="scroll">
          <table>
            <caption className="sr">Change requests</caption>
            <thead>
              <tr><th scope="col">Request</th><th scope="col">Type</th><th scope="col">Status</th>
                <th scope="col">AI risk</th><th scope="col">Requested by</th><th scope="col">Submitted</th></tr>
            </thead>
            <tbody>
              {data.map((r) => (
                <tr key={r.id} className={`row-${r.status}`}>
                  <th scope="row">
                    <button className="linklike" onClick={() => onOpen(r.id)}>#{r.id} {r.target}</button>
                  </th>
                  <td>{TYPE_LABELS[r.type]}</td>
                  <td><Status value={r.status} /></td>
                  <td><Risk level={r.ai_risk} /></td>
                  <td>{r.requester_name}</td>
                  <td>{fmt(r.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
