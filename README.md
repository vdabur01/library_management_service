# Neighborhood Library Service

A full-stack library management system built with:

- **Backend**: Python · gRPC (grpcio) · FastAPI · SQLAlchemy · PostgreSQL · Alembic
- **Frontend**: React 18 · Vite · TypeScript · Tailwind CSS · React Router v6

---

## Features

| Capability | Details |
|---|---|
| Books | Create, update, delete books with copy tracking |
| Members | Register/manage members, activate/deactivate accounts |
| Borrowing | Borrow a book (tracks available copies, prevents double-borrow) |
| Completing | Complete a lending with automatic fine calculation |
| Overdue tracking | Lendings past due date are flagged; fine = $0.25/day |
| Dashboard | Live stats: total books, members, active & overdue lendings |

---

## Architecture

```
Browser → HTTP/JSON → FastAPI gateway (:8000) → gRPC → gRPC server (:50051) → PostgreSQL
```

- **`grpc_server.py`** — gRPC server on `:50051`. Implements all business logic via SQLAlchemy.
- **`gateway.py`** — FastAPI HTTP gateway on `:8000`. Translates REST/JSON ↔ gRPC.
- **`proto/library.proto`** — Single proto file defining `BookService`, `MemberService`, `LendingService`.

---

## Quick Start (Docker)

**Prerequisites**: Docker and Docker Compose installed.

```bash
git clone <repo>
cd library-service
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API (HTTP gateway) | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Docs (ReDoc) | http://localhost:8000/redoc |
| gRPC server | localhost:50051 |

On first startup `entrypoint.sh` runs `alembic upgrade head` automatically before the gRPC server starts.

---

## Manual Setup

### Backend

**Requirements**: Python 3.11+, PostgreSQL 14+

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
# .venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — set DATABASE_URL and optionally GRPC_PORT / GRPC_SERVER

# Terminal 1 — apply migrations, then start the gRPC server
alembic upgrade head
python grpc_server.py

# Terminal 2 — start the HTTP gateway
uvicorn gateway:app --reload
```

The HTTP gateway starts at **http://localhost:8000**.

#### Adding a new migration

After changing an ORM model, generate and apply a migration:

```bash
alembic revision --autogenerate -m "describe your change"
alembic upgrade head
```

Alembic is the **only** way the schema is managed — there is no `create_all` fallback. Never modify the database schema by hand; always go through migrations.

#### Regenerating gRPC stubs

Run this from the repo root after editing `proto/library.proto`:

```bash
bash backend/generate_proto.sh
```

### Frontend

**Requirements**: Node.js 20+

```bash
cd frontend
npm install

# Set the API URL (defaults to http://localhost:8000)
cp .env.example .env
# Edit VITE_API_URL if your gateway runs on a different port

npm run dev
```

The app starts at **http://localhost:3000**.

---

## REST API Reference

### Books

| Method | Endpoint | Description |
|---|---|---|
| GET | `/books` | List all books |
| POST | `/books` | Create a book |
| GET | `/books/{id}` | Get a book |
| PUT | `/books/{id}` | Update a book |
| DELETE | `/books/{id}` | Delete a book |

### Members

| Method | Endpoint | Description |
|---|---|---|
| GET | `/members` | List all members |
| POST | `/members` | Register a member |
| GET | `/members/{id}` | Get a member |
| PUT | `/members/{id}` | Update a member |

### Lendings

| Method | Endpoint | Description |
|---|---|---|
| GET | `/lendings` | List lendings (filter: `?status=active\|overdue\|returned&member_id=N`) |
| POST | `/lendings` | Borrow a book |
| PUT | `/lendings/{id}/complete` | Complete a lending (return book) |
| GET | `/lendings/overdue` | List all overdue lendings |
| GET | `/lendings/member/{id}` | All lendings for a member |
| GET | `/lendings/{id}` | Get a specific lending |

### Other

| Method | Endpoint | Description |
|---|---|---|
| GET | `/stats` | Dashboard statistics |
| GET | `/health` | Health check |

---

## Sample API Calls

```bash
# Create a book
curl -X POST http://localhost:8000/books \
  -H "Content-Type: application/json" \
  -d '{"title":"The Great Gatsby","author":"F. Scott Fitzgerald","isbn":"9780743273565","total_copies":3}'

# Register a member
curl -X POST http://localhost:8000/members \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice Smith","email":"alice@example.com","phone":"555-1234"}'

# Borrow a book (use IDs returned above)
curl -X POST http://localhost:8000/lendings \
  -H "Content-Type: application/json" \
  -d '{"book_id":1,"member_id":1}'

# Complete a lending (return the book)
curl -X PUT http://localhost:8000/lendings/1/complete

# List overdue lendings
curl http://localhost:8000/lendings/overdue
```

---

## Database Schema

```
books
  id, title, author, isbn (unique), genre, published_year,
  total_copies, available_copies, created_at, updated_at

members
  id, name, email (unique), phone, address,
  is_active, created_at, updated_at

lendings
  id, book_id → books.id, member_id → members.id,
  borrowed_at, due_date, returned_at,
  fine_amount, status (active|returned|overdue), created_at
```

Business rules:
- `available_copies` is decremented on borrow, incremented on complete
- `due_date` = borrow date + 14 days
- Overdue fine = `$0.25 × days_late`, calculated on complete or status refresh
