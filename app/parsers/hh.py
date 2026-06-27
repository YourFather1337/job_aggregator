"""
HH.ru API — требует регистрации приложения для полноценного доступа.
Используем User-Agent формат который они принимают без токена.
"""
import logging
import httpx
from typing import Optional
from app.parsers.base import Vacancy

logger = logging.getLogger(__name__)
HH_API = "https://api.hh.ru/vacancies"

# Без зарегистрированного приложения HH даёт 403.
# Передаём корректный User-Agent согласно документации HH API.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "HH-User-Agent": "WorkFind/1.0 (student@example.com)",
}

EMPLOYMENT_MAP = {
    "full": "full", "part": "part",
    "remote": "remote", "contract": "contractor",
}


async def fetch(
    query: str,
    city: Optional[str] = None,
    salary_from: Optional[int] = None,
    employment_type: Optional[str] = None,
    per_page: int = 20,
) -> list[Vacancy]:
    params: dict = {
        "text": query,
        "per_page": per_page,
        "only_with_salary": "false",
        "search_field": "name",   # ищем только в названии
    }
    if salary_from:
        params["salary"] = salary_from
        params["only_with_salary"] = "true"
    if employment_type and employment_type in EMPLOYMENT_MAP:
        params["employment"] = EMPLOYMENT_MAP[employment_type]

    try:
        async with httpx.AsyncClient(timeout=8, follow_redirects=True) as client:
            resp = await client.get(HH_API, params=params, headers=HEADERS)
            logger.info("HH status: %s", resp.status_code)
            if resp.status_code == 403:
                logger.warning("HH вернул 403 — нужна регистрация приложения на dev.hh.ru")
                return []
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.error("HH ошибка: %s", e)
        return []

    results = []
    for item in data.get("items", []):
        salary = item.get("salary") or {}
        area   = item.get("area") or {}
        employer = item.get("employer") or {}

        # Фильтр по городу на стороне клиента
        if city and area.get("name", "").lower() not in city.lower():
            if city.lower() not in area.get("name", "").lower():
                continue

        results.append(Vacancy(
            title=item.get("name", ""),
            source_url=item.get("alternate_url", ""),
            source="hh",
            company=employer.get("name"),
            city=area.get("name"),
            employment_type=(item.get("employment") or {}).get("id"),
            salary_from=salary.get("from"),
            salary_to=salary.get("to"),
            currency=salary.get("currency", "RUB"),
        ))
    return results