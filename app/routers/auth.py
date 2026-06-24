from fastapi import APIRouter, Depends, HTTPException, Request, status, Form
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserLogin, UserResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

templates = Jinja2Templates(directory="app/templates")

router = APIRouter(tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------------------------------------------------------------------
# Утилиты
# ---------------------------------------------------------------------------

def _hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def _verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


# ---------------------------------------------------------------------------
# Зависимость: текущий пользователь
# ---------------------------------------------------------------------------

def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """
    Читает user_id из сессии и возвращает объект User.
    Бросает 401, если пользователь не аутентифицирован или не найден.
    """
    user_id: int | None = request.session.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Необходима аутентификация",
        )

    user = db.get(User, user_id)
    if user is None:
        # Сессия протухла — пользователь удалён из БД
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден. Войдите заново",
        )

    return RedirectResponse(url="/login", status_code=303)


# ---------------------------------------------------------------------------
# Эндпоинты
# ---------------------------------------------------------------------------

@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "current_user": None})

@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "current_user": None})


@router.post("/register")
def register(username: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    payload = UserCreate(username=username,email=email,password=password)
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
        # Определяем, какое именно поле нарушает уникальность
        err_str = str(exc.orig).lower()
        if "username" in err_str:
            detail = f"Имя пользователя «{payload.username}» уже занято"
        elif "email" in err_str:
            detail = f"Email «{payload.email}» уже зарегистрирован"
        else:
            detail = "Пользователь с такими данными уже существует"
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail) from exc

    return RedirectResponse(url="/", status_code=303)


@router.post("/login")
def login(username: str = Form(...), password: str = Form(...), request: Request = None, db: Session = Depends(get_db)):
    payload = UserLogin(username=username,password=password)
    user = _get_user_by_username(db, payload.username)

    # Намеренно проверяем пароль даже если user is None (timing-safe)
    dummy_hash = "$2b$12$notarealhashjustpadding000000000000000000000000000000"
    password_ok = _verify_password(
        payload.password,
        user.hashed_password if user else dummy_hash,
    )

    if user is None or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
        )

    request.session["user_id"] = user.id
    return user


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Выход из системы",
)
def logout(request: Request) -> None:
    request.session.clear()