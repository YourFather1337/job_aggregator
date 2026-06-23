from fastapi import APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from routers.auth import get_current_user

router = APIRouter(prefix="/resume", tags=["Resume"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/")
async def view_resume(request: Request, user: dict = Depends(get_current_user)):
    resume_data = {}
    return templates.TemplateResponse("resume.html", { "request": request, "resume": resume_data })

@router.get("/edit")
async def get_resume_edit(request: Request, user: dict = Depends(get_current_user)):
    resume_data = {}
    return templates.TemplateResponse("resume_edit.html", { "request": request, "resume": resume_data })

@router.post("edit")
async def post_resume_edit(request: Request, full_name: str = Form(...), about: str = Form(None), skills: str = Form(None), desired_position: str = Form(None), user: dict = Depends(get_current_user)):
    return RedirectResponse(url="/resume", status_code=303)