from fastapi import APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers.auth import require_user
from app.models import User, Resume

router = APIRouter(prefix="/resume", tags=["Resume"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
async def view_resume(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    resume = db.query(Resume).filter(Resume.user_id == current_user.id).first()
    return templates.TemplateResponse("resume.html", {
        "request": request,
        "resume": resume,
        "current_user": current_user,
    })


@router.get("/edit")
async def get_resume_edit(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    resume = db.query(Resume).filter(Resume.user_id == current_user.id).first()
    return templates.TemplateResponse("resume_edit.html", {
        "request": request,
        "resume": resume,
        "current_user": current_user,
    })


@router.post("/edit")
async def post_resume_edit(
    request: Request,
    full_name: str = Form(...),
    about: str = Form(None),
    skills: str = Form(None),
    desired_position: str = Form(None),
    desired_salary: int = Form(None),
    city: str = Form(None),
    employment_type: str = Form(None),
    contacts: str = Form(None),
    experience: str = Form(None),
    education: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    resume = db.query(Resume).filter(Resume.user_id == current_user.id).first()
    if resume:
        resume.full_name = full_name
        resume.about = about
        resume.skills = skills
        resume.desired_position = desired_position
        resume.desired_salary = desired_salary
        resume.city = city
        resume.employment_type = employment_type
        resume.contacts = contacts
        resume.experience = experience
        resume.education = education
    else:
        resume = Resume(
            user_id=current_user.id,
            full_name=full_name,
            about=about,
            skills=skills,
            desired_position=desired_position,
            desired_salary=desired_salary,
            city=city,
            employment_type=employment_type,
            contacts=contacts,
            experience=experience,
            education=education,
        )
        db.add(resume)
    db.commit()
    return RedirectResponse(url="/resume", status_code=303)