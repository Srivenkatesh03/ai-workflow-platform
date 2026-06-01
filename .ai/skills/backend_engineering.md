# Backend Engineering Skill

# Architecture Rules

Use:

* layered architecture
* service layer
* repository pattern
* dependency injection

Flow:
API → Service → Repository → Database

---

# FastAPI Standards

Requirements:

* async endpoints
* type hints
* modular routes
* versioned APIs
* Pydantic validation

---

# Service Rules

Services:

* contain business logic
* remain reusable
* never contain route logic

---

# Repository Rules

Repositories:

* isolate database queries
* support pagination
* support filtering

---

# Security Rules

Requirements:

* JWT validation
* RBAC checks
* input sanitization

---

# Logging Rules

Track:

* request ID
* execution time
* workflow execution
* AI requests
* failures

---

# Database Rules

Use:

* SQLAlchemy
* Alembic migrations
* indexed foreign keys
* UUID identifiers

---

# Code Quality Rules

Requirements:

* modular code
* reusable services
* meaningful naming
* production-grade structure
