# app/routers/books.py
from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path

from app import models, schemas
from app.database import SessionLocal

router = APIRouter(prefix="/books")

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/")
def list_books(db: Session = Depends(get_db)):
    return db.query(models.Book).all()


@router.get("/page")
def books_page(request: Request, db: Session = Depends(get_db)):
    books = db.query(models.Book).order_by(models.Book.id.desc()).all()
    return templates.TemplateResponse("books_page.html", {"request": request, "books": books})


@router.post("/", response_model=schemas.Book)
def create_book(book: schemas.BookCreate, db: Session = Depends(get_db)):
    obj = models.Book(
        title=book.title,
        author=book.author,
        year=book.year,
        description=book.description,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj