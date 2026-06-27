import logging
import httpx
from typing import Optional
from app.parsers.base import Vacancy

logger = logging.getLogger(__name__)
REMOTEOK_API = "https://remoteok.com/api"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}


async def fetch(
    query: str,
    city: Optional[str] = None,
    salary_from: Optional[int] = None,
    employment_type: Optional[str] = None,
) -> list[Vacancy]:
    if employment_type and employment_type not in ("remote", ""):
        return []

    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(REMOTEOK_API, headers=HEADERS)
            logger.info("RemoteOK status: %s", resp.status_code)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.error("RemoteOK ошибка: %s", e)
        return []

    # Разбиваем запрос на слова — ищем каждое отдельно (решает проблему "Go")
    q_words = [w.lower() for w in query.split() if len(w) > 1]

    results = []
    for item in data:
        if not isinstance(item, dict) or "slug" not in item:
            continue

        text = " ".join([
            item.get("position", ""),
            item.get("company", ""),
            item.get("description", ""),
            " ".join(item.get("tags", [])),
        ]).lower()

        # Хотя бы одно слово из запроса должно совпасть
        if not any(w in text for w in q_words):
            continue

        s_min = _to_float(item.get("salary_min"))
        s_max = _to_float(item.get("salary_max"))

        if salary_from and s_max and s_max < salary_from:
            continue

        results.append(Vacancy(
            title=item.get("position", ""),
            source_url=f"https://remoteok.com/remote-jobs/{item.get('slug', '')}",
            source="remoteok",
            company=item.get("company"),
            city="Remote",
            employment_type="remote",
            salary_from=s_min,
            salary_to=s_max,
            currency="USD",
        ))
        if len(results) >= 20:
            break

    logger.info("RemoteOK найдено: %d", len(results))
    return results


def _to_float(value) -> Optional[float]:
    try:
        return float(value) if value else None
    except (ValueError, TypeError):
        return None