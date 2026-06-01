# Project Folder Structure

# Root Structure

```text
ai-workflow-platform/
├── .ai/
├── backend/
├── frontend/
├── workflows/
├── docker/
├── nginx/
├── docs/
├── scripts/
├── .env
├── docker-compose.yml
└── README.md
```

---

# AI Memory System

```text
.ai/
├── PROJECT_CONTEXT.md
├── RULES.md
├── TASKS.md
├── ARCHITECTURE.md
├── API_SPEC.md
├── DATABASE_PLAN.md
├── FOLDER_STRUCTURE.md
├── DOCKER_PLAN.md
├── WORKFLOW_ENGINE.md
├── AI_INTEGRATION.md
└── DECISIONS.md
```

Purpose:

* persistent AI memory
* architecture consistency
* development roadmap
* coding standards

---

# Backend Structure

```text
backend/
├── app/
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── repositories/
│   ├── workflows/
│   ├── integrations/
│   ├── middleware/
│   ├── utils/
│   ├── database/
│   └── main.py
│
├── tests/
├── alembic/
├── requirements.txt
└── Dockerfile
```

---

# Backend Layer Responsibilities

## api/

Stores:

* route definitions
* endpoint handlers
* API versions

---

## core/

Stores:

* application config
* environment management
* security configuration
* constants

---

## models/

Stores:

* SQLAlchemy database models

---

## schemas/

Stores:

* Pydantic request/response schemas

---

## services/

Stores:

* business logic
* AI orchestration
* workflow execution logic

---

## repositories/

Stores:

* database access layer
* query logic

---

## workflows/

Stores:

* workflow engine
* execution logic
* retry system

---

## integrations/

Stores:

* OpenAI integration
* Claude integration
* Slack integration
* email integration
* n8n integration

---

## middleware/

Stores:

* JWT middleware
* logging middleware
* rate limiting middleware

---

# Frontend Structure

```text
frontend/
├── app/
├── components/
├── services/
├── hooks/
├── store/
├── lib/
├── styles/
├── types/
├── public/
└── Dockerfile
```

---

# Frontend Responsibilities

## app/

Next.js routing system

## components/

Reusable UI components

## services/

API communication layer

## hooks/

Reusable frontend logic

## store/

Global state management

---

# Workflow Directory

```text
workflows/
├── email-automation/
├── approval-workflows/
├── ai-processing/
├── notifications/
└── templates/
```

Purpose:

* store n8n exports
* workflow templates
* reusable automations

---

# Docker Directory

```text
docker/
├── backend/
├── frontend/
├── postgres/
├── nginx/
└── n8n/
```

Purpose:

* container configuration
* infrastructure setup

---

# Documentation Structure

```text
docs/
├── architecture/
├── api/
├── deployment/
├── workflows/
└── database/
```

---

# Folder Structure Rules

* Keep modules isolated
* Avoid deeply nested structures
* Separate business logic properly
* Maintain reusable services
* Keep integrations modular
* Keep workflows independent
