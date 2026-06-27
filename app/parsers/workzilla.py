import re
import logging
import httpx
from bs4 import BeautifulSoup
from typing import Optional
from app.parsers.base import Vacancy

logger = logging.getLogger(__name__)
# Workzilla перенаправляет workzilla.com → work-zilla.com
BASE = "https://work-zilla.com"
SEARCH_URL = f"{BASE}/jobs"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


async def fetch(
    query: str,
    city: Optional[str] = None,
    salary_from: Optional[int] = None,
    employment_type: Optional[str] = None,
) -> list[Vacancy]:
    params: dict = {"search": query}

    try:
        async with httpx.AsyncClient(
            timeout=8,
            follow_redirects=True,
            headers=HEADERS,
        ) as client:
            resp = await client.get(SEARCH_URL, params=params)
            logger.info("Workzilla status: %s, url: %s", resp.status_code, resp.url)
            resp.raise_for_status()
            html = resp.text
    except Exception as e:
        logger.error("Workzilla ошибка: %s", e)
        return []

    soup = BeautifulSoup(html, "html.parser")

    # Пробуем несколько вариантов селекторов
    cards = (
        soup.select("div.task-item") or
        soup.select("article.task") or
        soup.select(".jobs-list__item") or
        soup.select("[class*='task-item']") or
        soup.select("[class*='job-item']")
    )
    logger.info("Workzilla карточек: %d", len(cards))

    if not cards:
        # Fallback: ищем ссылки на задания
        links = soup.select("a[href*='/jobs/']") or soup.select("a[href*='/tasks/']")
        logger.info("Workzilla fallback links: %d", len(links))
        return _parse_links(links)

    results = []
    for card in cards[:20]:
        title_el = (
            card.select_one("a.task-item__title") or
            card.select_one("a.task__title") or
            card.select_one("a[class*='title']") or
            card.select_one("h2 a") or
            card.select_one("h3 a")
        )
        if not title_el:
            continue

        title = title_el.get_text(strip=True)
        href  = title_el.get("href", "")
        url   = href if href.startswith("http") else BASE + href

        price_el = (
            card.select_one("span.task-item__price") or
            card.select_one("span.task__price") or
            card.select_one("[class*='price']") or
            card.select_one("[class*='salary']")
        )
        sal_from, sal_to = _parse_price(price_el.get_text(strip=True) if price_el else "")

        if salary_from and sal_to and sal_to < salary_from:
            continue

        results.append(Vacancy(
            title=title,
            source_url=url,
            source="workzilla",
            company=None,
            city=city,
            employment_type=employment_type or "contract",
            salary_from=sal_from,
            salary_to=sal_to,
            currency="RUB",
        ))

    logger.info("Workzilla результатов: %d", len(results))
    return results


def _parse_links(links) -> list[Vacancy]:
    seen = set()
    results = []
    for a in links:
        href = a.get("href", "")
        if not href or href in seen:
            continue
        seen.add(href)
        title = a.get_text(strip=True)
        if not title or len(title) < 3:
            continue
        url = href if href.startswith("http") else BASE + href
        results.append(Vacancy(
            title=title, source_url=url, source="workzilla",
            employment_type="contract",
        ))
        if len(results) >= 15:
            break
    return results


def _parse_price(text: str) -> tuple[Optional[float], Optional[float]]:
    nums = re.findall(r"\d[\d\s\xa0]*\d|\d+", text)
    nums = [float(n.replace(" ", "").replace("\xa0", "")) for n in nums if n.strip()]
    if not nums:
        return None, None
    if len(nums) == 1:
        return nums[0], None
    return nums[0], nums[1]