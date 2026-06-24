from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
from pydantic import ValidationError

from app.database import get_db
from app.models import User
from app.schemas import UserCreate

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="app/templates")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------------------------------------------------------------------
# Утилиты
# ---------------------------------------------------------------------------

def _hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def _verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def _render_register(request: Request, error: str = None, username: str = "", email: str = ""):
    """Возвращает страницу регистрации с сохранёнными полями и текстом ошибки."""
    return templates.TemplateResponse("register.html", {
        "request": request,
        "current_user": getattr(request.state, "current_user", None),
        "error": error,
        "form_username": username,
        "form_email": email,
    })


def _render_login(request: Request, error: str = None):
    return templates.TemplateResponse("login.html", {
        "request": request,
        "current_user": getattr(request.state, "current_user", None),
        "error": error,
    })


# ---------------------------------------------------------------------------
# Зависимости
# ---------------------------------------------------------------------------

def get_current_user(request: Request) -> Optional[User]:
    return getattr(request.state, "current_user", None)


def require_current_user(request: Request) -> User:
    user = get_current_user(request)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Необходима аутентификация",
        )
    return user


# ---------------------------------------------------------------------------
# Страницы (GET)
# ---------------------------------------------------------------------------

@router.get("/login")
def login_page(request: Request):
    return _render_login(request)


@router.get("/register")
def register_page(request: Request):
    return _render_register(request)


# ---------------------------------------------------------------------------
# Эндпоинты (POST)
# ---------------------------------------------------------------------------

@router.post("/register")
def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    # Валидация через Pydantic — ловим ошибки и возвращаем HTML, не JSON
    try:
        payload = UserCreate(username=username, email=email, password=password)
    except ValidationError as exc:
        # Берём первое сообщение об ошибке и показываем на странице
        first_error = exc.errors()[0]["msg"].replace("Value error, ", "")
        return _render_register(request, error=first_error, username=username, email=email)

    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=_hash_password(payload.password),
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError as exc:
        db.rollback()
        err_str = str(exc.orig).lower()
        if "username" in err_str:
            detail = f"Имя пользователя «{username}» уже занято"
        elif "email" in err_str:
            detail = f"Email «{email}» уже зарегистрирован"
        else:
            detail = "Пользователь с такими данными уже существует"
        return _render_register(request, error=detail, username=username, email=email)

    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = _get_user_by_username(db, username)

    dummy_hash = "$2b$12$notarealhashjustpadding000000000000000000000000000000"
    password_ok = _verify_password(
        password,
        user.hashed_password if user else dummy_hash,
    )

    if user is None or not password_ok:
        return _render_login(request, error="Неверный логин или пароль")

    request.session["user_id"] = user.id
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/logout", status_code=status.HTTP_303_SEE_OTHER)
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)