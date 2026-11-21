"""Small in-process sliding-window limiter (fine for one worker; use Redis to scale out)."""
import threading
import time
from collections import defaultdict, deque

from fastapi import Depends, HTTPException, Request

from .config import settings
from .models import User
from .security import current_user

_lock = threading.Lock()
_hits: dict[str, deque] = defaultdict(deque)


def reset_limits() -> None:
    with _lock:
        _hits.clear()


def client_ip(request: Request) -> str:
    if settings.trust_proxy:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check(key: str, limit: int, window: int) -> None:
    now = time.monotonic()
    with _lock:
        q = _hits[key]
        while q and now - q[0] > window:
            q.popleft()
        if len(q) >= limit:
            raise HTTPException(429, "Too many requests. Wait a minute and try again.",
                                headers={"Retry-After": str(window)})
        q.append(now)


def login_limit(request: Request) -> None:
    _check(f"login:{client_ip(request)}", settings.login_rate_limit, settings.login_rate_window)


def review_limit(user: User = Depends(current_user)) -> None:
    _check(f"review:{user.id}", settings.review_rate_limit, settings.review_rate_window)
