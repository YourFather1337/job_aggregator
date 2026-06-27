from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import SECRET_KEY
from app.database import get_db
from app.routers import auth, search, favorites, resume

templates = Jinja2Templates(directory="app/templates")

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
@app.get("/")
def home(request: Request, db: Session = Depends(get_db)):
    current_user = auth.get_current_user(request, db)
    return templates.TemplateResponse("index.html", {"request": request, "current_user": current_user})

app.include_router(search.router)
app.include_router(auth.router)
app.include_router(favorites.router)
app.include_router(resume.router)
