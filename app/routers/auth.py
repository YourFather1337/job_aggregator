from fastapi import APIRouter, Depends, HTTPException, Request, status, Form
from sqlalchemy.orm import Session
import bcrypt

from app.database import get_db
from app.models import User
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(tags=["auth"])


# --- НАПРЯМУЮ ИСПОЛЬЗУЕМ BCRYPT БЕЗ PASSLIB ---


def _hash_password(plain: str) -> str:
    # 1. Кодируем в байты и жестко обрезаем до 72 байт (требование bcrypt)
    pwd_bytes = plain.encode("utf-8")[:72]
    # 2. Генерируем соль и хешируем
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(pwd_bytes, salt)
    # 3. Возвращаем как обычную строку для БД
    return hashed_bytes.decode("utf-8")


def _verify_password(plain: str, hashed: str) -> bool:
    try:
        # Подготавливаем введённый пароль так же, как при регистрации
        pwd_bytes = plain.encode("utf-8")[:72]
        hashed_bytes = hashed.encode("utf-8")
        # Сравниваем напрямую через bcrypt
        return bcrypt.checkpw(pwd_bytes, hashed_bytes)
    except Exception:
        return False


def _get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    """Возвращает текущего пользователя, если он авторизован."""
    user_id: int | None = request.session.get("user_id")
    if user_id is None:
        return None
    return db.get(User, user_id)


def require_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Требует авторизации. Если нет — редирект на /login (через 303 статус)."""
    user_id: int | None = request.session.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login"}
        )
    user = db.get(User, user_id)
    if user is None:
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login"}
        )
    return user


@router.get("/login")
def login_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    return templates.TemplateResponse(
        "login.html", {"request": request, "current_user": current_user}
    )


@router.get("/register")
def register_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    return templates.TemplateResponse(
        "register.html", {"request": request, "current_user": current_user}
    )


@router.post("/register")
def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    email: str = Form(...),
    db: Session = Depends(get_db),
):

    exists = db.query(User).filter(User.username == username).first()
    if exists:
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": "Пользователь уже зарегистрирован",
                "current_user": None,
            },
        )

    user = User(
        username=username, email=email, hashed_password=_hash_password(password)
    )
    db.add(user)
    db.commit()
    return RedirectResponse("/login", status_code=303)


@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = _get_user_by_username(db, username)

    # Простая и надежная проверка без скрытых костылей от passlib
    if user is None or not _verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Неверный логин или пароль",
                "current_user": None,
            },
        )

    request.session["user_id"] = user.id
    return RedirectResponse(url="/", status_code=303)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)
