"""Restrict application database access with user-scoped RLS.

Revision ID: rls_scoped_access
Revises: db54c4a90d60
"""

from collections.abc import Sequence

from alembic import op

revision: str = "rls_scoped_access"
down_revision: str | None = "db54c4a90d60"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = (
    "users",
    "chat_threads",
    "chat_messages",
    "message_citations",
    "source_documents",
    "document_chunks",
    "document_tables",
)


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_roles WHERE rolname = 'document_copilot_app'
            ) THEN
                EXECUTE
                    'CREATE ROLE document_copilot_app NOLOGIN NOSUPERUSER '
                    || 'NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS';
            ELSE
                EXECUTE
                    'ALTER ROLE document_copilot_app NOLOGIN NOSUPERUSER '
                    || 'NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS';
            END IF;
        END
        $$;
        """
    )
    op.execute("GRANT USAGE ON SCHEMA public, auth TO document_copilot_app")
    op.execute("GRANT EXECUTE ON FUNCTION auth.uid() TO document_copilot_app")

    for table in _TABLES:
        op.execute(
            f"REVOKE ALL ON TABLE public.{table} FROM PUBLIC, anon, authenticated"
        )
        op.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE public.{table} FORCE ROW LEVEL SECURITY")

    op.execute(
        """
        CREATE POLICY users_read_self ON public.users
        FOR SELECT TO document_copilot_app
        USING (id = (SELECT auth.uid()))
        """
    )
    op.execute(
        """
        CREATE POLICY users_create_self ON public.users
        FOR INSERT TO document_copilot_app
        WITH CHECK (id = (SELECT auth.uid()))
        """
    )
    op.execute(
        """
        CREATE POLICY users_update_self ON public.users
        FOR UPDATE TO document_copilot_app
        USING (id = (SELECT auth.uid()))
        WITH CHECK (id = (SELECT auth.uid()))
        """
    )
    op.execute(
        """
        CREATE POLICY chat_threads_owner ON public.chat_threads
        FOR ALL TO document_copilot_app
        USING (user_id = (SELECT auth.uid()))
        WITH CHECK (user_id = (SELECT auth.uid()))
        """
    )
    op.execute(
        """
        CREATE POLICY chat_messages_owner ON public.chat_messages
        FOR ALL TO document_copilot_app
        USING (
            EXISTS (
                SELECT 1 FROM public.chat_threads
                WHERE chat_threads.id = chat_messages.thread_id
                  AND chat_threads.user_id = (SELECT auth.uid())
            )
        )
        WITH CHECK (
            EXISTS (
                SELECT 1 FROM public.chat_threads
                WHERE chat_threads.id = chat_messages.thread_id
                  AND chat_threads.user_id = (SELECT auth.uid())
            )
        )
        """
    )
    op.execute(
        """
        CREATE POLICY message_citations_owner ON public.message_citations
        FOR ALL TO document_copilot_app
        USING (
            EXISTS (
                SELECT 1
                FROM public.chat_messages
                JOIN public.chat_threads
                  ON chat_threads.id = chat_messages.thread_id
                WHERE chat_messages.id = message_citations.message_id
                  AND chat_threads.user_id = (SELECT auth.uid())
            )
        )
        WITH CHECK (
            EXISTS (
                SELECT 1
                FROM public.chat_messages
                JOIN public.chat_threads
                  ON chat_threads.id = chat_messages.thread_id
                WHERE chat_messages.id = message_citations.message_id
                  AND chat_threads.user_id = (SELECT auth.uid())
            )
        )
        """
    )

    for table in ("source_documents", "document_chunks", "document_tables"):
        op.execute(
            f"""
            CREATE POLICY {table}_read ON public.{table}
            FOR SELECT TO document_copilot_app
            USING (true)
            """
        )

    op.execute(
        "GRANT SELECT, INSERT, UPDATE ON public.users TO document_copilot_app"
    )
    op.execute(
        """
        GRANT SELECT, INSERT, UPDATE, DELETE
        ON public.chat_threads, public.chat_messages, public.message_citations
        TO document_copilot_app
        """
    )
    op.execute(
        """
        GRANT SELECT
        ON public.source_documents, public.document_chunks, public.document_tables
        TO document_copilot_app
        """
    )


def downgrade() -> None:
    for table in ("source_documents", "document_chunks", "document_tables"):
        op.execute(f"DROP POLICY {table}_read ON public.{table}")

    for table, policy in (
        ("message_citations", "message_citations_owner"),
        ("chat_messages", "chat_messages_owner"),
        ("chat_threads", "chat_threads_owner"),
        ("users", "users_update_self"),
        ("users", "users_create_self"),
        ("users", "users_read_self"),
    ):
        op.execute(f"DROP POLICY {policy} ON public.{table}")

    for table in _TABLES:
        op.execute(f"ALTER TABLE public.{table} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE public.{table} DISABLE ROW LEVEL SECURITY")

    op.execute(
        """
        DO $$
        DECLARE
            role_member record;
        BEGIN
            FOR role_member IN
                SELECT member_role.rolname
                FROM pg_auth_members AS membership
                JOIN pg_roles AS member_role
                  ON member_role.oid = membership.member
                WHERE membership.roleid = (
                    SELECT oid FROM pg_roles
                    WHERE rolname = 'document_copilot_app'
                )
            LOOP
                EXECUTE format(
                    'REVOKE document_copilot_app FROM %I',
                    role_member.rolname
                );
            END LOOP;
        END
        $$;
        """
    )
    op.execute("DROP ROLE document_copilot_app")
