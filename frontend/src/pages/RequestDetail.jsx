import { useState } from "react";
import { api } from "../api.js";
import { ErrorMessage, Field, fmt, Risk, Status, TYPE_LABELS, useLoad } from "../ui.jsx";

const REC = { approve: "Approve", escalate: "Escalate to a human", reject: "Reject" };

function Review({ review }) {
  const failed = review.status === "failed";
  return (
    <article className="review">
      <h3>AI review <Risk level={review.risk_assessment} /></h3>
      {failed && (
        <p className="banner" role="note">
          Manual review needed. The AI review was unavailable, so this is a rule-based check only.
        </p>
      )}
      <p>{review.summary}</p>
      <p><strong>Suggested outcome:</strong> {REC[review.recommendation]} <span className="muted">
        (a suggestion only; the approver decides)</span></p>
      {review.risks.length > 0 && (<><h4>Risks</h4><ul>{review.risks.map((r, i) => <li key={i}>{r}</li>)}</ul></>)}
      {review.proposed_plan.length > 0 && (<><h4>Proposed plan</h4><ol>{review.proposed_plan.map((s, i) => <li key={i}>{s}</li>)}</ol></>)}
      <p className="muted">Reviewed by {review.model_name} on {fmt(review.created_at)}</p>
    </article>
  );
}

export default function RequestDetail({ id, user, onBack }) {
  const { loading, data: req, error, reload } = useLoad(() => api.getRequest(id), [id]);
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState("");
  const [decision, setDecision] = useState("approved");
  const [comment, setComment] = useState("");

  async function run(fn) {
    setBusy(true);
    setActionError("");
    try { await fn(); reload(); } catch (e) { setActionError(e.message); } finally { setBusy(false); }
  }

  if (loading && !req) return <p role="status">Loading request…</p>;
  if (error) return <><button className="linklike" onClick={onBack}>Back to list</button><ErrorMessage error={error} /></>;

  const decided = ["approved", "rejected"].includes(req.status);
  const canReview = !decided && ["engineer", "approver"].includes(user.role);
  const canDecide = user.role === "approver" && ["reviewed", "manual_review"].includes(req.status);

  return (
    <section>
      <button className="linklike" onClick={onBack}>Back to list</button>
      <h1>#{req.id} {req.target}</h1>
      <p><Status value={req.status} /></p>
      <dl className="facts">
        <div><dt>Type</dt><dd>{TYPE_LABELS[req.type]}</dd></div>
        <div><dt>Requested by</dt><dd>{req.requester_name}</dd></div>
        <div><dt>Their risk estimate</dt><dd>{req.risk_level}</dd></div>
        <div><dt>Submitted</dt><dd>{fmt(req.created_at)}</dd></div>
        <div className="wide"><dt>Justification</dt><dd className="prewrap">{req.justification}</dd></div>
      </dl>

      <h2>AI review</h2>
      <div aria-live="polite">
        {busy && <p role="status">Working… an AI review can take up to a minute.</p>}
        {req.reviews.length === 0 && !busy && <p className="empty">No AI review yet.</p>}
      </div>
      {canReview && (
        <button className="secondary" disabled={busy} onClick={() => run(() => api.review(id))}>
          {req.reviews.length ? "Run the review again" : "Run AI review"}
        </button>
      )}
      {req.reviews[0] && <Review review={req.reviews[0]} />}
      <ErrorMessage error={actionError} />

      {req.decisions.length > 0 && (
        <>
          <h2>Decision</h2>
          {req.decisions.map((d) => (
            <p key={d.id}><strong>{d.decision === "approved" ? "Approved" : "Rejected"}</strong> by {d.approver_name} on {fmt(d.created_at)}.
              <br />{d.comment}</p>
          ))}
        </>
      )}

      {canDecide && (
        <form onSubmit={(e) => { e.preventDefault(); run(() => api.decide(id, { decision, comment })); }} className="stack">
          <h2>Your decision</h2>
          <fieldset>
            <legend>Decision</legend>
            <label><input type="radio" name="decision" value="approved" checked={decision === "approved"}
                          onChange={() => setDecision("approved")} /> Approve</label>
            <label><input type="radio" name="decision" value="rejected" checked={decision === "rejected"}
                          onChange={() => setDecision("rejected")} /> Reject</label>
          </fieldset>
          <Field id="comment" label="Comment (required)">
            <textarea id="comment" required maxLength={1000} rows={3} value={comment}
                      onChange={(e) => setComment(e.target.value)} />
          </Field>
          <button className="primary" disabled={busy}>Record decision</button>
        </form>
      )}
    </section>
  );
}
