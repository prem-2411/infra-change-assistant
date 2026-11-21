from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

RequestType = Literal["add_server", "open_port", "grant_access", "change_config"]
RiskLevel = Literal["low", "medium", "high"]
Role = Literal["engineer", "approver", "admin"]


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class LoginIn(_In):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RegisterIn(_In):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=12, max_length=72)
    role: Role

    @field_validator("password")
    @classmethod
    def _bcrypt_limit(cls, v: str) -> str:
        if len(v.encode()) > 72:
            raise ValueError("password must be at most 72 bytes")
        return v


class RequestIn(_In):
    type: RequestType
    target: str = Field(min_length=1, max_length=200)
    justification: str = Field(min_length=10, max_length=2000)
    risk_level: RiskLevel


class DecisionIn(_In):
    decision: Literal["approved", "rejected"]
    comment: str = Field(min_length=1, max_length=1000)


class PolicyIn(_In):
    title: str = Field(min_length=1, max_length=200)
    rule_text: str = Field(min_length=1, max_length=2000)
    category: str = Field(min_length=1, max_length=50)


class _Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserOut(_Out):
    id: int
    name: str
    email: str
    role: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class PolicyOut(_Out):
    id: int
    title: str
    rule_text: str
    category: str


class ReviewOut(_Out):
    id: int
    request_id: int
    summary: str
    risks: list[str]
    proposed_plan: list[str]
    risk_assessment: str
    recommendation: str
    model_name: str
    status: str
    error: str | None
    created_at: datetime


class DecisionOut(BaseModel):
    id: int
    approver_id: int
    approver_name: str
    decision: str
    comment: str
    created_at: datetime


class RequestOut(BaseModel):
    id: int
    requester_id: int
    requester_name: str
    type: str
    target: str
    justification: str
    risk_level: str
    status: str
    ai_risk: str | None = None
    created_at: datetime


class RequestDetail(RequestOut):
    reviews: list[ReviewOut]
    decisions: list[DecisionOut]


class AuditOut(_Out):
    id: int
    actor_id: int | None
    action: str
    entity: str
    entity_id: int | None
    details: dict
    created_at: datetime
