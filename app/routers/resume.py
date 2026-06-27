from fastapi import APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Resume
from app.routers.auth import require_user

router = APIRouter(prefix="/resume", tags=["Resume"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def view_resume(
    request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)
):
    resume = db.query(Resume).filter(Resume.user_id == user.id).first()
    return templates.TemplateResponse(
        "resume.html", {"request": request, "resume": resume, "current_user": user}
    )


@router.get("/edit")
def get_resume_edit(
    request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)
):
    resume = db.query(Resume).filter(Resume.user_id == user.id).first()
    return templates.TemplateResponse(
        "resume_edit.html", {"request": request, "resume": resume, "current_user": user}
    )


@router.post("/edit")
def post_resume_edit(
    request: Request,
    full_name: str = Form(...),
    desired_position: str | None = Form(None),
    about: str | None = Form(None),
    skills: str | None = Form(None),
    experience: str | None = Form(None),
    education: str | None = Form(None),
    city: str | None = Form(None),
    desired_salary: str | None = Form(None),
    employment_type: str | None = Form(None),
    contacts: str | None = Form(None),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    resume = db.query(Resume).filter(Resume.user_id == user.id).first()
    if not resume:
        resume = Resume(user_id=user.id)
        db.add(resume)

    resume.full_name = full_name
    resume.desired_position = desired_position
    resume.about = about
    resume.skills = skills
    resume.experience = experience
    resume.education = education
    resume.city = city

    if desired_salary:
        try:
            resume.desired_salary = int(desired_salary)
        except ValueError:
            resume.desired_salary = None
    else:
        resume.desired_salary = None

    resume.employment_type = employment_type
    resume.contacts = contacts

    db.commit()

    return RedirectResponse(url="/resume", status_code=303)
