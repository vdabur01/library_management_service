# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Full-stack neighborhood library management system. Python gRPC backend + FastAPI HTTP gateway + React/Vite frontend + PostgreSQL.

## Commands

### Quickstart (Docker)
```bash
docker compose up --build
# gRPC server: :50051  HTTP gateway: :8000  Frontend: :3000
```

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env  # set DATABASE_URL

alembic upgrade head               # REQUIRED before first run — creates all tables
python grpc_server.py              # start gRPC server on :50051
uvicorn gateway:app --reload       # start HTTP gateway on :8000 (separate terminal)

alembic revision --autogenerate -m "description"  # generate migration after model changes
alembic upgrade head               # apply pending migrations
```

### Regenerate gRPC stubs (after editing proto/library.proto)
```bash
# From repo root:
bash backend/generate_proto.sh
# or manually:
python -m grpc_tools.protoc -I proto --python_out=backend/app/proto --grpc_python_out=backend/app/proto proto/library.proto
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env               # set VITE_API_URL=http://localhost:8000
npm run dev                        # start dev server on :3000
npm run build                      # production build (tsc + vite)
```

## Architecture

```
Browser → HTTP/JSON → FastAPI gateway (:8000) → gRPC → gRPC server (:50051) → PostgreSQL
```

### gRPC layer (`proto/library.proto`)

Single proto file defines three services: `BookService`, `MemberService`, `LendingService`. Key conventions:
- Dates are ISO strings (not timestamps).
- Partial updates use a `repeated string update_mask` field on all Update requests.
- `CompleteLending` is the RPC for returning a borrowed book (avoids the Python keyword `return`).
- `GetStatsRequest` is reused as the empty-message type for `ListOverdueLendings`.

Generated stubs live at `backend/app/proto/library_pb2.py` and `library_pb2_grpc.py`.

### gRPC server (`backend/grpc_server.py`)

Starts on `:50051`. Registers `BookServicer`, `MemberServicer`, `LendingServicer`. Calls `Base.metadata.create_all()` on startup.

### HTTP gateway (`backend/gateway.py`)

FastAPI app on `:8000`. Opens a single insecure gRPC channel to `GRPC_SERVER` env var (default `localhost:50051`). Translates REST/JSON ↔ gRPC using `google.protobuf.json_format.MessageToDict`. Maps gRPC status codes to HTTP status codes via `_GRPC_TO_HTTP`.

### Backend service layer (`backend/app/`)

Layered: **servicer → service → SQLAlchemy model**.

- `app/utils/database.py` — SQLAlchemy engine, `SessionLocal` (used as context manager), `Base`.
- `app/models/` — ORM models (`Book`, `Member`, `Lending`). `models/__init__.py` imports all three.
- `app/services/errors.py` — Custom exception hierarchy: `LibraryError`, `NotFoundError`, `ConflictError`, `ValidationError`. Services raise these; servicers map them to `context.abort()`.
- `app/services/` — all business logic. No dependency on gRPC or HTTP.
- `app/servicers/` — gRPC servicers that call services and convert ORM objects to proto messages via `converters.py`.

**Key business rules in `lending_service.py`:**
- `borrow_book`: checks `available_copies > 0`, member `is_active`, no duplicate active lending; decrements `available_copies` with `with_for_update()`.
- `complete_lending`: calculates fine (`$0.25 × days_late`), increments `available_copies`, sets status to `RETURNED`.
- `_refresh_overdue()`: called on every `get_lendings` — updates status and fine for any lendings past `due_date`.
- Default lending period: 14 days (`LENDING_DAYS = 14`).

**Alembic is the sole schema source of truth.** There is no `create_all` fallback. `alembic/versions/001_initial_schema.py` contains the full initial migration. `alembic/env.py` reads `DATABASE_URL` from the environment. In Docker, `entrypoint.sh` runs `alembic upgrade head` before starting the gRPC server.

### Frontend (`frontend/`)

React 18 SPA with Vite. Routing via React Router v6 (`BrowserRouter` in `App.tsx`).

- `src/main.tsx` — entry point, mounts `<App />`.
- `src/App.tsx` — declares all routes and the top nav bar with `NavLink`.
- `src/pages/` — one component per route: `Dashboard`, `Books`, `Members`, `Lending`.
- `src/lib/api.ts` — all `fetch` calls grouped into `booksApi`, `membersApi`, `lendingsApi`, `statsApi`. API base URL from `import.meta.env.VITE_API_URL`.
- `src/types/index.ts` — all TypeScript interfaces shared across pages.
- `src/components/ui/Modal.tsx` — single shared modal (closes on Escape or overlay click).

**Lending page tabs:** Active / Overdue / Returned. Tab state is reflected in `?tab=overdue` query param via `useSearchParams` + `useNavigate`.

### Database Schema

```
books:    id, title, author, isbn(unique), genre, published_year, total_copies, available_copies
members:  id, name, email(unique), phone, address, is_active
lendings: id, book_id→books, member_id→members, borrowed_at, due_date, returned_at, fine_amount, status(active|returned|overdue)
```

`available_copies` is a denormalized counter kept in sync by the lending service (not computed from the lendings table).

## Environment Variables

| Variable | Where | Default |
|---|---|---|
| `DATABASE_URL` | `backend/.env` | `postgresql://library_user:library_pass@localhost:5432/library_db` |
| `GRPC_PORT` | `backend/.env` | `50051` |
| `GRPC_SERVER` | `backend/.env` | `localhost:50051` |
| `VITE_API_URL` | `frontend/.env` | `http://localhost:8000` |

Docker Compose uses `library_user` / `library_pass` / `library_db` — match these in `.env` for local dev against the Docker DB.
