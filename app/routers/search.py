from fastapi import APIRouter, Request, Query, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers.auth import get_current_user

router = APIRouter(tags=["Search"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
async def get_index(request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return templates.TemplateResponse("index.html", {"request": request, "current_user": current_user})


@router.get("/search")
async def search(
    request: Request,
    q: str = Query(...),
    salary: int = Query(None),
    city: str = Query(None),
    employment_type: str = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    results = []
    return templates.TemplateResponse("search.html", {
        "request": request,
        "query": q,
        "vacancies": results,
        "current_user": current_user,
        "city": city,
        "salary_from": salary,
        "employment": employment_type,
    })