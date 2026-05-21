"""initial schema

Revision ID: 0001_init
Revises:
Create Date: 2026-05-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "0001_init"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "issues",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("external_id", sa.Integer(), nullable=False),
        sa.Column("repo", sa.String(length=255), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("labels", sa.JSON(), nullable=False),
        sa.Column("mapped_label", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
    )
    op.create_index("ix_issues_repo", "issues", ["repo"])
    op.create_index("ix_issues_number", "issues", ["number"])
    op.create_index("ix_issues_mapped_label", "issues", ["mapped_label"])
    op.create_index("ix_issues_created_at", "issues", ["created_at"])

    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("repo", sa.String(length=255), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("doc_metadata", sa.JSON(), nullable=False),
        sa.Column("embedding", Vector(384), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_documents_source_type", "documents", ["source_type"])
    op.create_index("ix_documents_repo", "documents", ["repo"])

    op.create_table(
        "memories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("memory_type", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(384), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_memories_memory_type", "memories", ["memory_type"])

    op.create_table(
        "widgets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("widget_id", sa.String(length=64), nullable=False),
        sa.Column("allowed_origins", sa.JSON(), nullable=False),
        sa.Column("theme", sa.JSON(), nullable=False),
        sa.Column("greeting", sa.Text(), nullable=False),
        sa.Column("enabled_tools", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_widgets_widget_id", "widgets", ["widget_id"], unique=True)

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("target", sa.String(length=255), nullable=False),
        sa.Column("audit_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_target", "audit_logs", ["target"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("widgets")
    op.drop_table("memories")
    op.drop_table("documents")
    op.drop_table("issues")
    op.drop_table("users")
    op.execute("DROP EXTENSION IF EXISTS vector")