import re
import logging
import httpx
from bs4 import BeautifulSoup
from typing import Optional
from app.parsers.base import Vacancy

logger = logging.getLogger(__name__)
BASE = "https://career.habr.com"
SEARCH_URL = f"{BASE}/vacancies"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "ru-RU,ru;q=0.9",
}

EMPLOYMENT_MAP = {
    "full":     "full_time",
    "part":     "part_time",
    "remote":   "remote",
    "contract": "contract",
}


async def fetch(
    query: str,
    city: Optional[str] = None,
    salary_from: Optional[int] = None,
    employment_type: Optional[str] = None,
    max_pages: int = 3,          # берём до 3 страниц = до 60 вакансий
) -> list[Vacancy]:

    params: dict = {"q": query, "type": "all"}
    if salary_from:
        params["salary"] = salary_from
    if employment_type and employment_type in EMPLOYMENT_MAP:
        params["employment_type"] = EMPLOYMENT_MAP[employment_type]
    if city:
        params["city"] = city

    all_vacancies: list[Vacancy] = []

    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            for page in range(1, max_pages + 1):
                params["page"] = page
                resp = await client.get(SEARCH_URL, params=params, headers=HEADERS)
                logger.info("Habr page %d status: %s", page, resp.status_code)
                resp.raise_for_status()

                page_vacancies = _parse_html(resp.text, query, city, salary_from, employment_type)
                logger.info("Habr page %d: %d вакансий", page, len(page_vacancies))

                all_vacancies.extend(page_vacancies)

                # Если страница вернула меньше 20 — дальше страниц нет
                if len(page_vacancies) < 20:
                    break

    except Exception as e:
        logger.error("Habr ошибка: %s", e)

    logger.info("Habr итого: %d вакансий", len(all_vacancies))
    return all_vacancies


def _parse_html(
    html: str,
    query: str,
    city: Optional[str],
    salary_from: Optional[int],
    employment_type: Optional[str],
) -> list[Vacancy]:
    soup = BeautifulSoup(html, "html.parser")

    cards = (
        soup.select("div.vacancy-card") or
        soup.select("article.vacancy-card") or
        soup.select(".vacancy-card")
    )

    if not cards:
        links = soup.select("a[href*='/vacancies/']")
        return _parse_links(links)

    results = []
    for card in cards:
        title_el = (
            card.select_one("a.vacancy-card__title") or
            card.select_one(".vacancy-card__title a") or
            card.select_one("h2 a") or
            card.select_one("a[href*='/vacancies/']")
        )
        if not title_el:
            continue

        title = title_el.get_text(strip=True)
        href  = title_el.get("href", "")
        url   = href if href.startswith("http") else BASE + href

        company_el = (
            card.select_one("a.vacancy-card__company-title") or
            card.select_one(".company_name a") or
            card.select_one("[class*='company'] a")
        )
        company = company_el.get_text(strip=True) if company_el else None

        location_el = (
            card.select_one("span.vacancy-card__meta") or
            card.select_one("[class*='location']") or
            card.select_one("[class*='city']")
        )
        city_text = location_el.get_text(strip=True) if location_el else None

        salary_el = (
            card.select_one("div.basic-salary") or
            card.select_one("[class*='salary']")
        )
        sal_text = salary_el.get_text(strip=True) if salary_el else ""
        sal_from, sal_to = _parse_salary(sal_text)

        # Фильтрация на стороне клиента
        # Город: если фильтр задан но город не указан в карточке или не совпадает — пропускаем
        if city:
            if not city_text or city.lower() not in city_text.lower():
                continue

        # Зарплата: если фильтр задан но зарплата не указана или ниже порога — пропускаем
        if salary_from:
            if not sal_from or sal_from < salary_from:
                continue

        # Релевантность: хотя бы одно слово запроса должно быть в заголовке вакансии
        q_words = [w.lower() for w in query.split() if len(w) > 1]
        if q_words and not any(w in title.lower() for w in q_words):
            continue

        results.append(Vacancy(
            title=title,
            source_url=url,
            source="habr",
            company=company,
            city=city_text,
            employment_type=employment_type,
            salary_from=sal_from,
            salary_to=sal_to,
            currency="RUB",
        ))

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
        results.append(Vacancy(title=title, source_url=url, source="habr"))
        if len(results) >= 15:
            break
    return results


def _parse_salary(text: str) -> tuple[Optional[float], Optional[float]]:
    nums = re.findall(r"\d[\d\s\xa0]*\d|\d+", text)
    nums = [float(n.replace(" ", "").replace("\xa0", "")) for n in nums if n.strip()]
    if not nums:
        return None, None
    if len(nums) == 1:
        return (nums[0], None) if "от" in text else (None, nums[0])
    return nums[0], nums[1]