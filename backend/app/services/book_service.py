from datetime import datetime
from sqlalchemy.orm import Session

from app.models.book import Book
from app.models.lending import Lending, LendingStatus
from app.services.errors import NotFoundError, ConflictError, ValidationError


def get_books(db: Session, skip: int = 0, limit: int = 100) -> list[Book]:
    return db.query(Book).offset(skip).limit(limit).all()


def get_book(db: Session, book_id: int) -> Book:
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise NotFoundError("Book not found")
    return book


def create_book(db: Session, title: str, author: str, isbn: str = "",
                genre: str = "", published_year: int = 0, total_copies: int = 1) -> Book:
    if total_copies < 1:
        raise ValidationError("total_copies must be at least 1")
    if isbn:
        if db.query(Book).filter(Book.isbn == isbn).first():
            raise ConflictError("A book with this ISBN already exists")

    book = Book(
        title=title, author=author,
        isbn=isbn or None, genre=genre or None,
        published_year=published_year or None,
        total_copies=total_copies, available_copies=total_copies,
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def update_book(db: Session, book_id: int, update_mask: list[str], **fields) -> Book:
    book = get_book(db, book_id)

    if "isbn" in update_mask and fields.get("isbn"):
        conflict = db.query(Book).filter(Book.isbn == fields["isbn"], Book.id != book_id).first()
        if conflict:
            raise ConflictError("Another book with this ISBN already exists")

    if "total_copies" in update_mask:
        new_total = fields["total_copies"]
        if new_total < 1:
            raise ValidationError("total_copies must be at least 1")
        active = db.query(Lending).filter(
            Lending.book_id == book_id,
            Lending.status.in_([LendingStatus.ACTIVE, LendingStatus.OVERDUE]),
        ).count()
        if new_total < active:
            raise ValidationError(f"Cannot set total_copies below active lending count ({active})")
        book.available_copies = new_total - active
        book.total_copies = new_total
        update_mask = [f for f in update_mask if f != "total_copies"]

    for field in update_mask:
        value = fields.get(field)
        if value is not None:
            setattr(book, field, value or None if field in ("isbn", "genre") else value)

    book.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(book)
    return book


def delete_book(db: Session, book_id: int) -> str:
    book = get_book(db, book_id)
    active = db.query(Lending).filter(
        Lending.book_id == book_id,
        Lending.status.in_([LendingStatus.ACTIVE, LendingStatus.OVERDUE]),
    ).count()
    if active:
        raise ValidationError("Cannot delete a book with active lendings")
    db.delete(book)
    db.commit()
    return "Book deleted"
