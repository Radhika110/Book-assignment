from pathlib import Path
from typing import Literal, cast

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

BookStatus = Literal["to-read", "reading", "done"]
BOOK_STATUSES: tuple[BookStatus, ...] = ("to-read", "reading", "done")

app = FastAPI()
INDEX_FILE = Path(__file__).with_name("index.html")


@app.get("/", include_in_schema=False)
def homepage() -> FileResponse:
    return FileResponse(INDEX_FILE)


class BookCreate(BaseModel):
    title: str = Field(min_length=1)
    author: str
    status: str


class BookStatusUpdate(BaseModel):
    status: str


class Book(BaseModel):
    id: int
    title: str
    author: str
    status: BookStatus


books: list[Book] = []


def validate_status(status: str) -> BookStatus:
    if status not in BOOK_STATUSES:
        allowed_statuses = ", ".join(BOOK_STATUSES)
        raise HTTPException(
            status_code=400,
            detail=f"status must be one of: {allowed_statuses}",
        )
    return cast(BookStatus, status)


@app.post("/books", response_model=Book, status_code=201)
def create_book(book_data: BookCreate) -> Book:
    status = validate_status(book_data.status)
    book = Book(
        id=len(books) + 1,
        title=book_data.title,
        author=book_data.author,
        status=status,
    )
    books.append(book)
    return book


@app.patch("/books/{book_id}", response_model=Book)
def update_book_status(book_id: int, update: BookStatusUpdate) -> Book:
    book = next((book for book in books if book.id == book_id), None)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    book.status = validate_status(update.status)
    return book


@app.get("/books", response_model=list[Book])
def list_books(status: str | None = None) -> list[Book]:
    if status is None:
        return books
    validated_status = validate_status(status)
    return [book for book in books if book.status == validated_status]


@app.get("/books/count-by-status", response_model=dict[str, int])
def count_books_by_status() -> dict[str, int]:
    return {
        status: sum(book.status == status for book in books)
        for status in BOOK_STATUSES
    }