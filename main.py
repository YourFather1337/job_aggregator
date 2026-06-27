import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s [%(name)s]: %(message)s",
)

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.config import SECRET_KEY
from app.database import SessionLocal
from app.models import User
from app.routers import auth, search, favorites, resume


class CurrentUserMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        user_id: int | None = request.session.get("user_id")
        user: User | None = None
        if user_id is not None:
            db = SessionLocal()
            try:
                user = db.get(User, user_id)
                if user is None:
                    request.session.clear()
            finally:
                db.close()
        request.state.current_user = user
        response = await call_next(request)
        return response


app = FastAPI(title="WorkFind", description="Агрегатор вакансий", version="0.1.0")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.add_middleware(CurrentUserMiddleware)
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="jobs_session",
    max_age=60 * 60 * 24 * 7,
    https_only=False,
    same_site="lax",
)

app.include_router(auth.router)
app.include_router(search.router)
app.include_router(favorites.router)
app.include_router(resume.router)