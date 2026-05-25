import grpc
from app.proto import library_pb2, library_pb2_grpc
from app.utils.database import SessionLocal
from app.models.lending import LendingStatus
from app.services import lending_service
from app.services.errors import LibraryError
from app.servicers.converters import lending_to_proto
from datetime import date

_PROTO_STATUS_MAP = {
    library_pb2.LENDING_STATUS_ACTIVE:   LendingStatus.ACTIVE,
    library_pb2.LENDING_STATUS_RETURNED: LendingStatus.RETURNED,
    library_pb2.LENDING_STATUS_OVERDUE:  LendingStatus.OVERDUE,
}


def _abort(context, err: LibraryError):
    context.abort(err.code, err.message)


class LendingServicer(library_pb2_grpc.LendingServiceServicer):

    def BorrowBook(self, request, context):
        with SessionLocal() as db:
            try:
                lending = lending_service.borrow_book(db, request.book_id, request.member_id)
                return lending_to_proto(lending)
            except LibraryError as e:
                _abort(context, e)
            except Exception as e:
                context.abort(grpc.StatusCode.INTERNAL, f"Unexpected error: {e}")

    def CompleteLending(self, request, context):
        with SessionLocal() as db:
            try:
                lending = lending_service.complete_lending(db, request.lending_id)
                return lending_to_proto(lending)
            except LibraryError as e:
                _abort(context, e)
            except Exception as e:
                context.abort(grpc.StatusCode.INTERNAL, f"Unexpected error: {e}")

    def GetLending(self, request, context):
        with SessionLocal() as db:
            try:
                return lending_to_proto(lending_service.get_lending(db, request.id))
            except LibraryError as e:
                _abort(context, e)
            except Exception as e:
                context.abort(grpc.StatusCode.INTERNAL, f"Unexpected error: {e}")

    def ListLendings(self, request, context):
        with SessionLocal() as db:
            try:
                status = _PROTO_STATUS_MAP.get(request.status_filter)
                lendings = lending_service.get_lendings(
                    db, status=status,
                    member_id=request.member_id,
                    skip=request.skip,
                    limit=request.limit or 100,
                )
                return library_pb2.ListLendingsResponse(
                    lendings=[lending_to_proto(l) for l in lendings]
                )
            except Exception as e:
                context.abort(grpc.StatusCode.INTERNAL, f"Unexpected error: {e}")

    def ListOverdueLendings(self, request, context):
        with SessionLocal() as db:
            try:
                lendings = lending_service.get_overdue_lendings(db)
                return library_pb2.ListLendingsResponse(
                    lendings=[lending_to_proto(l) for l in lendings]
                )
            except Exception as e:
                context.abort(grpc.StatusCode.INTERNAL, f"Unexpected error: {e}")

    def ListMemberLendings(self, request, context):
        with SessionLocal() as db:
            try:
                lendings = lending_service.get_member_lendings(db, request.member_id)
                return library_pb2.ListLendingsResponse(
                    lendings=[lending_to_proto(l) for l in lendings]
                )
            except LibraryError as e:
                _abort(context, e)
            except Exception as e:
                context.abort(grpc.StatusCode.INTERNAL, f"Unexpected error: {e}")

    def GetStats(self, request, context):
        with SessionLocal() as db:
            from app.models.book import Book
            from app.models.member import Member
            from app.models.lending import Lending
            today = date.today()
            return library_pb2.StatsResponse(
                total_books=db.query(Book).count(),
                total_members=db.query(Member).count(),
                active_lendings=db.query(Lending).filter(
                    Lending.status == LendingStatus.ACTIVE
                ).count(),
                overdue_lendings=db.query(Lending).filter(
                    Lending.status.in_([LendingStatus.ACTIVE, LendingStatus.OVERDUE]),
                    Lending.due_date < today,
                ).count(),
            )
