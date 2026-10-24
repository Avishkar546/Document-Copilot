# Backend

FastAPI service using SQLAlchemy 2 and Alembic. Python 3.12 or newer is required.

```powershell
cd backend
uv venv
.\.venv\Scripts\Activate.ps1
uv sync --extra dev
Copy-Item .env.example .env
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

The API documentation is available at `/docs`. Liveness and database readiness
checks are available at `/api/v1/health/live` and `/api/v1/health/ready`.
Set `DATABASE_URL` in `.env` to a `postgresql+asyncpg://` URL for deployment;
the default `sqlite+aiosqlite` URL is for local development. Alembic converts
these async driver URLs to their synchronous migration equivalents.

Run tests and lint with `uv run pytest` and `uv run ruff check .`.
