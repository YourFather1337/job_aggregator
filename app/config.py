import os

DATABASE_URL: str = "sqlite:///./jobs.db"

SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production-use-strong-random-key")