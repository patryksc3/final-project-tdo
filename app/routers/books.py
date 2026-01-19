# app/routers/books.py
from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
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

def _get_book_or_404(db: Session, book_id: int) -> models.Book:
    obj = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return obj
@router.get("/")
def list_books(db: Session = Depends(get_db)):
    return db.query(models.Book).all()

@router.get("/{book_id:int}", response_model=schemas.Book)
def get_book(book_id: int, db: Session = Depends(get_db)):
    return _get_book_or_404(db, book_id)
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

@router.put("/{book_id:int}", response_model=schemas.Book)
def update_book(book_id: int, book: schemas.BookCreate, db: Session = Depends(get_db)):
    obj = _get_book_or_404(db, book_id)
    obj.title = book.title
    obj.author = book.author
    obj.year = book.year
    obj.description = book.description
    db.commit()
    db.refresh(obj)
    return obj

@router.delete("/{book_id:int}")
def delete_book(book_id: int, db: Session = Depends(get_db)):
    obj = _get_book_or_404(db, book_id)
    db.delete(obj)
    db.commit()
    return {"detail": "Book deleted"}

@router.get("/new")
def new_book_form(request: Request):
    return templates.TemplateResponse("book_new.html", {"request": request})

@router.post("/new")
async def create_book_form(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    title = (form.get("title") or "").strip()
    author = (form.get("author") or "").strip()
    year_raw = (form.get("year") or "").strip()
    description = (form.get("description") or "").strip() or None

    errors: list[str] = []
    if not title or not author:
        errors.append("Tytuł i autor są wymagane.")

    year: int | None = None
    if year_raw:
        try:
            year = int(year_raw)
        except ValueError:
            errors.append("Rok musi być liczbą całkowitą.")

    if errors:
        return templates.TemplateResponse(
            "book_new.html",
            {
                "request": request,
                "errors": errors,
                "form": {
                    "title": title,
                    "author": author,
                    "year": year_raw,
                    "description": description or "",
                },
            },
        )

    obj = models.Book(title=title, author=author, year=year, description=description)
    db.add(obj)
    db.commit()
    db.refresh(obj)

    return RedirectResponse(url="/books/page", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/{book_id:int}/edit")
def edit_book_page(book_id: int, request: Request, db: Session = Depends(get_db)):
    book = _get_book_or_404(db, book_id)
    return templates.TemplateResponse("book_edit.html", {"request": request, "book": book})

@router.post("/{book_id:int}/edit")
async def update_book_form(book_id: int, request: Request, db: Session = Depends(get_db)):
    book = _get_book_or_404(db, book_id)
    form = await request.form()
    title = form.get("title")
    author = form.get("author")
    year_raw = form.get("year")
    description = form.get("description")

    errors = []
    if not title or not author:
        errors.append("Tytuł i autor są wymagane.")

    year = None
    if year_raw:
        try:
            year = int(year_raw)
        except ValueError:
            errors.append("Rok musi być liczbą całkowitą.")

    if errors:
        return templates.TemplateResponse(
            "book_edit.html",
            {"request": request, "errors": errors, "book": book},
        )

    book.title = title
    book.author = author
    book.year = year
    book.description = description
    db.commit()
    db.refresh(book)

    return RedirectResponse(url="/books/page", status_code=status.HTTP_302_FOUND)

@router.post("/{book_id:int}/delete")
def delete_book_submit(book_id: int, db: Session = Depends(get_db)):
    book = _get_book_or_404(db, book_id)
    db.delete(book)
    db.commit()
    return RedirectResponse(url="/books/page", status_code=status.HTTP_303_SEE_OTHER)