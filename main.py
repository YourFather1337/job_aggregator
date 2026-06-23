from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from config import SECRET_KEY
from routers import auth

app = FastAPI(
    title="Jobs API",
    description="Сервис для работы с вакансиями и резюме",
    version="0.1.0",
)

# ── Middleware ──────────────────────────────────────────────────────────────
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="jobs_session",
    max_age=60 * 60 * 24 * 7,   # 7 дней
    https_only=False,            # True в продакшене за HTTPS
    same_site="lax",
)

# ── Роутеры ─────────────────────────────────────────────────────────────────
app.include_router(auth.router)


@app.get("/", tags=["health"])
def root() -> dict:
    return {"status": "ok", "message": "Jobs API is running"}