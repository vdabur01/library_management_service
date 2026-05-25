from datetime import datetime
from sqlalchemy.orm import Session

from app.models.member import Member
from app.services.errors import NotFoundError, ConflictError


def get_members(db: Session, skip: int = 0, limit: int = 100) -> list[Member]:
    return db.query(Member).offset(skip).limit(limit).all()


def get_member(db: Session, member_id: int) -> Member:
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise NotFoundError("Member not found")
    return member


def create_member(db: Session, name: str, email: str,
                  phone: str = "", address: str = "") -> Member:
    if db.query(Member).filter(Member.email == email).first():
        raise ConflictError("A member with this email already exists")

    member = Member(name=name, email=email, phone=phone or None, address=address or None)
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def update_member(db: Session, member_id: int, update_mask: list[str], **fields) -> Member:
    member = get_member(db, member_id)

    if "email" in update_mask and fields.get("email"):
        conflict = db.query(Member).filter(
            Member.email == fields["email"], Member.id != member_id
        ).first()
        if conflict:
            raise ConflictError("Another member with this email already exists")

    for field in update_mask:
        if field in fields:
            setattr(member, field, fields[field])

    member.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(member)
    return member
