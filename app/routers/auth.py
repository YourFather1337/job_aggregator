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
) -> User | None:
    """
    Возвращает объект User, если пользователь авторизован, иначе None.
    Не выбрасывает исключения, чтобы можно было использовать в шаблоне для проверки {% if user %}.
    """
    user_id: int | None = request.session.get("user_id")
    if user_id is None:
        return None
    
    user = db.get(User, user_id)
    return user

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


# ---------------------------------------------------------------------------
# Эндпоинты
# ---------------------------------------------------------------------------

@router.get("/login")
def login_page(request: Request, db: Session = Depends(get_db)):
    # Получаем текущего пользователя, если он есть
    current_user = get_current_user(request, db)
    return templates.TemplateResponse("login.html", {
        "request": request, 
        "current_user": current_user  # Передаем пользователя в шаблон
    })

@router.get("/register")
def register_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    return templates.TemplateResponse("register.html", {
        "request": request, 
        "current_user": current_user
    })


@router.post("/register")
def register(request: Request, username: str = Form(...), 
             password: str = Form(...), email: str = Form(...), db: Session = Depends(get_db)):
    exists = db.query(User).filter(User.username == username).first()
    if exists:
        return templates.TemplateResponse(request=request, name="register.html",
                context={"error": "Пользователь уже зареган"})
    user = User(username=username, email=email, hashed_password=_hash_password(password))
    db.add(user)
    db.commit()
    return RedirectResponse("/login", status_code=303)


@router.post("/login")
def login(username: str = Form(...), password: str = Form(...), request: Request = None, db: Session = Depends(get_db)):
    payload = UserLogin(username=username, password=password)
    user = _get_user_by_username(db, payload.username)
    
    dummy_hash = "$2b$12$notarealhashjustpadding0000000000000000000000000000000 "
    password_ok = _verify_password(
        payload.password,
        user.hashed_password if user else dummy_hash,
    )

    if user is None or not password_ok:
        # Исправлена опечатка в TemplateResponse и контексте
        return templates.TemplateResponse("login.html", {
            "request": request,  
            "error": "Неверный логин или пароль", # Ключ должен совпадать с тем, что проверяется в шаблоне
            "current_user": None
        })

    request.session["user_id"] = user.id
    return RedirectResponse(url="/", status_code=303)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Выход из системы",
)
def logout(request: Request) -> None:
    request.session.clear()
    response = RedirectResponse("/", status_code=303)
    return response