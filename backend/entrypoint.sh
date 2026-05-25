#!/bin/sh
set -e
echo "Running Alembic migrations…"
alembic upgrade head
echo "Starting gRPC server…"
exec python grpc_server.py
