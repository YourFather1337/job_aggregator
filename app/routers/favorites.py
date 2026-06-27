from fastapi import APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, SavedVacancy
from app.routers.auth import require_user

router = APIRouter(prefix="/favorites", tags=["Favorites"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def get_favorites(
    request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)
):
    vacancies = db.query(SavedVacancy).filter(SavedVacancy.user_id == user.id).all()
    return templates.TemplateResponse(
        "favorites.html",
        {"request": request, "vacancies": vacancies, "current_user": user},
    )


@router.post("/add")
def add_favorite(
    request: Request,
    title: str | None = Form(None),
    company: str | None = Form(None),
    salary_from: str | None = Form(None),
    salary_to: str | None = Form(None),
    currency: str | None = Form(None),
    city: str | None = Form(None),
    employment_type: str | None = Form(None),
    source: str | None = Form(None),
    source_url: str | None = Form(None),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    if not source_url:
        return RedirectResponse(
            url=request.headers.get("referer", "/"), status_code=303
        )

    exists = (
        db.query(SavedVacancy)
        .filter(SavedVacancy.user_id == user.id, SavedVacancy.source_url == source_url)
        .first()
    )

    if not exists:

        def parse_int(val):
            if val:
                try:
                    return int(float(val))
                except ValueError:
                    return None
            return None

        vacancy = SavedVacancy(
            user_id=user.id,
            title=title,
            company=company,
            salary_from=parse_int(salary_from),
            salary_to=parse_int(salary_to),
            currency=currency,
            city=city,
            employment_type=employment_type,
            source=source,
            source_url=source_url,
        )
        db.add(vacancy)
        db.commit()

    referer = request.headers.get("referer", "/")
    return RedirectResponse(url=referer, status_code=303)


@router.post("/{id}/delete")
def delete_favorite(
    id: int,
    request: Request,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    vacancy = (
        db.query(SavedVacancy)
        .filter(SavedVacancy.id == id, SavedVacancy.user_id == user.id)
        .first()
    )
    if vacancy:
        db.delete(vacancy)
        db.commit()
    return RedirectResponse(url="/favorites", status_code=303)
