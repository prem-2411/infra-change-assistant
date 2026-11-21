from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .. import agent, audit
from ..db import get_db
from ..models import ChangeRequest, Decision, User
from ..ratelimit import review_limit
from ..schemas import DecisionIn, RequestDetail, RequestIn, RequestOut, ReviewOut
from ..security import current_user, require_roles

router = APIRouter(prefix="/requests", tags=["requests"])
STATUSES = {"submitted", "reviewed", "manual_review", "approved", "rejected"}


def _out(r: ChangeRequest) -> dict:
    return {"id": r.id, "requester_id": r.requester_id, "requester_name": r.requester.name, "type": r.type,
            "target": r.target, "justification": r.justification, "risk_level": r.risk_level,
            "status": r.status, "created_at": r.created_at,
            "ai_risk": r.reviews[-1].risk_assessment if r.reviews else None}


def _detail(r: ChangeRequest) -> dict:
    d = _out(r)
    d["reviews"] = [ReviewOut.model_validate(x) for x in reversed(r.reviews)]  # newest first
    d["decisions"] = [{"id": x.id, "approver_id": x.approver_id, "approver_name": x.approver.name,
                       "decision": x.decision, "comment": x.comment, "created_at": x.created_at}
                      for x in r.decisions]
    return d


def _load(db: Session, user: User, request_id: int, lock: bool = False) -> ChangeRequest:
    stmt = select(ChangeRequest).where(ChangeRequest.id == request_id)
    if lock:
        stmt = stmt.with_for_update()  # no-op on SQLite; serializes concurrent decisions on Postgres
    req = db.scalar(stmt)
    # Engineers only ever see their own requests; others get 404 so ids can't be probed.
    if req is None or (user.role == "engineer" and req.requester_id != user.id):
        raise HTTPException(404, "Request not found")
    return req


@router.post("", response_model=RequestOut, status_code=201)
def create_request(body: RequestIn, db: Session = Depends(get_db), user: User = Depends(require_roles("engineer"))):
    req = ChangeRequest(requester_id=user.id, type=body.type, target=body.target,
                        justification=body.justification, risk_level=body.risk_level, status="submitted")
    db.add(req)
    db.flush()
    audit.record(db, user.id, "request_submitted", "request", req.id, {"type": req.type, "risk_level": req.risk_level})
    db.commit()
    return _out(req)


@router.get("", response_model=list[RequestOut])
def list_requests(status: str | None = Query(None), limit: int = Query(50, ge=1, le=200),
                  offset: int = Query(0, ge=0), db: Session = Depends(get_db), user: User = Depends(current_user)):
    if status is not None and status not in STATUSES:
        raise HTTPException(422, "Unknown status")
    stmt = (select(ChangeRequest).options(selectinload(ChangeRequest.reviews), selectinload(ChangeRequest.requester))
            .order_by(ChangeRequest.id.desc()).limit(limit).offset(offset))
    if user.role == "engineer":
        stmt = stmt.where(ChangeRequest.requester_id == user.id)
    if status:
        stmt = stmt.where(ChangeRequest.status == status)
    return [_out(r) for r in db.scalars(stmt).all()]


@router.get("/{request_id}", response_model=RequestDetail)
def get_request(request_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return _detail(_load(db, user, request_id))


@router.post("/{request_id}/review", response_model=RequestDetail, dependencies=[Depends(review_limit)])
def review(request_id: int, db: Session = Depends(get_db),
           user: User = Depends(require_roles("engineer", "approver"))):
    req = _load(db, user, request_id, lock=True)
    if req.status in ("approved", "rejected"):
        raise HTTPException(409, "This request has already been decided")
    agent.review_request(db, req, agent.get_client(), actor_id=user.id)
    db.commit()
    db.refresh(req)
    return _detail(req)


@router.post("/{request_id}/decision", response_model=RequestDetail)
def decide(request_id: int, body: DecisionIn, db: Session = Depends(get_db),
           user: User = Depends(require_roles("approver"))):
    req = _load(db, user, request_id, lock=True)
    if req.status in ("approved", "rejected"):
        raise HTTPException(409, "This request has already been decided")
    if req.status == "submitted":
        raise HTTPException(409, "Run the AI review before deciding")
    if req.requester_id == user.id:
        raise HTTPException(403, "You cannot decide your own request")
    db.add(Decision(request_id=req.id, approver_id=user.id, decision=body.decision, comment=body.comment))
    req.status = body.decision
    audit.record(db, user.id, f"request_{body.decision}", "request", req.id, {"comment": body.comment[:200]})
    db.commit()
    db.refresh(req)
    return _detail(req)
