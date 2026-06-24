from fastapi import APIRouter, Depends, HTTPException, Request, status, Form
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserLogin
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

templates = Jinja2Templates(directory="app/templates")

router = APIRouter(tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def _verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User | None:
    user_id: int | None = request.session.get("user_id")
    if user_id is None:
        return None
    return db.get(User, user_id)


def require_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    user_id: int | None = request.session.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"},
        )
    user = db.get(User, user_id)
    if user is None:
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"},
        )
    return user


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "current_user": None})


@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "current_user": None})


@router.post("/register")
def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        payload = UserCreate(username=username, email=email, password=password)
    except Exception:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "current_user": None,
            "error": "Пароль должен содержать минимум 8 символов",
        })

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
            detail = f"Имя пользователя «{payload.username}» уже занято"
        elif "email" in err_str:
            detail = f"Email «{payload.email}» уже зарегистрирован"
        else:
            detail = "Пользователь с такими данными уже существует"
        return templates.TemplateResponse("register.html", {
            "request": request,
            "current_user": None,
            "error": detail,
        })

    return RedirectResponse(url="/login", status_code=303)


@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    payload = UserLogin(username=username, password=password)
    user = _get_user_by_username(db, payload.username)

    dummy_hash = "$2b$12$notarealhashjustpadding000000000000000000000000000000"
    password_ok = _verify_password(
        payload.password,
        user.hashed_password if user else dummy_hash,
    )

    if user is None or not password_ok:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "current_user": None,
            "error": "Неверный логин или пароль",
        })

    request.session["user_id"] = user.id
    return RedirectResponse(url="/", status_code=303)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)