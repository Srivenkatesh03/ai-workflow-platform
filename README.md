# AI Workflow Automation Platform

Production-style AI workflow automation platform with a FastAPI backend, Next.js dashboard, PostgreSQL, n8n, and Docker-based local deployment.

## Current Status

This scaffold includes:

- FastAPI app structure with versioned APIs
- SQLAlchemy models for users, workflows, executions, logs, AI logs, webhooks, notifications, and audit logs
- Service/repository workflow execution pattern
- AI provider abstraction with local fallback behavior
- Next.js dashboard shell with workflow and log views
- Docker Compose with backend, frontend, PostgreSQL, n8n, and Nginx

## Local Development

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Docker:

```powershell
docker compose up --build
```

## Key URLs

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- n8n: `http://localhost:5678`

# ai-workflow-platform
