# Important File Structure (selected, excludes docs files)

Below are the important files and folders to navigate when working on this project. Documentation files are intentionally excluded from this listing.

- `docker-compose.yml`
- `start.bat`, `start.sh`, `restart_frontend.bat`
- `setup_database.sql`, `setup_postgres_env.bat`, `setup_postgres_env.sh`

backend/
- `Dockerfile` (backend/Dockerfile)
- `run.py`
- `requirements.txt`
- `alembic/`
  - `alembic.ini`
  - `env.py`
  - `versions/` (migration files, e.g., `001_initial_schema.py`, `007_add_controlled_versioning.py`)
- scripts/
  - `init_db.py`
  - `reset_db.py`
  - `add_print_tables.py`
  - `test_audit_logs.py`
- tests/
  - `conftest.py`
  - `test_auth.py`
  - `test_users.py`
- app/
  - `main.py` — FastAPI app entrypoint (CORS, router registration)
  - `config.py` — `Settings` / env var config
  - `database.py` — DB engine / session provider (dependency `get_db`) (if present)
  - `api/`
    - `v1/`
      - `__init__.py` — `api_router` aggregating v1 routers
      - `auth.py`
      - `users.py`
      - `documents.py`
      - `document_versions.py`
      - `edit_locks.py`
      - `attachments.py`
      - `comments.py`
      - `templates.py`
      - `template_builder.py` (optional)
      - `export.py` (optional)
      - `ai_insights.py` (optional)
      - `print_control.py` (optional)
    - `deps.py` — common FastAPI dependencies (auth, db, headers)
  - `core/`
    - `security.py` — password hashing, JWT utilities
    - `rbac.py` — Role & permission helpers
    - `audit.py` — `AuditLogger` helpers
    - `email_service.py`, `email_templates.py`
    - `document_utils.py` — document-number helpers
    - `ai_service.py` — AI/LLM integration (optional)
    - `notification_dispatcher.py`
  - `models/`
    - `user.py`, `role.py`, `document.py`, `document_version.py`, `attachment.py`, `comment.py`, `audit_log.py`
  - `schemas/` — Pydantic schemas for requests/responses (e.g., `auth.py`, `user.py`, `document.py`)
  - `storage/` — attachment or file storage helpers (if present)

frontend/
- `src/` — main frontend source directory (React/Vite or similar)
- `package.json`, `vite.config.js` (if present)

top-level
- `.env` (not committed) — environment variables used by `app.config.Settings`
- `LICENSE`, `CONTRIBUTING.md`

Notes
- This file intentionally omits Markdown documentation files and the `docs/` folder contents.
- If you want a full tree including every file or include docs files, tell me and I will generate it.
