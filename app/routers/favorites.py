from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import SavedVacancy
from app.routers.auth import require_current_user

router = APIRouter(prefix="/favorites", tags=["Favorites"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def favorites_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_current_user),
):
    vacancies = (
        db.query(SavedVacancy)
        .filter(SavedVacancy.user_id == current_user.id)
        .order_by(SavedVacancy.saved_at.desc())
        .all()
    )
    return templates.TemplateResponse("favorites.html", {
        "request": request,
        "current_user": current_user,
        "vacancies": vacancies,
    })


@router.post("/add")
def add_favorite(
    request: Request,
    title: str = Form(...),
    source_url: str = Form(...),
    company: Optional[str] = Form(None),
    salary_from: Optional[float] = Form(None),
    salary_to: Optional[float] = Form(None),
    currency: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    employment_type: Optional[str] = Form(None),
    source: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user=Depends(require_current_user),
):
    # Проверяем дубль — не добавляем одну вакансию дважды
    exists = (
        db.query(SavedVacancy)
        .filter(
            SavedVacancy.user_id == current_user.id,
            SavedVacancy.source_url == source_url,
        )
        .first()
    )
    if not exists:
        vacancy = SavedVacancy(
            user_id=current_user.id,
            title=title,
            source_url=source_url,
            company=company or None,
            salary_from=salary_from or None,
            salary_to=salary_to or None,
            currency=currency or None,
            city=city or None,
            employment_type=employment_type or None,
            source=source or None,
        )
        db.add(vacancy)
        db.commit()

    # Возвращаемся обратно на страницу поиска
    referer = request.headers.get("referer", "/")
    return RedirectResponse(url=referer, status_code=303)


@router.post("/{vacancy_id}/delete")
def delete_favorite(
    vacancy_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_current_user),
):
    vacancy = (
        db.query(SavedVacancy)
        .filter(
            SavedVacancy.id == vacancy_id,
            SavedVacancy.user_id == current_user.id,
        )
        .first()
    )
    if vacancy:
        db.delete(vacancy)
        db.commit()
    return RedirectResponse(url="/favorites", status_code=303)