#!/usr/bin/env bash
# Regenerate Python gRPC stubs from proto/library.proto
# Run from the repo root: bash backend/generate_proto.sh
set -e
python -m grpc_tools.protoc \
  -I proto \
  --python_out=backend/app/proto \
  --grpc_python_out=backend/app/proto \
  proto/library.proto
echo "Stubs written to backend/app/proto/"
