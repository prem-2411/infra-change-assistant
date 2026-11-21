from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import audit
from ..db import get_db
from ..models import User
from ..ratelimit import login_limit
from ..schemas import LoginIn, RegisterIn, TokenOut, UserOut
from ..security import (_DUMMY_HASH, create_token, current_user, hash_password, require_roles,
                        verify_password)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut, dependencies=[Depends(login_limit)])
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    ok = verify_password(body.password, user.password_hash if user else _DUMMY_HASH)
    if not user or not ok:
        audit.record(db, None, "login_failed", "user", None, {"email": body.email.lower()})
        db.commit()
        raise HTTPException(401, "Incorrect email or password")
    audit.record(db, user.id, "login", "user", user.id)
    db.commit()
    return TokenOut(access_token=create_token(user), user=UserOut.model_validate(user))


@router.post("/register", response_model=UserOut, status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db), admin: User = Depends(require_roles("admin"))):
    email = body.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "A user with this email already exists")
    user = User(name=body.name, email=email, password_hash=hash_password(body.password), role=body.role)
    db.add(user)
    db.flush()
    audit.record(db, admin.id, "user_created", "user", user.id, {"role": user.role})
    db.commit()
    return user


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user
