import grpc
from app.proto import library_pb2, library_pb2_grpc
from app.utils.database import SessionLocal
from app.services import book_service
from app.services.errors import LibraryError
from app.servicers.converters import book_to_proto


def _abort(context, err: LibraryError):
    context.abort(err.code, err.message)


class BookServicer(library_pb2_grpc.BookServiceServicer):

    def CreateBook(self, request, context):
        with SessionLocal() as db:
            try:
                book = book_service.create_book(
                    db,
                    title=request.title,
                    author=request.author,
                    isbn=request.isbn,
                    genre=request.genre,
                    published_year=request.published_year,
                    total_copies=request.total_copies or 1,
                )
                return book_to_proto(book)
            except LibraryError as e:
                _abort(context, e)
            except Exception as e:
                context.abort(grpc.StatusCode.INTERNAL, f"Unexpected error: {e}")

    def GetBook(self, request, context):
        with SessionLocal() as db:
            try:
                return book_to_proto(book_service.get_book(db, request.id))
            except LibraryError as e:
                _abort(context, e)
            except Exception as e:
                context.abort(grpc.StatusCode.INTERNAL, f"Unexpected error: {e}")

    def UpdateBook(self, request, context):
        with SessionLocal() as db:
            try:
                mask = list(request.update_mask) or ["title", "author", "isbn", "genre",
                                                      "published_year", "total_copies"]
                book = book_service.update_book(
                    db, request.id, mask,
                    title=request.title, author=request.author,
                    isbn=request.isbn, genre=request.genre,
                    published_year=request.published_year,
                    total_copies=request.total_copies,
                )
                return book_to_proto(book)
            except LibraryError as e:
                _abort(context, e)
            except Exception as e:
                context.abort(grpc.StatusCode.INTERNAL, f"Unexpected error: {e}")

    def DeleteBook(self, request, context):
        with SessionLocal() as db:
            try:
                msg = book_service.delete_book(db, request.id)
                return library_pb2.DeleteBookResponse(message=msg)
            except LibraryError as e:
                _abort(context, e)
            except Exception as e:
                context.abort(grpc.StatusCode.INTERNAL, f"Unexpected error: {e}")

    def ListBooks(self, request, context):
        with SessionLocal() as db:
            try:
                books = book_service.get_books(db, skip=request.skip,
                                               limit=request.limit or 100)
                return library_pb2.ListBooksResponse(books=[book_to_proto(b) for b in books])
            except Exception as e:
                context.abort(grpc.StatusCode.INTERNAL, f"Unexpected error: {e}")
