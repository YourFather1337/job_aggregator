from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import SECRET_KEY
from app.routers import auth, search, favorites, resume

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

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ── Роутеры ─────────────────────────────────────────────────────────────────
app.include_router(search.router)
app.include_router(auth.router)
app.include_router(favorites.router)
app.include_router(resume.router)
