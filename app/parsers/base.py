from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Vacancy:
    """Единый формат вакансии для всех источников."""
    title: str
    source_url: str
    source: str                        # "hh", "remoteok", "habr", "workzilla"
    company: Optional[str] = None
    city: Optional[str] = None
    employment_type: Optional[str] = None
    salary_from: Optional[float] = None
    salary_to: Optional[float] = None
    currency: Optional[str] = "RUB"
    description: Optional[str] = None

    @property
    def salary_display(self) -> str:
        if not self.salary_from and not self.salary_to:
            return ""
        parts = []
        if self.salary_from:
            parts.append(str(int(self.salary_from)))
        if self.salary_to:
            parts.append(str(int(self.salary_to)))
        return " – ".join(parts) + f" {self.currency or ''}"