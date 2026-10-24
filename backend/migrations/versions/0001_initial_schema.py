"""Create the initial Document Copilot schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-10-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("display_name", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["id"], ["auth.users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute(
        """
        INSERT INTO public.profiles (id, email)
        SELECT id, email FROM auth.users
        ON CONFLICT (id) DO NOTHING
        """
    )
    op.execute(
        """
        CREATE FUNCTION public.handle_new_auth_user()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = ''
        AS $$
        BEGIN
            INSERT INTO public.profiles (id, email)
            VALUES (NEW.id, NEW.email)
            ON CONFLICT (id) DO UPDATE SET email = EXCLUDED.email;
            RETURN NEW;
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER on_auth_user_created
        AFTER INSERT OR UPDATE OF email ON auth.users
        FOR EACH ROW EXECUTE FUNCTION public.handle_new_auth_user()
        """
    )

    op.create_table(
        "source_documents",
        sa.Column(
            "id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("ticker", sa.String(length=10), nullable=False),
        sa.Column("cik", sa.String(length=10), nullable=False),
        sa.Column("form", sa.String(length=20), nullable=False),
        sa.Column("accession_number", sa.String(length=25), nullable=False),
        sa.Column("filing_date", sa.Date(), nullable=False),
        sa.Column("report_date", sa.Date(), nullable=True),
        sa.Column("fiscal_year", sa.Integer(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("primary_document", sa.Text(), nullable=True),
        sa.Column("content_markdown", sa.Text(), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("accession_number", name="uq_source_documents_accession"),
    )

    op.create_table(
        "document_chunks",
        sa.Column(
            "id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("source_document_id", sa.Uuid(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("section", sa.Text(), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed(
                "to_tsvector('english'::regconfig, chunk_text)", persisted=True
            ),
            nullable=False,
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["source_document_id"], ["source_documents.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_document_id",
            "chunk_index",
            name="uq_document_chunks_document_index",
        ),
    )
    op.create_index(
        "ix_document_chunks_embedding_hnsw",
        "document_chunks",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
    op.create_index(
        "ix_document_chunks_search_vector_gin",
        "document_chunks",
        ["search_vector"],
        postgresql_using="gin",
    )
    op.create_index(
        "ix_document_chunks_metadata_gin",
        "document_chunks",
        ["metadata"],
        postgresql_using="gin",
        postgresql_ops={"metadata": "jsonb_path_ops"},
    )

    op.create_table(
        "chat_threads",
        sa.Column(
            "id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "chat_messages",
        sa.Column(
            "id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("thread_id", sa.Uuid(), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "message_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "usage_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "role IN ('user', 'assistant')", name="ck_chat_messages_role"
        ),
        sa.ForeignKeyConstraint(["thread_id"], ["chat_threads.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "thread_id", "sequence_number", name="uq_chat_messages_thread_sequence"
        ),
    )

    op.create_table(
        "message_citations",
        sa.Column(
            "id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("message_id", sa.Uuid(), nullable=False),
        sa.Column("document_chunk_id", sa.Uuid(), nullable=True),
        sa.Column("citation_index", sa.Integer(), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["document_chunk_id"], ["document_chunks.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["message_id"], ["chat_messages.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "message_id", "citation_index", name="uq_message_citations_message_index"
        ),
    )

    for table in (
        "profiles",
        "source_documents",
        "document_chunks",
        "chat_threads",
        "chat_messages",
        "message_citations",
    ):
        op.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY")

    op.execute(
        """
        CREATE POLICY profiles_select_own ON public.profiles
        FOR SELECT TO authenticated USING (id = (SELECT auth.uid()))
        """
    )
    op.execute(
        """
        CREATE POLICY profiles_insert_own ON public.profiles
        FOR INSERT TO authenticated WITH CHECK (id = (SELECT auth.uid()))
        """
    )
    op.execute(
        """
        CREATE POLICY profiles_update_own ON public.profiles
        FOR UPDATE TO authenticated
        USING (id = (SELECT auth.uid()))
        WITH CHECK (id = (SELECT auth.uid()))
        """
    )
    op.execute(
        """
        CREATE POLICY chat_threads_select_own ON public.chat_threads
        FOR SELECT TO authenticated USING (user_id = (SELECT auth.uid()))
        """
    )
    op.execute(
        """
        CREATE POLICY chat_threads_insert_own ON public.chat_threads
        FOR INSERT TO authenticated WITH CHECK (user_id = (SELECT auth.uid()))
        """
    )
    op.execute(
        """
        CREATE POLICY chat_threads_update_own ON public.chat_threads
        FOR UPDATE TO authenticated
        USING (user_id = (SELECT auth.uid()))
        WITH CHECK (user_id = (SELECT auth.uid()))
        """
    )
    op.execute(
        """
        CREATE POLICY chat_threads_delete_own ON public.chat_threads
        FOR DELETE TO authenticated USING (user_id = (SELECT auth.uid()))
        """
    )
    op.execute(
        """
        CREATE POLICY chat_messages_select_own ON public.chat_messages
        FOR SELECT TO authenticated
        USING (
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
        CREATE POLICY chat_messages_insert_own ON public.chat_messages
        FOR INSERT TO authenticated
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
        CREATE POLICY chat_messages_update_own ON public.chat_messages
        FOR UPDATE TO authenticated
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
        CREATE POLICY chat_messages_delete_own ON public.chat_messages
        FOR DELETE TO authenticated
        USING (
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
        CREATE POLICY message_citations_select_own ON public.message_citations
        FOR SELECT TO authenticated
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
        """
    )

    op.execute("GRANT SELECT, INSERT, UPDATE ON public.profiles TO authenticated")
    op.execute(
        """
        GRANT SELECT, INSERT, UPDATE, DELETE
        ON public.chat_threads, public.chat_messages TO authenticated
        """
    )
    op.execute("GRANT SELECT ON public.message_citations TO authenticated")
    op.execute(
        """
        GRANT SELECT, INSERT, UPDATE, DELETE
        ON public.source_documents, public.document_chunks, public.message_citations
        TO service_role
        """
    )
    op.execute(
        "REVOKE ALL ON FUNCTION public.handle_new_auth_user() "
        "FROM PUBLIC, anon, authenticated"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users")
    op.execute("DROP FUNCTION IF EXISTS public.handle_new_auth_user()")
    op.drop_table("message_citations")
    op.drop_table("chat_messages")
    op.drop_table("chat_threads")
    op.drop_table("document_chunks")
    op.drop_table("source_documents")
    op.drop_table("profiles")
