import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .config import settings
from .db import Base, SessionLocal, engine
from .observability import install_middleware, setup_logging
from .routers import admin, auth, requests
from .seed import seed

log = logging.getLogger("startup")


def init_db(retries: int = 15) -> None:
    for attempt in range(1, retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            break
        except Exception:
            log.warning("database not ready (attempt %s/%s)", attempt, retries)
            time.sleep(2)
    # create_all keeps the demo simple; use Alembic migrations for a real deployment.
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed(db)


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logging()
    if settings.secret_key == "dev-only-change-me":
        log.warning("SECRET_KEY is the development default; set a real secret")
    init_db()
    yield


app = FastAPI(title="Infra Change Assistant", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["*"],
                   allow_headers=["Authorization", "Content-Type"])
install_middleware(app)
app.include_router(auth.router)
app.include_router(requests.router)
app.include_router(admin.router)
