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
Set `DATABASE_URL` in `.env` to a PostgreSQL direct/session URL for Alembic.
Do not use Supabase's transaction pooler for migrations. Alembic converts async
PostgreSQL URLs to the synchronous `psycopg` driver. The schema migrations use
PostgreSQL features including pgvector and Supabase Auth, so SQLite is not a
supported migration target.

The FastAPI app must use a separate least-privilege database login configured
in `APP_DATABASE_URL`. Do not use the `postgres` login or the Supabase
service-role key for the application connection.

## Database migrations

Run these commands from `backend/`. The reviewed `rls_scoped_access` revision
adds row-level security to the schema created by `db54c4a90d60`.

```powershell
# Check which revision the database has applied.
uv run alembic current

# Apply the pending RLS revision after reviewing it.
uv run alembic upgrade head

# Confirm the database is at the latest revision.
uv run alembic current
```

For future model changes, generate a candidate revision with
`uv run alembic revision --autogenerate -m "describe schema changes"`, then
review and adjust it before applying. Autogenerate does not understand intent
such as renames, data-preserving conversions, or Supabase RLS policies.

Do not edit an already-applied revision. If the database has schema objects but
no Alembic revision history, inspect and reconcile its schema with the existing
migrations before upgrading; do not blindly stamp it or run the initial revision.

### Protecting application data

The browser sends its Supabase access token to FastAPI; it does not connect to
the database with a privileged key. FastAPI validates the token with Supabase
Auth. For each database transaction, the backend switches to the
`document_copilot_app` role and sets the validated user's ID. PostgreSQL RLS
then limits chat data to that user. Filing documents are read-only to this app
role. The RLS migration removes table privileges from Supabase's `anon` and
`authenticated` API roles, so clients must use FastAPI for database access.

After reviewing and applying the RLS migration, create a separate database
login in the Supabase SQL editor:

```sql
CREATE ROLE document_copilot_login
    LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS
    PASSWORD '<generate-a-unique-strong-password>';
GRANT document_copilot_app TO document_copilot_login;
```

Set `APP_DATABASE_URL` in the backend's private environment to use this login.
URL-encode special characters in the password. Keep the privileged direct
connection only in `DATABASE_URL` for Alembic; never put either database URL or
the service-role key in frontend configuration. The current API has no chat
routes yet. Future database routes must depend on `get_current_user_id` and
call `get_session(user_id)` so every query uses the verified identity and
RLS-scoped database role.

Set the intended `APP_DATABASE_URL` value in `.env` before running Alembic; the
migration command loads the same settings file, but does not connect using this
application URL. The login itself only needs to exist before starting FastAPI.

Run tests and lint with `uv run pytest` and `uv run ruff check .`.
