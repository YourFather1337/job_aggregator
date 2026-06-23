from fastapi import APIRouter, Request, Query
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["Search"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
async def get_index(request: Request):
    return templates.TemplateResponse("index.html", { "request": request })

@router.get("/search")
async def search(request: Request, q: str = Query(..., description="Search request"), salary: int = Query(None), city: str = Query(None), employment_type: str = Query(None)):
    results = []

    return templates.TemplateResponse("search.html", { "request": request, "q": q, "results": results })