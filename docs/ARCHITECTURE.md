# Project Architecture

This section describes high-level architecture, module interactions, and data flow.

## High-level components

- Frontend (React) — UI, runs in browser.
- Backend (FastAPI) — REST API, business logic, data models, authentication.
- Database (SQL) — persistent storage for users, documents, versions, audit logs.
- SMTP/email provider — for notifications and e-signature workflows.
- Optional AI service (OpenAI/Anthropic) — for document insights.

## How modules interact

1. Frontend authenticates user via `POST /api/v1/auth/login` → Backend `auth` route.
2. Backend validates credentials (`app.core.security`), records audit (`app.core.audit`) and issues JWT.
3. Frontend uses Bearer token to call protected endpoints (documents, comments, attachments).
4. Backend routes use dependencies (e.g., `get_db`, `get_current_user`) to fetch DB session and user.
5. Business logic often lives in `app.api.v1.*` endpoints and uses `app.models` + helper functions from `app.core`.
6. Audit events are written by `AuditLogger` to `audit_log` table for every critical action.

## Data flow (text-based)

User login and session creation:

Frontend -> POST /api/v1/auth/login -> Backend(auth.login)
  auth.login -> verify_password -> DB(User) -> create_access_token -> persist active_session_token -> AuditLogger.log_login
  -> Response: {access_token, user}

Document creation flow:

Frontend -> POST /api/v1/documents -> Backend(documents.create_document)
  documents.create_document -> permission checks (core.rbac or current_user.has_role) -> generate_document_number -> DB(Document) + DB(DocumentVersion)
  -> AuditLogger.log(DOCUMENT_CREATED) -> Response: DocumentResponse

Document approval flow (simplified):

User(Approver) -> POST /api/v1/documents/{id}/versions/{vid}/approve -> Backend -> validate e-signature -> update version status -> set effective -> mark previous effective version obsolete -> AuditLogger.log(DOCUMENT_APPROVED)

## Dependencies and key libraries

- FastAPI — web framework and automatic OpenAPI generation
- Uvicorn — ASGI server
- SQLAlchemy — ORM
- Alembic — migrations
- Pydantic / pydantic-settings — configuration and request/response schemas
- jose — JWT encoding/decoding
- passlib — password hashing (pbkdf2_sha256 by default)
- fastapi-mail — email sending

## Notes on scaling & production

- Use Postgres for production; configure `DATABASE_URL` accordingly.
- Put Uvicorn behind a process manager (Gunicorn + Uvicorn workers) or use an ASGI platform.
- Use HTTPS and secure cookies when integrating frontend.
- Consider using a dedicated audit log store or write-through to an append-only log for long-term retention.
