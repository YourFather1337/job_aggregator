from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    resume = relationship("Resume", back_populates="owner", uselist=False, cascade="all, delete-orphan")
    saved_vacancies = relationship("SavedVacancy", back_populates="owner", cascade="all, delete-orphan")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)

    full_name = Column(String(255), nullable=False)
    desired_position = Column(String(255), nullable=True)
    about = Column(Text, nullable=True)
    skills = Column(Text, nullable=True)        # строка через запятую
    experience = Column(Text, nullable=True)
    education = Column(Text, nullable=True)
    city = Column(String(128), nullable=True)
    desired_salary = Column(Integer, nullable=True)
    employment_type = Column(String(64), nullable=True)
    contacts = Column(String(512), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="resume")


class SavedVacancy(Base):
    __tablename__ = "saved_vacancies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=True)
    city = Column(String(128), nullable=True)
    employment_type = Column(String(64), nullable=True)
    salary_from = Column(Float, nullable=True)
    salary_to = Column(Float, nullable=True)
    currency = Column(String(16), nullable=True)
    source = Column(String(64), nullable=True)      # hh, remoteok, habr …
    source_url = Column(String(512), nullable=False)
    saved_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    owner = relationship("User", back_populates="saved_vacancies")