import enum
from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Date, Numeric, Enum
from sqlalchemy.orm import relationship
from app.utils.database import Base


class LendingStatus(str, enum.Enum):
    ACTIVE   = "active"
    RETURNED = "returned"
    OVERDUE  = "overdue"


class Lending(Base):
    __tablename__ = "lendings"

    id           = Column(Integer, primary_key=True, index=True)
    book_id      = Column(Integer, ForeignKey("books.id"), nullable=False)
    member_id    = Column(Integer, ForeignKey("members.id"), nullable=False)
    borrowed_at  = Column(DateTime, default=datetime.utcnow, nullable=False)
    due_date     = Column(Date, nullable=False)
    returned_at  = Column(DateTime, nullable=True)
    fine_amount  = Column(Numeric(10, 2), default=0, nullable=False)
    status       = Column(Enum(LendingStatus), default=LendingStatus.ACTIVE, nullable=False)
    created_at   = Column(DateTime, default=datetime.utcnow)

    book   = relationship("Book",   back_populates="lendings")
    member = relationship("Member", back_populates="lendings")
