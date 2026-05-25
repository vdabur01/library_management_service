from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload

from app.models.book import Book
from app.models.member import Member
from app.models.lending import Lending, LendingStatus
from app.services.errors import NotFoundError, ConflictError, ValidationError

LENDING_DAYS  = 14
FINE_PER_DAY  = Decimal("0.25")


def _refresh_overdue(db: Session) -> None:
    today = date.today()
    for lending in db.query(Lending).filter(
        Lending.status == LendingStatus.ACTIVE, Lending.due_date < today
    ).all():
        lending.status = LendingStatus.OVERDUE
        lending.fine_amount = (today - lending.due_date).days * FINE_PER_DAY
    db.commit()


def _eager(query):
    return query.options(joinedload(Lending.book), joinedload(Lending.member))


def get_lendings(db: Session, status: LendingStatus | None = None,
                 member_id: int = 0, skip: int = 0, limit: int = 100) -> list[Lending]:
    _refresh_overdue(db)
    q = _eager(db.query(Lending))
    if status:
        q = q.filter(Lending.status == status)
    if member_id:
        q = q.filter(Lending.member_id == member_id)
    return q.order_by(Lending.borrowed_at.desc()).offset(skip).limit(limit).all()


def get_lending(db: Session, lending_id: int) -> Lending:
    lending = _eager(db.query(Lending)).filter(Lending.id == lending_id).first()
    if not lending:
        raise NotFoundError("Lending not found")
    return lending


def borrow_book(db: Session, book_id: int, member_id: int) -> Lending:
    book = db.query(Book).filter(Book.id == book_id).with_for_update().first()
    if not book:
        raise NotFoundError("Book not found")
    if book.available_copies <= 0:
        raise ValidationError("No copies of this book are currently available")

    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise NotFoundError("Member not found")
    if not member.is_active:
        raise ValidationError("Member account is inactive")

    if db.query(Lending).filter(
        Lending.book_id == book_id, Lending.member_id == member_id,
        Lending.status.in_([LendingStatus.ACTIVE, LendingStatus.OVERDUE]),
    ).first():
        raise ConflictError("Member already has an active lending for this book")

    lending = Lending(
        book_id=book_id, member_id=member_id,
        due_date=date.today() + timedelta(days=LENDING_DAYS),
    )
    book.available_copies -= 1
    db.add(lending)
    db.commit()
    db.refresh(lending)
    return get_lending(db, lending.id)


def complete_lending(db: Session, lending_id: int) -> Lending:
    lending = db.query(Lending).filter(
        Lending.id == lending_id,
        Lending.status.in_([LendingStatus.ACTIVE, LendingStatus.OVERDUE]),
    ).with_for_update().first()
    if not lending:
        raise NotFoundError("Active lending not found")

    today = date.today()
    lending.returned_at = datetime.utcnow()
    lending.status = LendingStatus.RETURNED
    if today > lending.due_date:
        lending.fine_amount = (today - lending.due_date).days * FINE_PER_DAY

    book = db.query(Book).filter(Book.id == lending.book_id).with_for_update().first()
    book.available_copies += 1
    db.commit()
    return get_lending(db, lending.id)


def get_overdue_lendings(db: Session) -> list[Lending]:
    _refresh_overdue(db)
    return _eager(
        db.query(Lending).filter(Lending.status == LendingStatus.OVERDUE)
    ).order_by(Lending.due_date).all()


def get_member_lendings(db: Session, member_id: int) -> list[Lending]:
    if not db.query(Member).filter(Member.id == member_id).first():
        raise NotFoundError("Member not found")
    return get_lendings(db, member_id=member_id, limit=500)
