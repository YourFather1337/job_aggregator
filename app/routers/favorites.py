from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

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


@router.post("/{vacancy_id}/delete")
def delete_favorite(
    vacancy_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_current_user),
):
    vacancy = (
        db.query(SavedVacancy)
        .filter(SavedVacancy.id == vacancy_id, SavedVacancy.user_id == current_user.id)
        .first()
    )
    if vacancy:
        db.delete(vacancy)
        db.commit()
    return RedirectResponse(url="/favorites", status_code=303)