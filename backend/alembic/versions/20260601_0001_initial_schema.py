"""initial schema

Revision ID: 20260601_0001
Revises:
Create Date: 2026-06-01 00:01:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260601_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("permissions", sa.JSON(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_roles_name"), "roles", ["name"], unique=True)

    op.create_table(
        "ai_logs",
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False),
        sa.Column("completion_tokens", sa.Integer(), nullable=False),
        sa.Column("total_tokens", sa.Integer(), nullable=False),
        sa.Column("response_time_ms", sa.Integer(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ai_logs_provider"), "ai_logs", ["provider"], unique=False)

    op.create_table(
        "notifications",
        sa.Column("channel", sa.String(length=50), nullable=False),
        sa.Column("recipient", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_notifications_channel"), "notifications", ["channel"], unique=False)
    op.create_index(op.f("ix_notifications_status"), "notifications", ["status"], unique=False)

    op.create_table(
        "users",
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role_id", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "audit_logs",
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_audit_logs_entity_id"), "audit_logs", ["entity_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_entity_type"), "audit_logs", ["entity_type"], unique=False)
    op.create_index(op.f("ix_audit_logs_user_id"), "audit_logs", ["user_id"], unique=False)

    op.create_table(
        "sessions",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("refresh_token", sa.String(length=500), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sessions_refresh_token"), "sessions", ["refresh_token"], unique=True)
    op.create_index(op.f("ix_sessions_user_id"), "sessions", ["user_id"], unique=False)

    op.create_table(
        "workflows",
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("trigger_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_workflows_name"), "workflows", ["name"], unique=False)
    op.create_index(op.f("ix_workflows_status"), "workflows", ["status"], unique=False)
    op.create_index(op.f("ix_workflows_trigger_type"), "workflows", ["trigger_type"], unique=False)

    op.create_table(
        "executions",
        sa.Column("workflow_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflows.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_executions_status"), "executions", ["status"], unique=False)
    op.create_index(op.f("ix_executions_workflow_id"), "executions", ["workflow_id"], unique=False)

    op.create_table(
        "webhook_logs",
        sa.Column("workflow_id", sa.Uuid(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("headers", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflows.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_webhook_logs_status"), "webhook_logs", ["status"], unique=False)
    op.create_index(op.f("ix_webhook_logs_workflow_id"), "webhook_logs", ["workflow_id"], unique=False)

    op.create_table(
        "workflow_steps",
        sa.Column("workflow_id", sa.Uuid(), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("step_type", sa.String(length=50), nullable=False),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflows.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_workflow_steps_workflow_id"), "workflow_steps", ["workflow_id"], unique=False)

    op.create_table(
        "execution_logs",
        sa.Column("execution_id", sa.Uuid(), nullable=False),
        sa.Column("log_level", sa.String(length=20), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["execution_id"], ["executions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_execution_logs_execution_id"), "execution_logs", ["execution_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_execution_logs_execution_id"), table_name="execution_logs")
    op.drop_table("execution_logs")
    op.drop_index(op.f("ix_workflow_steps_workflow_id"), table_name="workflow_steps")
    op.drop_table("workflow_steps")
    op.drop_index(op.f("ix_webhook_logs_workflow_id"), table_name="webhook_logs")
    op.drop_index(op.f("ix_webhook_logs_status"), table_name="webhook_logs")
    op.drop_table("webhook_logs")
    op.drop_index(op.f("ix_executions_workflow_id"), table_name="executions")
    op.drop_index(op.f("ix_executions_status"), table_name="executions")
    op.drop_table("executions")
    op.drop_index(op.f("ix_workflows_trigger_type"), table_name="workflows")
    op.drop_index(op.f("ix_workflows_status"), table_name="workflows")
    op.drop_index(op.f("ix_workflows_name"), table_name="workflows")
    op.drop_table("workflows")
    op.drop_index(op.f("ix_sessions_user_id"), table_name="sessions")
    op.drop_index(op.f("ix_sessions_refresh_token"), table_name="sessions")
    op.drop_table("sessions")
    op.drop_index(op.f("ix_audit_logs_user_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_entity_type"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_entity_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_action"), table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_notifications_status"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_channel"), table_name="notifications")
    op.drop_table("notifications")
    op.drop_index(op.f("ix_ai_logs_provider"), table_name="ai_logs")
    op.drop_table("ai_logs")
    op.drop_index(op.f("ix_roles_name"), table_name="roles")
    op.drop_table("roles")
