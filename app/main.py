from fastapi import FastAPI, Request
from pathlib import Path
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from routers import books
from contextlib import asynccontextmanager
from app.database import Base, engine

import os

Base.metadata.create_all(bind=engine)

app = FastAPI(title="LibraryLite")

instrumentator = Instrumentator().instrument(app).expose(app)

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
static_dir = os.path.join(BASE_DIR, "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.include_router(books.router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from init_db import init_db
    init_db()
    yield


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
