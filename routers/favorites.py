from fastapi import APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from routers.auth import get_current_user

router = APIRouter(prefix="/favorites", tags=["Favorites"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/")
async def get_favorites(request: Request, user: dict = Depends(get_current_user)):
    favorites_list = []
    return templates.TemplateResponse("favorites.html", { "request": request, "favorites": favorites_list })

@router.post("/add")
async def add_favorites(request: Request, title: str = Form(...), source_url: str = Form(...), company: str = Form(None), user: dict = Depends(get_current_user)):
    referer = request.headers.get("referer", "/")
    return RedirectResponse(url=referer, status_code=303)

@router.delete("/{id}")
async def delete_favorite(id: int, user: dict = Depends(get_current_user)):
    return { "status": "success", "message": "Delete from favorites" }