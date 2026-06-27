import asyncio
import logging
from typing import Optional
from app.parsers.base import Vacancy
from app.parsers import hh, remoteok, habr, workzilla

logger = logging.getLogger(__name__)


async def search_all(
    query: str,
    city: Optional[str] = None,
    salary_from: Optional[int] = None,
    employment_type: Optional[str] = None,
) -> list[Vacancy]:
    sources = {
        "hh":        hh.fetch(query, city, salary_from, employment_type),
        "remoteok":  remoteok.fetch(query, city, salary_from, employment_type),
        "habr":      habr.fetch(query, city, salary_from, employment_type),
        "workzilla": workzilla.fetch(query, city, salary_from, employment_type),
    }

    # Каждый источник ограничен своим таймаутом — падает только он, не все
    async def safe_fetch(name, coro):
        try:
            return name, await asyncio.wait_for(coro, timeout=9.0)
        except asyncio.TimeoutError:
            logger.warning("Парсер [%s]: таймаут", name)
            return name, []
        except Exception as e:
            logger.error("Парсер [%s] ошибка: %s", name, e)
            return name, []

    tasks = [safe_fetch(name, coro) for name, coro in sources.items()]
    results = await asyncio.gather(*tasks)

    vacancies: list[Vacancy] = []
    for name, result in results:
        if isinstance(result, list):
            logger.info("Парсер [%s]: %d вакансий", name, len(result))
            vacancies.extend(result)

    deduped = _deduplicate(vacancies)
    logger.info("Итого: %d → после дедупликации: %d", len(vacancies), len(deduped))
    return deduped


def _deduplicate(vacancies: list[Vacancy]) -> list[Vacancy]:
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    result: list[Vacancy] = []
    for v in vacancies:
        url_key = v.source_url.strip().rstrip("/").lower()
        if url_key in seen_urls:
            continue
        seen_urls.add(url_key)
        title_key = f"{v.title.lower().strip()}|{(v.company or '').lower().strip()}"
        if title_key in seen_titles:
            continue
        seen_titles.add(title_key)
        result.append(v)
    return result