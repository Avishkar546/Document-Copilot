# Backend

FastAPI service using SQLAlchemy 2 and Alembic. Python 3.12 or newer is required.

```powershell
cd backend
uv venv
.\.venv\Scripts\Activate.ps1
uv sync --extra dev
Copy-Item .env.example .env
uv run uvicorn app.main:app --reload
```

The API documentation is available at `/docs`. Liveness and database readiness
checks are available at `/api/v1/health/live` and `/api/v1/health/ready`.
Set `DATABASE_URL` in `.env` to a PostgreSQL direct/session connection URL
(for example, `postgresql+asyncpg://...`). Do not use Supabase's transaction
pooler for migrations. Alembic converts async PostgreSQL driver URLs to the
synchronous `psycopg` driver. The schema migrations use PostgreSQL features
including pgvector and Supabase Auth, so SQLite is not a supported migration
target.

## Database migrations

Run these commands from `backend/`. Autogenerate creates a candidate revision;
it does not apply it. Review and adjust the file in `migrations/versions/`
before applying it, especially for renames, data-preserving type changes,
PostgreSQL-specific objects, and Supabase RLS policies.

```powershell
# Check which revision the database has applied.
uv run alembic current

# Generate a candidate revision from the SQLAlchemy models.
uv run alembic revision --autogenerate -m "describe schema changes"

# Review and edit the generated migration before applying it.
# Apply only after the migration has been verified and approved.
uv run alembic upgrade head

# Confirm the database is at the latest revision.
uv run alembic current
```

Do not edit an already-applied revision. If the database has schema objects but
no Alembic revision history, inspect and reconcile its schema with the existing
migrations before upgrading; do not blindly stamp it or run the initial revision.

Run tests and lint with `uv run pytest` and `uv run ruff check .`.
