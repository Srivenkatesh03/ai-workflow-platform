# Engineering Rules

## General Rules

* Never generate unnecessary files
* Never rewrite unrelated code
* Keep architecture modular
* Use reusable services
* Keep responses concise
* Prefer maintainable code over shortcuts

---

# Backend Rules

## Architecture

* Use layered architecture
* Use service layer
* Use repository pattern
* Separate routes, services, repositories, schemas, and models

## API Design

* Use RESTful APIs
* Use versioned APIs
* Validate all inputs
* Return structured responses

## Security

* Use JWT authentication
* Hash passwords using bcrypt
* Never hardcode secrets
* Use environment variables

## Logging

* Log workflow executions
* Log AI requests
* Log failures and retries
* Log authentication events

---

# Frontend Rules

* Use reusable components
* Keep components modular
* Use proper state management
* Avoid deeply nested components
* Use Tailwind utility classes properly

---

# Database Rules

* Use UUIDs where appropriate
* Add indexes for searchable fields
* Use foreign keys correctly
* Avoid duplicated data
* Use migration files

---

# Docker Rules

* Use lightweight images
* Separate services properly
* Use .env files
* Avoid hardcoded ports

---

# Git Rules

## Commit Format

feat: add workflow execution service
fix: resolve webhook retry bug
docs: update architecture docs

---

# AI Rules

* Use prompt templates
* Handle API failures gracefully
* Track token usage
* Log AI responses
* Use retry mechanisms

---

# Scalability Rules

* Design for horizontal scaling
* Keep services stateless where possible
* Use queues for heavy processing
* Use async processing when needed

---

# Documentation Rules

* Update docs after major changes
* Keep architecture docs accurate
* Document APIs properly
* Keep setup instructions updated
