from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from dataclasses import asdict

from app.parsers.aggregator import search_all

router = APIRouter(tags=["Search"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
async def get_index(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "current_user": getattr(request.state, "current_user", None),
    })


@router.get("/search")
async def search_page(
    request: Request,
    q: str = Query(...),
    salary: Optional[int] = Query(None),
    city: Optional[str] = Query(None),
    employment: Optional[str] = Query(None),
):
    """Возвращает страницу сразу — результаты подгружаются через /api/search."""
    return templates.TemplateResponse("search.html", {
        "request": request,
        "current_user": getattr(request.state, "current_user", None),
        "query": q,
        "vacancies": [],   # пустой список — AJAX заполнит
        "total": None,
        "filters": {
            "city": city or "",
            "salary": salary or "",
            "employment": employment or "",
        },
    })


@router.get("/api/search")
async def search_api(
    q: str = Query(...),
    salary: Optional[int] = Query(None),
    city: Optional[str] = Query(None),
    employment: Optional[str] = Query(None),
):
    """JSON-эндпоинт, который вызывает AJAX со страницы поиска."""
    vacancies = await search_all(
        query=q,
        city=city,
        salary_from=salary,
        employment_type=employment,
    )
    return JSONResponse(content={
        "total": len(vacancies),
        "vacancies": [asdict(v) for v in vacancies],
    })