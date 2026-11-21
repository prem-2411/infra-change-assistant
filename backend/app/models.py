from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, event
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))  # engineer | approver | admin
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class ChangeRequest(Base):
    __tablename__ = "requests"
    id: Mapped[int] = mapped_column(primary_key=True)
    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    type: Mapped[str] = mapped_column(String(30), index=True)
    target: Mapped[str] = mapped_column(String(200))
    justification: Mapped[str] = mapped_column(Text)
    risk_level: Mapped[str] = mapped_column(String(10))  # claimed by the requester
    # submitted | reviewed | manual_review | approved | rejected
    status: Mapped[str] = mapped_column(String(20), default="submitted", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    requester: Mapped[User] = relationship()
    reviews: Mapped[list["AIReview"]] = relationship(order_by="AIReview.id", back_populates="request")
    decisions: Mapped[list["Decision"]] = relationship(order_by="Decision.id", back_populates="request")


class Policy(Base):
    __tablename__ = "policies"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    rule_text: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50))


class AIReview(Base):
    __tablename__ = "ai_reviews"
    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id"), index=True)
    summary: Mapped[str] = mapped_column(Text)
    risks: Mapped[list] = mapped_column(JSON, default=list)
    proposed_plan: Mapped[list] = mapped_column(JSON, default=list)
    risk_assessment: Mapped[str] = mapped_column(String(10))
    recommendation: Mapped[str] = mapped_column(String(10))  # approve | escalate | reject
    model_name: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(10))  # ok | failed
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    request: Mapped[ChangeRequest] = relationship(back_populates="reviews")


class Decision(Base):
    __tablename__ = "decisions"
    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id"), index=True)
    approver_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    decision: Mapped[str] = mapped_column(String(10))  # approved | rejected
    comment: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    request: Mapped[ChangeRequest] = relationship(back_populates="decisions")
    approver: Mapped[User] = relationship()


class AuditLog(Base):
    """Append-only. Only inserts are allowed through the ORM."""

    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(50), index=True)
    entity: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


@event.listens_for(AuditLog, "before_update")
@event.listens_for(AuditLog, "before_delete")
def _audit_is_append_only(mapper, connection, target):  # noqa: ARG001
    raise RuntimeError("audit_log is append-only")
