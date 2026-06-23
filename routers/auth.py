from fastapi import Request, APIRouter, Form, Response, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["Auth"])
templates = Jinja2Templates(directory="app/templates")

async def get_current_user(request: Request):
    session_token = request.cookies.get("session_id")
    if not session_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login")

@router.get("/register")
async def get_register(request: Request):
    return templates.TemplateResponse("register.html", { "request": request })

@router.post("/register")
async def post_register(request: Request, username: str = Form(...), password: str = Form(...), email: str = Form(None)):
    return RedirectResponse(url="/login", status_code=303)

@router.get("/login")
async def get_login(request: Request):
    return templates.TemplateResponse("login.html", { "request": request })

@router.post("/login")
async def post_login(response: Response, request: Request, username: str = Form(...), password: str = Form(...)):
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="session_id", value="", httponly=True)
    return response

@router.post("/logout")
async def logout(response: Response):
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("session_id")
    return response