# Local Docker Deployment

1. Copy `.env.example` to `.env`.
2. Update secrets in `.env`.
3. Start the stack:

```powershell
docker compose up --build
```

Services:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- Nginx proxy: `http://localhost:8080`
- n8n: `http://localhost:5678`
- PostgreSQL: `localhost:5432`

