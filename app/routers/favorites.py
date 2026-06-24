from fastapi import APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers.auth import require_user
from app.models import User

router = APIRouter(prefix="/favorites", tags=["Favorites"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
async def get_favorites(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    favorites_list = []
    return templates.TemplateResponse("favorites.html", {
        "request": request,
        "vacancies": favorites_list,
        "current_user": current_user,
    })


@router.post("/add")
async def add_favorites(
    request: Request,
    title: str = Form(...),
    source_url: str = Form(...),
    company: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    referer = request.headers.get("referer", "/")
    return RedirectResponse(url=referer, status_code=303)


@router.post("/{id}/delete")
async def delete_favorite(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    return RedirectResponse(url="/favorites", status_code=303)