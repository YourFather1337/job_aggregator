from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routers import auth, search, favorites, resume

app = FastAPI(title="Job Aggregator")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(search.router)
app.include_router(auth.router)
app.include_router(favorites.router)
app.include_router(resume.router)