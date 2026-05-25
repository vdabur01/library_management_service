"""gRPC server — listens on :50051."""
import os
import grpc
from concurrent import futures
from dotenv import load_dotenv

load_dotenv()

from app.proto import library_pb2_grpc
from app.servicers.book_servicer import BookServicer
from app.servicers.member_servicer import MemberServicer
from app.servicers.lending_servicer import LendingServicer


def serve():
    port = os.getenv("GRPC_PORT", "50051")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    library_pb2_grpc.add_BookServiceServicer_to_server(BookServicer(), server)
    library_pb2_grpc.add_MemberServiceServicer_to_server(MemberServicer(), server)
    library_pb2_grpc.add_LendingServiceServicer_to_server(LendingServicer(), server)

    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"gRPC server started on port {port}", flush=True)
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
