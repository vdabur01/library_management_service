"""Convert SQLAlchemy ORM objects → proto message objects."""
from app.proto import library_pb2
from app.models.book import Book
from app.models.member import Member
from app.models.lending import Lending, LendingStatus

_STATUS_MAP = {
    LendingStatus.ACTIVE:   library_pb2.LENDING_STATUS_ACTIVE,
    LendingStatus.RETURNED: library_pb2.LENDING_STATUS_RETURNED,
    LendingStatus.OVERDUE:  library_pb2.LENDING_STATUS_OVERDUE,
}


def book_to_proto(b: Book) -> library_pb2.Book:
    return library_pb2.Book(
        id=b.id,
        title=b.title,
        author=b.author,
        isbn=b.isbn or "",
        genre=b.genre or "",
        published_year=b.published_year or 0,
        total_copies=b.total_copies,
        available_copies=b.available_copies,
        created_at=b.created_at.isoformat() if b.created_at else "",
        updated_at=b.updated_at.isoformat() if b.updated_at else "",
    )


def member_to_proto(m: Member) -> library_pb2.Member:
    return library_pb2.Member(
        id=m.id,
        name=m.name,
        email=m.email,
        phone=m.phone or "",
        address=m.address or "",
        is_active=m.is_active,
        created_at=m.created_at.isoformat() if m.created_at else "",
        updated_at=m.updated_at.isoformat() if m.updated_at else "",
    )


def lending_to_proto(l: Lending) -> library_pb2.Lending:
    msg = library_pb2.Lending(
        id=l.id,
        book_id=l.book_id,
        member_id=l.member_id,
        borrowed_at=l.borrowed_at.isoformat() if l.borrowed_at else "",
        due_date=l.due_date.isoformat() if l.due_date else "",
        returned_at=l.returned_at.isoformat() if l.returned_at else "",
        fine_amount=float(l.fine_amount),
        status=_STATUS_MAP.get(l.status, library_pb2.LENDING_STATUS_UNSPECIFIED),
        created_at=l.created_at.isoformat() if l.created_at else "",
    )
    if l.book:
        msg.book.CopyFrom(book_to_proto(l.book))
    if l.member:
        msg.member.CopyFrom(member_to_proto(l.member))
    return msg
