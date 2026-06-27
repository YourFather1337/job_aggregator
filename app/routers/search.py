from fastapi import APIRouter, Request, Query, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.routers.auth import get_current_user

router = APIRouter(tags=["Search"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def get_index(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    return templates.TemplateResponse(
        "index.html", {"request": request, "current_user": current_user}
    )


@router.get("/search")
def search(
    request: Request,
    q: str = Query("", description="Search request"),
    city: str = Query("", description="City filter"),
    employment: str = Query("", description="Employment type filter"),
    salary_from: str = Query("", description="Salary from"),
    db: Session = Depends(get_db),
):
    current_user = get_current_user(request, db)

    # Заглушка: здесь будет вызов парсеров
    # all_vacancies.extend(hh_parser(q)) ...
    all_vacancies = []

    # ── Агрегация и Дедупликация ──
    unique_vacancies = {}
    for v in all_vacancies:
        url = v.get("source_url")
        if url and url not in unique_vacancies:
            unique_vacancies[url] = v
    aggregated = list(unique_vacancies.values())

    # ── Фильтрация ──
    filtered_results = []
    salary_from_int = None
    if salary_from and salary_from.isdigit():
        salary_from_int = int(salary_from)

    for v in aggregated:
        # Фильтр по городу
        if city and city.lower() not in (v.get("city") or "").lower():
            continue

        # Фильтр по занятости
        if employment and employment != v.get("employment_type"):
            continue

        # Фильтр по зарплате
        if salary_from_int is not None:
            v_salary_from = v.get("salary_from")
            if v_salary_from and v_salary_from < salary_from_int:
                continue

        filtered_results.append(v)

    return templates.TemplateResponse(
        "search.html",
        {
            "request": request,
            "query": q,
            "city": city,
            "employment": employment,
            "salary_from": salary_from,
            "vacancies": filtered_results,
            "current_user": current_user,
        },
    )
