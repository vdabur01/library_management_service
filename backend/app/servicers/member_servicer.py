import grpc
from app.proto import library_pb2, library_pb2_grpc
from app.utils.database import SessionLocal
from app.services import member_service
from app.services.errors import LibraryError
from app.servicers.converters import member_to_proto


def _abort(context, err: LibraryError):
    context.abort(err.code, err.message)


class MemberServicer(library_pb2_grpc.MemberServiceServicer):

    def CreateMember(self, request, context):
        with SessionLocal() as db:
            try:
                member = member_service.create_member(
                    db,
                    name=request.name,
                    email=request.email,
                    phone=request.phone,
                    address=request.address,
                )
                return member_to_proto(member)
            except LibraryError as e:
                _abort(context, e)
            except Exception as e:
                context.abort(grpc.StatusCode.INTERNAL, f"Unexpected error: {e}")

    def GetMember(self, request, context):
        with SessionLocal() as db:
            try:
                return member_to_proto(member_service.get_member(db, request.id))
            except LibraryError as e:
                _abort(context, e)
            except Exception as e:
                context.abort(grpc.StatusCode.INTERNAL, f"Unexpected error: {e}")

    def UpdateMember(self, request, context):
        with SessionLocal() as db:
            try:
                mask = list(request.update_mask) or ["name", "email", "phone",
                                                      "address", "is_active"]
                member = member_service.update_member(
                    db, request.id, mask,
                    name=request.name, email=request.email,
                    phone=request.phone, address=request.address,
                    is_active=request.is_active,
                )
                return member_to_proto(member)
            except LibraryError as e:
                _abort(context, e)
            except Exception as e:
                context.abort(grpc.StatusCode.INTERNAL, f"Unexpected error: {e}")

    def ListMembers(self, request, context):
        with SessionLocal() as db:
            try:
                members = member_service.get_members(db, skip=request.skip,
                                                     limit=request.limit or 100)
                return library_pb2.ListMembersResponse(
                    members=[member_to_proto(m) for m in members]
                )
            except Exception as e:
                context.abort(grpc.StatusCode.INTERNAL, f"Unexpected error: {e}")
