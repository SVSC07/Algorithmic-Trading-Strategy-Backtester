# Algorithmic Trading Strategy Backtester — Backend

Software Engineering Mini Project — JSS University Noida  
**Member C / Lead:** Molik Gupta (Metrics Engine & API Lead, Integration Owner)

---

## 1. Stack & Architecture

- **Runtime:** Python 3.11+
- **Framework:** FastAPI
- **Database & ORM:** PostgreSQL / SQLite (for test runs), SQLAlchemy 2.0+
- **Migrations:** Alembic
- **Analytics & Math:** pandas, numpy, math
- **Authentication:** bcrypt password hashing, PyJWT (HS256)
- **Port:** `8000` (FastAPI) | Frontend `5173` (Vite)
- **CORS Allowed Origin:** `http://localhost:5173`

---

## 2. Environment Variables

The backend requires the following environment variables:

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string (or SQLite URI in development/test) | `postgresql://postgres:postgres@localhost:5432/trading_db` |
| `SECRET_KEY` | Secret key for signing JWT tokens (min 32 bytes recommended) | `your-secure-jwt-signing-key-here-32chars` |

---

## 3. Setup & Running

### Option A: Running with Docker Compose (PostgreSQL)

1. Start the PostgreSQL database service:
   ```bash
   docker compose up -d
   ```

2. Run database migrations:
   ```bash
   alembic upgrade head
   ```

3. Seed the database with the initial Administrator, Demo Trader, and sample price data:
   ```bash
   python scripts/seed.py
   ```

4. Start the FastAPI application server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

Interactive API documentation will be available at:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- Health check: [http://localhost:8000/health](http://localhost:8000/health)

### Option B: Local Development with SQLite

If PostgreSQL is not running locally, SQLite in-memory or file-based database can be used:

```bash
export DATABASE_URL="sqlite:///./dev.db"
export SECRET_KEY="dev-secret-key-at-least-32-bytes-long"
python scripts/seed.py
uvicorn app.main:app --reload --port 8000
```

---

## 4. Running Tests

Execute the test suite using pytest from the `backend/` directory:

```bash
cd backend
pytest -q
```

Or for verbose output with coverage:

```bash
pytest -v
```

Tests run completely in-memory using SQLite and do not require PostgreSQL or external networks.

---

## 5. Endpoints & API Contract Reference

Base path: `/api`  
All error responses adhere to standard envelope: `{"error": {"code": "...", "message": "..."}}`  
Authentication header: `Authorization: Bearer <token>`

| Method | Endpoint | Allowed Roles | Description | Status Code |
|---|---|---|---|---|
| `POST` | `/api/auth/register` | Public | Register new TRADER account | `201` (400 validation, 409 duplicate) |
| `POST` | `/api/auth/login` | Public | Login with email & password | `200` (401 invalid credentials) |
| `POST` | `/api/strategies` | `TRADER`, `ADMIN` | Create strategy config | `201` |
| `GET` | `/api/strategies` | `TRADER`, `ADMIN` | List user's strategies | `200` |
| `GET` | `/api/instruments` | `TRADER`, `ADMIN` | List instruments with coverage data | `200` |
| `POST` | `/api/instruments` | `ADMIN` | Create new instrument | `201` (409 duplicate ticker) |
| `PUT` | `/api/instruments/{id}` | `ADMIN` | Update instrument | `200` (404 not found) |
| `DELETE`| `/api/instruments/{id}` | `ADMIN` | Remove instrument | `204` (409 if in use) |
| `POST` | `/api/instruments/{id}/prices` | `ADMIN` | Upload CSV prices (multipart) | `200` |
| `POST` | `/api/backtests` | `TRADER`, `ADMIN` | Run strategy backtest | `201` (400 bad dates, 422 insufficient data) |
| `GET` | `/api/backtests` | `TRADER`, `ADMIN` | List user's backtest runs (newest first) | `200` |
| `GET` | `/api/backtests/compare` | `TRADER`, `ADMIN` | Compare 2 runs (`?runA=&runB=`) | `200` (400 if same run) |
| `GET` | `/api/backtests/{id}` | `TRADER`, `ADMIN` | Get run details, metrics, curve | `200` (404 if not owned) |
| `GET` | `/health` | Public | Health probe | `200` |

---

## 6. Directory Ownership & Modules

| Module / Directory | Owner | Role |
|---|---|---|
| `frontend/**` | Shourya | UI & Dashboard |
| `backend/app/models/`, `repositories/` | Rishabh | Persistence layer & ORM |
| `backend/app/services/instrument_service.py` | Rishabh | Instruments & CSV upload |
| `backend/app/core/database.py`, `alembic/`, `scripts/` | Rishabh | DB engine, migrations & scripts |
| `backend/app/strategies/` | Shaurya | Strategy implementations |
| `backend/app/services/strategy_service.py`, `backtest_engine.py`, `equity.py` | Shaurya | Backtest engine & signals |
| `backend/app/api/` | Molik | REST API endpoints & routing |
| `backend/app/main.py`, `core/security.py`, `core/errors.py` | Molik | App setup, JWT, error envelope |
| `backend/app/services/auth_service.py`, `metrics_calculator.py`, `results_service.py` | Molik | Authentication, Metrics engine, Results |
| `backend/app/domain.py` | Shared | Shared domain entities & exceptions |
