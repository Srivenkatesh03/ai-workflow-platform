# API Endpoints

Base path: `/api/v1`

Core endpoints:

- `GET /health`
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `GET /users/me`
- `PUT /users/me`
- `GET /workflows`
- `POST /workflows`
- `GET /workflows/{workflow_id}`
- `PUT /workflows/{workflow_id}`
- `DELETE /workflows/{workflow_id}`
- `POST /workflows/{workflow_id}/execute`
- `GET /executions`
- `POST /executions/{execution_id}/retry`
- `POST /webhooks/{workflow_id}`
- `POST /ai/summarize`
- `POST /ai/classify`
- `POST /notifications/email`
- `POST /notifications/slack`

All successful responses use:

```json
{
  "success": true,
  "message": "Operation successful",
  "data": {}
}
```
