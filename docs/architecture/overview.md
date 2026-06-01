# Architecture Overview

The platform is split into a Next.js dashboard, a FastAPI backend, PostgreSQL persistence, n8n automation, and Nginx routing.

```text
User -> Nginx -> Frontend -> Backend API -> Workflow Engine -> AI Providers
                                      -> PostgreSQL
                                      -> n8n
```

The backend follows a layered pattern:

```text
API route -> service -> repository -> database model
```

AI integrations are isolated behind provider adapters so OpenAI, Claude, and local fallback behavior can share a common response contract.

