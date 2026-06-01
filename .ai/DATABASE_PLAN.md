# Database Design Plan

# Database Technology

Database:

* PostgreSQL

ORM:

* SQLAlchemy

Migration Tool:

* Alembic

---

# Database Design Principles

* Use normalized schema
* Use UUIDs where appropriate
* Add indexes for performance
* Maintain foreign key integrity
* Support audit logging
* Support future scaling

---

# Core Tables

# Users Table

## Purpose

Stores user authentication and profile information.

## Fields

| Field         | Type      |
| ------------- | --------- |
| id            | UUID      |
| name          | VARCHAR   |
| email         | VARCHAR   |
| password_hash | TEXT      |
| role_id       | UUID      |
| created_at    | TIMESTAMP |

## Indexes

* email unique index

---

# Roles Table

## Purpose

Stores RBAC role definitions.

## Fields

| Field       | Type    |
| ----------- | ------- |
| id          | UUID    |
| name        | VARCHAR |
| permissions | JSONB   |

---

# Sessions Table

## Purpose

Stores refresh token sessions.

## Fields

| Field         | Type      |
| ------------- | --------- |
| id            | UUID      |
| user_id       | UUID      |
| refresh_token | TEXT      |
| expires_at    | TIMESTAMP |

---

# Workflows Table

## Purpose

Stores workflow definitions.

## Fields

| Field        | Type      |
| ------------ | --------- |
| id           | UUID      |
| name         | VARCHAR   |
| description  | TEXT      |
| trigger_type | VARCHAR   |
| status       | VARCHAR   |
| created_by   | UUID      |
| created_at   | TIMESTAMP |

---

# Workflow Steps Table

## Purpose

Stores workflow step definitions.

## Fields

| Field         | Type    |
| ------------- | ------- |
| id            | UUID    |
| workflow_id   | UUID    |
| step_order    | INTEGER |
| step_type     | VARCHAR |
| configuration | JSONB   |

---

# Executions Table

## Purpose

Stores workflow execution records.

## Fields

| Field        | Type      |
| ------------ | --------- |
| id           | UUID      |
| workflow_id  | UUID      |
| status       | VARCHAR   |
| started_at   | TIMESTAMP |
| completed_at | TIMESTAMP |

---

# Execution Logs Table

## Purpose

Stores detailed workflow execution logs.

## Fields

| Field        | Type      |
| ------------ | --------- |
| id           | UUID      |
| execution_id | UUID      |
| log_level    | VARCHAR   |
| message      | TEXT      |
| created_at   | TIMESTAMP |

---

# AI Logs Table

## Purpose

Stores AI interaction records.

## Fields

| Field             | Type    |
| ----------------- | ------- |
| id                | UUID    |
| provider          | VARCHAR |
| model             | VARCHAR |
| prompt_tokens     | INTEGER |
| completion_tokens | INTEGER |
| total_tokens      | INTEGER |
| response_time_ms  | INTEGER |

---

# Webhook Logs Table

## Purpose

Stores incoming webhook events.

## Fields

| Field       | Type    |
| ----------- | ------- |
| id          | UUID    |
| workflow_id | UUID    |
| payload     | JSONB   |
| headers     | JSONB   |
| status      | VARCHAR |

---

# Notifications Table

## Purpose

Stores notification history.

## Fields

| Field     | Type      |
| --------- | --------- |
| id        | UUID      |
| channel   | VARCHAR   |
| recipient | VARCHAR   |
| status    | VARCHAR   |
| sent_at   | TIMESTAMP |

---

# Audit Logs Table

## Purpose

Stores system audit history.

## Fields

| Field       | Type      |
| ----------- | --------- |
| id          | UUID      |
| user_id     | UUID      |
| action      | VARCHAR   |
| entity_type | VARCHAR   |
| entity_id   | UUID      |
| created_at  | TIMESTAMP |

---

# Relationships

## User Relationships

* users → roles
* users → workflows

## Workflow Relationships

* workflows → workflow_steps
* workflows → executions

## Execution Relationships

* executions → execution_logs

---

# Database Optimization

## Indexing Strategy

* index foreign keys
* index status fields
* index created_at timestamps
* add composite indexes for analytics

## Performance Strategy

* pagination
* query optimization
* selective indexing
* partition large log tables

---

# Future Database Enhancements

Future upgrades:

* read replicas
* partitioning
* Redis caching
* analytics warehouse
* event sourcing

---

# Migration Standards

Migration Rules:

* use versioned migrations
* never edit old migrations
* keep migrations reversible
* test migrations before deployment

---

# Backup Strategy

* daily backups
* WAL archiving
* restore testing
* disaster recovery plan
