# AI Code Generation Rules

# Purpose

These rules ensure:

* consistent code quality
* scalable architecture
* maintainable codebase
* deterministic AI-generated outputs

---

# General Rules

* Generate only requested files
* Never rewrite unrelated modules
* Avoid duplicated logic
* Reuse existing services
* Follow existing architecture

---

# Architecture Rules

Use:

* layered architecture
* modular services
* repository pattern
* dependency injection

Flow:
API → Service → Repository → Database

---

# Backend Code Rules

## Required Standards

* use async where appropriate
* use type hints
* validate all inputs
* separate business logic properly

---

# API Rules

Requirements:

* RESTful APIs
* versioned routes
* standardized responses
* proper HTTP status codes

---

# Service Layer Rules

Services must:

* contain business logic
* remain reusable
* avoid direct route logic

Services must not:

* access request objects directly
* contain frontend logic

---

# Repository Rules

Repositories must:

* isolate database logic
* support filtering
* support pagination

Repositories must not:

* contain business logic

---

# Frontend Rules

Requirements:

* reusable components
* isolated UI logic
* responsive design
* centralized API handling

---

# Database Rules

Requirements:

* migrations only
* indexed foreign keys
* normalized schema

Never:

* hardcode SQL in services

---

# Docker Rules

Requirements:

* lightweight containers
* multi-stage builds
* environment variable usage

---

# Logging Rules

All major operations must log:

* execution ID
* request ID
* errors
* duration
* retries

---

# Security Rules

Requirements:

* JWT validation
* input sanitization
* RBAC checks
* secure secret handling

---

# AI Integration Rules

Requirements:

* provider abstraction
* retry handling
* token tracking
* prompt templates

---

# Naming Conventions

## Backend

* snake_case for files
* PascalCase for classes

## Frontend

* PascalCase for components
* camelCase for functions

---

# File Generation Rules

Never:

* generate placeholder code
* generate mock production credentials
* generate unnecessary comments

Always:

* generate production-style structure
* use meaningful names
* follow modular architecture

---

# Future Enhancements

Future additions:

* automated architecture validation
* AI-assisted refactoring
* code quality scoring
