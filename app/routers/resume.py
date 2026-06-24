from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import Resume
from app.routers.auth import require_current_user

router = APIRouter(prefix="/resume", tags=["Resume"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def resume_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_current_user),
):
    resume = db.query(Resume).filter(Resume.user_id == current_user.id).first()
    return templates.TemplateResponse("resume.html", {
        "request": request,
        "current_user": current_user,
        "resume": resume,
    })


@router.get("/edit")
def resume_edit_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_current_user),
):
    resume = db.query(Resume).filter(Resume.user_id == current_user.id).first()
    return templates.TemplateResponse("resume_edit.html", {
        "request": request,
        "current_user": current_user,
        "resume": resume,
        "error": None,
    })


@router.post("/edit")
def resume_edit_save(
    request: Request,
    full_name: str = Form(...),
    desired_position: str = Form(""),
    about: str = Form(""),
    skills: str = Form(""),
    experience: str = Form(""),
    education: str = Form(""),
    city: str = Form(""),
    desired_salary: Optional[int] = Form(None),
    employment_type: str = Form(""),
    contacts: str = Form(""),
    db: Session = Depends(get_db),
    current_user=Depends(require_current_user),
):
    resume = db.query(Resume).filter(Resume.user_id == current_user.id).first()

    if resume is None:
        # Создаём новое резюме
        resume = Resume(user_id=current_user.id)
        db.add(resume)

    resume.full_name = full_name.strip()
    resume.desired_position = desired_position.strip() or None
    resume.about = about.strip() or None
    resume.skills = skills.strip() or None
    resume.experience = experience.strip() or None
    resume.education = education.strip() or None
    resume.city = city.strip() or None
    resume.desired_salary = desired_salary
    resume.employment_type = employment_type or None
    resume.contacts = contacts.strip() or None

    db.commit()
    return RedirectResponse(url="/resume", status_code=303)