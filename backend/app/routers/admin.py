from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, text
from sqlalchemy.orm import Session, selectinload

from .. import audit
from ..db import get_db
from ..models import AuditLog, ChangeRequest, Decision, Policy, User
from ..observability import metrics
from ..schemas import AuditOut, PolicyIn, PolicyOut, UserOut
from ..security import current_user, require_roles

router = APIRouter(tags=["admin"])


@router.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(503, "Database unavailable") from None
    return {"status": "ok"}


@router.get("/policies", response_model=list[PolicyOut])
def list_policies(db: Session = Depends(get_db), _: User = Depends(current_user)):
    return db.scalars(select(Policy).order_by(Policy.id)).all()


@router.post("/policies", response_model=PolicyOut, status_code=201)
def create_policy(body: PolicyIn, db: Session = Depends(get_db), admin: User = Depends(require_roles("admin"))):
    policy = Policy(**body.model_dump())
    db.add(policy)
    db.flush()
    audit.record(db, admin.id, "policy_created", "policy", policy.id, {"title": policy.title})
    db.commit()
    return policy


@router.put("/policies/{policy_id}", response_model=PolicyOut)
def update_policy(policy_id: int, body: PolicyIn, db: Session = Depends(get_db),
                  admin: User = Depends(require_roles("admin"))):
    policy = db.get(Policy, policy_id)
    if policy is None:
        raise HTTPException(404, "Policy not found")
    for k, v in body.model_dump().items():
        setattr(policy, k, v)
    audit.record(db, admin.id, "policy_updated", "policy", policy.id, {"title": policy.title})
    db.commit()
    return policy


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    return db.scalars(select(User).order_by(User.id)).all()


@router.get("/audit", response_model=list[AuditOut])
def audit_log(limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0),
              db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    return db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(limit).offset(offset)).all()


@router.get("/metrics")
def get_metrics(_: User = Depends(require_roles("admin"))):
    return metrics.snapshot()


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), _: User = Depends(require_roles("approver", "admin"))):
    reqs = db.scalars(select(ChangeRequest).options(selectinload(ChangeRequest.reviews))).all()
    by_status: dict[str, int] = {}
    by_risk: dict[str, int] = {"low": 0, "medium": 0, "high": 0}
    by_ai_risk: dict[str, int] = {"low": 0, "medium": 0, "high": 0}
    for r in reqs:
        by_status[r.status] = by_status.get(r.status, 0) + 1
        by_risk[r.risk_level] = by_risk.get(r.risk_level, 0) + 1
        if r.reviews:
            by_ai_risk[r.reviews[-1].risk_assessment] += 1
    created = {r.id: r.created_at for r in reqs}
    durations = [(d.created_at - created[d.request_id]).total_seconds()
                 for d in db.scalars(select(Decision)).all() if d.request_id in created]
    return {"total": len(reqs), "by_status": by_status, "by_claimed_risk": by_risk, "by_ai_risk": by_ai_risk,
            "avg_review_seconds": round(sum(durations) / len(durations), 1) if durations else None}
