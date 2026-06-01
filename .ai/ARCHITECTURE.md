# System Architecture

# High-Level Architecture

Client → Frontend → Backend API → Workflow Engine → AI Services → Database

Additional systems:

* n8n orchestration
* notification services
* webhook handlers
* logging services

---

# Frontend Layer

Technology:

* Next.js
* Tailwind CSS
* ShadCN UI

Responsibilities:

* Authentication UI
* Dashboard
* Workflow management
* Logs visualization
* Real-time updates

---

# Backend Layer

Technology:

* FastAPI

Responsibilities:

* API gateway
* Authentication
* Workflow execution
* AI orchestration
* Database communication
* Logging

---

# Workflow Engine

Responsibilities:

* Execute workflows
* Trigger automations
* Retry failed tasks
* Manage workflow states

Workflow states:

* pending
* running
* completed
* failed
* retrying

---

# AI Layer

Providers:

* OpenAI
* Claude

Responsibilities:

* text summarization
* document analysis
* classification
* response generation

---

# Database Layer

Technology:

* PostgreSQL

Core tables:

* users
* workflows
* workflow_steps
* executions
* execution_logs
* ai_logs
* notifications

---

# Notification Layer

Channels:

* Email
* Slack
* Discord

Responsibilities:

* status updates
* approval requests
* alerts
* execution notifications

---

# DevOps Layer

Technology:

* Docker
* Docker Compose
* Nginx
* GitHub Actions

Responsibilities:

* deployment
* scaling
* reverse proxy
* CI/CD
* monitoring

---

# Future Scalability

Future enhancements:

* Redis queues
* Celery workers
* Kubernetes
* multi-region deployment
* OpenTelemetry
* distributed tracing
