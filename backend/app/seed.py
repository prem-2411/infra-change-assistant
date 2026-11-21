from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .config import settings
from .models import Policy, User
from .policies_seed import SEED_POLICIES
from .security import hash_password


def _ensure_user(db: Session, email: str, password: str, name: str, role: str) -> None:
    if not db.scalar(select(User).where(User.email == email)):
        db.add(User(name=name, email=email, password_hash=hash_password(password), role=role))


def seed(db: Session) -> None:
    if not db.scalar(select(func.count()).select_from(Policy)):
        db.add_all(Policy(**p) for p in SEED_POLICIES)
    if settings.admin_email and settings.admin_password:
        _ensure_user(db, settings.admin_email, settings.admin_password, "Admin", "admin")
    if settings.seed_demo_users and settings.demo_password:
        _ensure_user(db, "engineer@example.com", settings.demo_password, "Demo Engineer", "engineer")
        _ensure_user(db, "approver@example.com", settings.demo_password, "Demo Approver", "approver")
    db.commit()
