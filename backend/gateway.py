"""FastAPI HTTP gateway — translates REST/JSON → gRPC calls to the gRPC server."""
import os
from typing import Optional

import grpc
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from dotenv import load_dotenv

load_dotenv()

from app.proto import library_pb2, library_pb2_grpc
from google.protobuf.json_format import MessageToDict

GRPC_SERVER = os.getenv("GRPC_SERVER", "localhost:50051")
_channel = grpc.insecure_channel(GRPC_SERVER)
_book_stub    = library_pb2_grpc.BookServiceStub(_channel)
_member_stub  = library_pb2_grpc.MemberServiceStub(_channel)
_lending_stub = library_pb2_grpc.LendingServiceStub(_channel)

_GRPC_TO_HTTP = {
    grpc.StatusCode.NOT_FOUND:        404,
    grpc.StatusCode.ALREADY_EXISTS:   409,
    grpc.StatusCode.INVALID_ARGUMENT: 400,
}

app = FastAPI(
    title="Neighborhood Library — HTTP Gateway",
    description="REST facade over the gRPC library service",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://0.0.0.0:3000",
    ],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1|0\.0\.0\.0)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except grpc.RpcError as e:
        status = _GRPC_TO_HTTP.get(e.code(), 500)
        raise HTTPException(status_code=status, detail=e.details())


def _proto(msg):
    return MessageToDict(msg, preserving_proto_field_name=True)


# ── Pydantic input models ──────────────────────────────────────────────────────

class BookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    author: str = Field(..., min_length=1, max_length=255)
    isbn: Optional[str] = Field(default="", max_length=50)
    genre: Optional[str] = Field(default="", max_length=100)
    published_year: Optional[int] = Field(default=0, ge=0, le=9999)
    total_copies: int = Field(default=1, ge=1)

class BookUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=255)
    author: Optional[str] = Field(default=None, max_length=255)
    isbn: Optional[str] = Field(default=None, max_length=50)
    genre: Optional[str] = Field(default=None, max_length=100)
    published_year: Optional[int] = Field(default=None, ge=0, le=9999)
    total_copies: Optional[int] = Field(default=None, ge=1)

class MemberCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: Optional[str] = Field(default="", max_length=50)
    address: Optional[str] = Field(default="", max_length=500)

class MemberUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=50)
    address: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = None

class LendingCreate(BaseModel):
    book_id: int
    member_id: int


# ── Books ──────────────────────────────────────────────────────────────────────

@app.get("/books")
def list_books(skip: int = 0, limit: int = 100):
    r = _call(_book_stub.ListBooks, library_pb2.ListBooksRequest(skip=skip, limit=limit))
    return [_proto(b) for b in r.books]

@app.get("/books/{book_id}")
def get_book(book_id: int):
    return _proto(_call(_book_stub.GetBook, library_pb2.GetBookRequest(id=book_id)))

@app.post("/books", status_code=201)
def create_book(body: BookCreate):
    return _proto(_call(_book_stub.CreateBook, library_pb2.CreateBookRequest(
        title=body.title, author=body.author,
        isbn=body.isbn or "", genre=body.genre or "",
        published_year=body.published_year or 0,
        total_copies=body.total_copies,
    )))

@app.put("/books/{book_id}")
def update_book(book_id: int, body: BookUpdate):
    mask = [f for f, v in body.model_dump(exclude_unset=True).items() if v is not None]
    data = body.model_dump(exclude_unset=True)
    return _proto(_call(_book_stub.UpdateBook, library_pb2.UpdateBookRequest(
        id=book_id,
        title=data.get("title", ""),
        author=data.get("author", ""),
        isbn=data.get("isbn", ""),
        genre=data.get("genre", ""),
        published_year=data.get("published_year", 0),
        total_copies=data.get("total_copies", 0),
        update_mask=mask,
    )))

@app.delete("/books/{book_id}")
def delete_book(book_id: int):
    return _proto(_call(_book_stub.DeleteBook, library_pb2.DeleteBookRequest(id=book_id)))


# ── Members ────────────────────────────────────────────────────────────────────

@app.get("/members")
def list_members(skip: int = 0, limit: int = 100):
    r = _call(_member_stub.ListMembers, library_pb2.ListMembersRequest(skip=skip, limit=limit))
    return [_proto(m) for m in r.members]

@app.get("/members/{member_id}")
def get_member(member_id: int):
    return _proto(_call(_member_stub.GetMember, library_pb2.GetMemberRequest(id=member_id)))

@app.post("/members", status_code=201)
def create_member(body: MemberCreate):
    return _proto(_call(_member_stub.CreateMember, library_pb2.CreateMemberRequest(
        name=body.name, email=body.email,
        phone=body.phone or "", address=body.address or "",
    )))

@app.put("/members/{member_id}")
def update_member(member_id: int, body: MemberUpdate):
    mask = list(body.model_dump(exclude_unset=True).keys())
    data = body.model_dump(exclude_unset=True)
    return _proto(_call(_member_stub.UpdateMember, library_pb2.UpdateMemberRequest(
        id=member_id,
        name=data.get("name", ""),
        email=str(data.get("email", "")),
        phone=data.get("phone", ""),
        address=data.get("address", ""),
        is_active=data.get("is_active", True),
        update_mask=mask,
    )))


# ── Lendings ───────────────────────────────────────────────────────────────────

_STR_STATUS = {
    "active":   library_pb2.LENDING_STATUS_ACTIVE,
    "returned": library_pb2.LENDING_STATUS_RETURNED,
    "overdue":  library_pb2.LENDING_STATUS_OVERDUE,
}

@app.get("/lendings")
def list_lendings(status: Optional[str] = None, member_id: Optional[int] = None,
                  skip: int = 0, limit: int = 100):
    r = _call(_lending_stub.ListLendings, library_pb2.ListLendingsRequest(
        status_filter=_STR_STATUS.get(status or "", library_pb2.LENDING_STATUS_UNSPECIFIED),
        member_id=member_id or 0, skip=skip, limit=limit,
    ))
    return [_proto(l) for l in r.lendings]

@app.get("/lendings/overdue")
def list_overdue_lendings():
    r = _call(_lending_stub.ListOverdueLendings, library_pb2.GetStatsRequest())
    return [_proto(l) for l in r.lendings]

@app.get("/lendings/member/{member_id}")
def list_member_lendings(member_id: int):
    r = _call(_lending_stub.ListMemberLendings,
              library_pb2.ListMemberLendingsRequest(member_id=member_id))
    return [_proto(l) for l in r.lendings]

@app.get("/lendings/{lending_id}")
def get_lending(lending_id: int):
    return _proto(_call(_lending_stub.GetLending, library_pb2.GetLendingRequest(id=lending_id)))

@app.post("/lendings", status_code=201)
def borrow_book(body: LendingCreate):
    return _proto(_call(_lending_stub.BorrowBook, library_pb2.BorrowBookRequest(
        book_id=body.book_id, member_id=body.member_id,
    )))

@app.put("/lendings/{lending_id}/complete")
def complete_lending(lending_id: int):
    return _proto(_call(_lending_stub.CompleteLending,
                        library_pb2.CompleteLendingRequest(lending_id=lending_id)))


# ── Stats ──────────────────────────────────────────────────────────────────────

@app.get("/stats")
def get_stats():
    return _proto(_call(_lending_stub.GetStats, library_pb2.GetStatsRequest()))

@app.get("/health")
def health():
    return {"status": "ok"}
