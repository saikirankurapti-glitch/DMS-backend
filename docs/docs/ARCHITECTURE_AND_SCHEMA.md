## Pharma DMS — Architecture & Database Schema (Complete)

**Workspace**: `DMS`  
**Backend**: FastAPI + SQLAlchemy + Alembic  
**Frontend**: React + Vite + TypeScript + Tailwind  
**Database**: PostgreSQL (prod via Docker Compose) or SQLite (dev fallback)  
**Last updated**: 2026-01-02

---

## 1) System architecture

### 1.1 High-level component view

```mermaid
flowchart LR
  U[User Browser] -->|HTTPS| FE[Frontend (Vite/React)\n:3000]
  FE -->|REST JSON\n/api/v1/*| BE[Backend (FastAPI)\n:8000]
  BE -->|SQLAlchemy| DB[(PostgreSQL)\n:5432]
  BE -->|local filesystem| FS[(Attachment storage)\nbackend/storage/attachments]
  BE -->|SMTP| SMTP[(Email Provider)]
  BE -->|OpenAI/Anthropic| LLM[(LLM API)]
```

### 1.2 Runtime topology (Docker Compose)

Defined in `docker-compose.yml`:

- **postgres**: `postgres:15-alpine`, exposed `5432:5432`
- **backend**: FastAPI container, exposed `8000:8000`
  - runs `python scripts/init_db.py` then `uvicorn app.main:app --reload`
- **pgadmin** (optional): `5050:80`

### 1.3 Repository layout

- **Backend**: `backend/app/*`
  - `app/main.py`: FastAPI app + CORS + mounts API router at `/api/v1`
  - `app/api/v1/*`: REST endpoints grouped by module
  - `app/models/*`: SQLAlchemy models (source of truth for ORM)
  - `app/schemas/*`: Pydantic request/response schemas
  - `app/core/*`: cross‑cutting services (security, RBAC, audit, email, AI)
  - `alembic/versions/*`: DB migrations (source of truth for DB schema)
- **Frontend**: `frontend/src/*`
  - `pages/*`: route-level UI pages
  - `components/*`: reusable UI + editor/commenting/versioning components
  - `services/*`: API client modules per backend feature
  - `context/AuthContext.tsx`: auth state + session polling

---

## 2) Backend architecture (FastAPI)

### 2.1 Entry point and routing

- **FastAPI app**: `backend/app/main.py`
  - Swagger: `/api/docs`
  - Base API prefix: `/api/v1`
- **Router registration**: `backend/app/api/v1/__init__.py`
  - Auth: `/auth/*`
  - Users: `/users/*`
  - Audit logs: `/audit-logs/*`
  - Documents: `/documents/*` (documents, versions, edit locks, export, comments)
  - Attachments: `/attachments/*`
  - Templates: `/templates/*`
  - Template Builder: `/template-builder/*`
  - AI: `/ai/*`
  - Print Control: `/print/*`

### 2.2 AuthN/AuthZ (JWT + RBAC)

- **JWT**:
  - Token created/decoded in `backend/app/core/security.py`
  - Auth dependency: `backend/app/api/deps.py:get_current_user`
- **Single active session enforcement**:
  - `users.active_session_token` + `users.session_created_at`
  - Frontend polls `/auth/validate-session` (see `frontend/src/context/AuthContext.tsx`)
- **RBAC**:
  - Role→permission mapping in `backend/app/core/rbac.py`
  - Enforcement via dependencies:
    - `require_admin`
    - `require_permission("<capability>")`

### 2.3 Audit logging (compliance)

- Persistent audit trail in table `audit_logs`
- Central writer: `backend/app/core/audit.py:AuditLogger`
- Audit fields capture:
  - actor (user_id/username)
  - action code
  - entity type/id
  - timestamp, IP, user agent, structured `details`

### 2.4 Domain modules (ownership summary)

- **Users & Roles**: create/update/activate/deactivate/reset/delete users; role assignment
- **Documents**: document metadata + lifecycle (soft delete)
- **Document Versions**: versioned content, workflow transitions, e-signature metadata, controlled versioning (parent/replaced_by/is_latest)
- **Edit Locks**: server-side lock tokens + heartbeats to avoid concurrent edits
- **Comments**: inline comments on a specific document version; resolve workflow
- **Attachments**: upload/download/delete; stored on local filesystem; linked to document or version
- **Templates**: template library + template version workflow (review/approval/publish)
- **Template Builder**: block-based template authoring + token library + doc generation
- **Notifications**: email dispatch + persisted send log in `notification_logs`
- **AI insights**: optional LLM-backed summarization/insights with cache endpoints
- **Print control**: controlled printing requests, tokens, copy tracking, audit logs, policies

---

## 3) Frontend architecture (React/Vite)

### 3.1 API access pattern

- API base URL: `frontend/src/config/api.ts`
  - default: `http://localhost:8000/api/v1`
  - overridable via `VITE_API_BASE_URL`
- Axios instance: `frontend/src/services/api.ts`
  - attaches `Authorization: Bearer <token>` from `localStorage`
  - 401 clears session + redirects to `/login`

### 3.2 Routing and feature pages (high level)

- Auth: `pages/Login.tsx`, `context/AuthContext.tsx`
- Admin: `pages/Users/*`, `pages/AuditLogs.tsx`
- Documents:
  - `pages/Documents/DocumentList.tsx`, `DocumentDetail.tsx`, `DocumentEditor.tsx`
  - editor components in `components/Editor/*`
  - comments in `components/Comments/*`
  - version history in `components/VersionHistory.tsx`
- Templates:
  - `pages/Templates/*` (upload, review, approval, versions, builder)
- Print control:
  - `pages/PrintRequests.tsx`

---

## 4) Database schema (complete)

### 4.1 Migration sources (authoritative)

Primary schema is defined in `backend/alembic/versions/*`:

- `001_initial_schema.py`: roles/users/user_roles/audit_logs
- `002_document_models.py`: documents/document_versions/attachments/edit_locks + enums
- `003_add_comments.py`: document_comments
- `004_add_session_management.py`: users.active_session_token/users.session_created_at
- `005_add_templates.py`: templates/template_versions/template_reviews/template_approvals + enum `templatestatus`
- `006_add_template_builder_fields.py`: template builder additions/adjustments
- `007_add_controlled_versioning.py`: controlled versioning fields on document_versions
- `d4a9c2c8603f_add_document_view_tracking.py`: document_views
- `8ea00ab4174f_add_notification_logs_table.py`: notification_logs
- `add_print_control_tables.py`: print control tables (see note in §4.5)

### 4.2 Core identity & compliance tables

#### `roles`

- **Columns**: `id (PK)`, `name (unique)`, `description`
- **Indexes**: `ix_roles_name (unique)`, `ix_roles_id`

#### `users`

- **Columns**:
  - identity: `id (PK)`, `username (unique)`, `email (unique)`
  - auth: `hashed_password`, `is_temp_password`
  - session: `active_session_token`, `session_created_at`
  - profile: `first_name`, `last_name`, `department`, `phone`
  - status/timestamps: `is_active`, `created_at`, `updated_at`, `last_login`
- **Indexes**: `ix_users_username (unique)`, `ix_users_email (unique)`, `ix_users_id`

#### `user_roles` (many-to-many)

- **Columns**: `user_id (PK/FK users.id)`, `role_id (PK/FK roles.id)`
- **On delete**: CASCADE to remove join rows when user/role deleted

#### `audit_logs`

- **Columns**:
  - `id (PK)`
  - `user_id (FK users.id, nullable, ondelete SET NULL)`
  - `username` (denormalized historical value)
  - `action`, `entity_type`, `entity_id`
  - `description`, `details (JSON)`
  - `ip_address`, `user_agent`
  - `timestamp`
- **Indexes**: `user_id`, `action`, `entity_type`, `entity_id`, `timestamp`

### 4.3 Documents, versions, locking, comments, views

#### `documents`

- **Columns**:
  - `id (PK)`
  - `document_number (unique)`
  - `title`, `description`, `department`, `tags (JSON)`
  - `owner_id (FK users.id)`
  - `created_by_id (FK users.id)`
  - `current_version_id (FK document_versions.id, nullable)`
  - `status` (string; denormalized from version workflow)
  - timestamps: `created_at`, `updated_at`
  - soft-delete: `is_deleted`, `deleted_at`, `deleted_by_id (FK users.id, nullable)`
- **Indexes**: `document_number (unique)`, `title`, `department`, `status`

#### `document_versions`

- **Columns** (selected; full set is large):
  - identity: `id (PK)`, `document_id (FK documents.id, ondelete CASCADE)`, `version_number`
  - content: `content_html`, `content_hash`
  - workflow: `status (ENUM versionstatus)`, timestamps/actors for submit/review/approve/publish/reject/archive
  - e-sign: `e_signature_data (JSON)`
  - attachments: `attachments_metadata (JSON)`, `docx_attachment_id (FK attachments.id, nullable)`
  - optimistic lock: `lock_version`
  - controlled versioning (added in 007):
    - `version_string`
    - `parent_version_id (FK document_versions.id, nullable)`
    - `replaced_by_version_id (FK document_versions.id, nullable)`
    - `is_latest (bool)`
    - `change_reason`, `change_type`
    - `effective_date`, `obsolete_date`
- **Indexes**: `document_id`, `status`, `version_string`, `is_latest`
- **Enum type**: `versionstatus` (created in 002 migration)

#### `edit_locks`

- **Purpose**: enforce exclusive editing per document version
- **Columns**: `id (PK)`, `document_version_id (FK document_versions.id, unique)`, `user_id (FK users.id)`, `lock_token (unique)`, `acquired_at`, `expires_at`, `last_heartbeat`, `session_id`, `ip_address`, `user_agent`
- **Constraints**: unique `document_version_id` (one lock per version)
- **Indexes**: `lock_token (unique)`, `expires_at`, `document_version_id`

#### `document_comments`

- **Columns**: `id (PK)`, `document_version_id (FK document_versions.id, ondelete CASCADE)`, `user_id (FK users.id)`, `comment_text`, selection metadata (`selected_text`, `selection_start`, `selection_end`, `text_context`), resolution (`is_resolved`, `resolved_at`, `resolved_by_id (FK users.id)`), `created_at`, `updated_at`
- **Indexes**: `document_version_id`, `user_id`, `is_resolved`

#### `document_views`

- **Purpose**: enforce “must view before review/approval” rule
- **Columns**: `id (PK)`, `document_id (FK documents.id, ondelete CASCADE)`, `version_id (FK document_versions.id, ondelete CASCADE)`, `user_id (FK users.id, ondelete CASCADE)`, `viewed_at`
- **Constraints**: unique (`version_id`, `user_id`)
- **Indexes**: `document_id`, `version_id`, `user_id`, `viewed_at`, composite (`document_id`, `version_id`, `user_id`)

### 4.4 Templates (library + workflow)

#### `templates`

- **Columns**: `id (PK)`, `name`, `template_code (unique, nullable)`, `description`, `category`, `department`, `confidentiality`, `created_by_id (FK users.id)`, `owner_id (FK users.id)`, `current_published_version_id (FK template_versions.id, nullable)`, `template_type`, timestamps, soft-delete columns
- **Indexes**: `name`, `category`, `department`, `template_code (unique)`

#### `template_versions`

- **Columns**: `id (PK)`, `template_id (FK templates.id, ondelete CASCADE)`, `version_number`, `revision`, `docx_file_path`, `preview_html_path`, `template_data (JSON)`, `generated_docx_path`, `generated_pdf_path`, `status (ENUM templatestatus)`, workflow fields, `sample_values (JSON)`, timestamps
- **Indexes**: `template_id`, `status`
- **Enum type**: `templatestatus`

#### `template_reviews`

- **Columns**: `id (PK)`, `template_version_id (FK template_versions.id, ondelete CASCADE)`, `reviewer_id (FK users.id)`, `comment`, timestamps
- **Indexes**: `template_version_id`

#### `template_approvals`

- **Columns**: `id (PK)`, `template_version_id (FK template_versions.id, ondelete CASCADE)`, `approver_id (FK users.id)`, `decision`, `comment`, `e_signature_data`, `created_at`
- **Indexes**: `template_version_id`

### 4.5 Notifications

#### `notification_logs`

- **Columns**: `id (PK)`, `document_id (FK documents.id, ondelete CASCADE)`, `version_id (FK document_versions.id, nullable, ondelete CASCADE)`, `event_type`, `recipient_email`, `recipient_user_id (FK users.id, nullable, ondelete SET NULL)`, `subject`, `body_html`, `status`, `sent_at`, `error_message`, `created_at`
- **Indexes**: `document_id`, `version_id`, `event_type`, `recipient_email`, `recipient_user_id`, `status`, `created_at`

### 4.6 Print control (controlled printing)

Tables created by `add_print_control_tables.py`:

- `print_requests`
- `print_tokens`
- `print_copy_tracking`
- `print_audit_logs`
- `print_policies`

**Important note**: this migration file has `down_revision = None` (i.e., it is not chained to the main Alembic history). In practice, that means:

- it may not run automatically in a linear `alembic upgrade head` flow without branch handling
- your environment may rely on `Base.metadata.create_all()` (see `backend/scripts/init_db.py`) to create these tables instead

---

## 4.7 DB tables and their schema (columns / constraints / indexes)

**Source of truth used**: `backend/alembic/versions/*` (migrations).  
When a column has no `server_default` in migrations but has a Python default in models, the default is **application-level** (set by SQLAlchemy/FastAPI), not enforced by the database.

### 4.7.1 `roles`

| Column | Type | Null | Default | Notes |
|---|---|---:|---|---|
| `id` | INTEGER | NO | - | PK |
| `name` | VARCHAR(50) | NO | - | unique |
| `description` | TEXT | YES | - |  |

- **PK**: (`id`)
- **Indexes**: `ix_roles_id`, `ix_roles_name` (**unique**)

### 4.7.2 `users`

| Column | Type | Null | Default | Notes |
|---|---|---:|---|---|
| `id` | INTEGER | NO | - | PK |
| `username` | VARCHAR(100) | NO | - | unique |
| `email` | VARCHAR(255) | NO | - | unique |
| `hashed_password` | VARCHAR(255) | NO | - |  |
| `is_temp_password` | BOOLEAN | NO | `0` |  |
| `first_name` | VARCHAR(100) | NO | - |  |
| `last_name` | VARCHAR(100) | NO | - |  |
| `department` | VARCHAR(100) | YES | - |  |
| `phone` | VARCHAR(20) | YES | - |  |
| `is_active` | BOOLEAN | NO | `1` |  |
| `created_at` | TIMESTAMP | NO | `CURRENT_TIMESTAMP` |  |
| `updated_at` | TIMESTAMP | NO | `CURRENT_TIMESTAMP` |  |
| `last_login` | TIMESTAMP | YES | - |  |
| `active_session_token` | VARCHAR(500) | YES | - | added in 004 |
| `session_created_at` | TIMESTAMP | YES | - | added in 004 |

- **PK**: (`id`)
- **Indexes**: `ix_users_id`, `ix_users_username` (**unique**), `ix_users_email` (**unique**)

### 4.7.3 `user_roles` (join table)

| Column | Type | Null | Default | Notes |
|---|---|---:|---|---|
| `user_id` | INTEGER | NO | - | FK → `users.id` (on delete CASCADE), part of PK |
| `role_id` | INTEGER | NO | - | FK → `roles.id` (on delete CASCADE), part of PK |

- **PK**: (`user_id`, `role_id`)
- **FKs**: `user_id` → `users.id`, `role_id` → `roles.id`

### 4.7.4 `audit_logs`

| Column | Type | Null | Default | Notes |
|---|---|---:|---|---|
| `id` | INTEGER | NO | - | PK |
| `user_id` | INTEGER | YES | - | FK → `users.id` (on delete SET NULL) |
| `username` | VARCHAR(100) | NO | - | denormalized historical username |
| `action` | VARCHAR(100) | NO | - |  |
| `entity_type` | VARCHAR(50) | NO | - |  |
| `entity_id` | INTEGER | YES | - |  |
| `description` | TEXT | NO | - |  |
| `details` | JSON | YES | - |  |
| `ip_address` | VARCHAR(45) | YES | - | IPv4/IPv6 |
| `user_agent` | VARCHAR(500) | YES | - |  |
| `timestamp` | TIMESTAMP | NO | `CURRENT_TIMESTAMP` |  |

- **PK**: (`id`)
- **FKs**: `user_id` → `users.id` (SET NULL)
- **Indexes**: `ix_audit_logs_id`, `ix_audit_logs_user_id`, `ix_audit_logs_action`, `ix_audit_logs_entity_type`, `ix_audit_logs_entity_id`, `ix_audit_logs_timestamp`

### 4.7.5 `documents`

| Column | Type | Null | Default | Notes |
|---|---|---:|---|---|
| `id` | INTEGER | NO | - | PK |
| `document_number` | VARCHAR(100) | NO | - | unique |
| `title` | VARCHAR(500) | NO | - |  |
| `description` | TEXT | YES | - |  |
| `department` | VARCHAR(100) | YES | - |  |
| `tags` | JSON | YES | - |  |
| `owner_id` | INTEGER | NO | - | FK → `users.id` |
| `created_by_id` | INTEGER | NO | - | FK → `users.id` |
| `current_version_id` | INTEGER | YES | - | FK → `document_versions.id` |
| `status` | VARCHAR(50) | NO | - | denormalized status |
| `created_at` | TIMESTAMP | NO | app-level | model default `utcnow()` |
| `updated_at` | TIMESTAMP | NO | app-level | model default `utcnow()` |
| `is_deleted` | BOOLEAN | NO | app-level | model default `false` |
| `deleted_at` | TIMESTAMP | YES | - |  |
| `deleted_by_id` | INTEGER | YES | - | FK → `users.id` |

- **PK**: (`id`)
- **FKs**:
  - `owner_id` → `users.id`
  - `created_by_id` → `users.id`
  - `current_version_id` → `document_versions.id`
  - `deleted_by_id` → `users.id`
- **Indexes**: `ix_documents_id`, `ix_documents_document_number` (**unique**), `ix_documents_title`, `ix_documents_department`, `ix_documents_status`

### 4.7.6 `document_versions`

**Enum**: `versionstatus` = (`DRAFT`, `UNDER_REVIEW`, `PENDING_APPROVAL`, `APPROVED`, `PUBLISHED`, `REJECTED`, `ARCHIVED`, `OBSOLETE`)

| Column | Type | Null | Default | Notes |
|---|---|---:|---|---|
| `id` | INTEGER | NO | - | PK |
| `document_id` | INTEGER | NO | - | FK → `documents.id` (on delete CASCADE) |
| `version_number` | INTEGER | NO | - | sequential 1,2,3… |
| `content_html` | TEXT | YES | - |  |
| `content_hash` | VARCHAR(64) | YES | - |  |
| `change_summary` | TEXT | YES | - |  |
| `status` | `versionstatus` | NO | - |  |
| `attachments_metadata` | JSON | YES | - |  |
| `docx_attachment_id` | INTEGER | YES | - | FK → `attachments.id` |
| `created_by_id` | INTEGER | NO | - | FK → `users.id` |
| `submitted_at` | TIMESTAMP | YES | - |  |
| `submitted_by_id` | INTEGER | YES | - | FK → `users.id` |
| `reviewed_at` | TIMESTAMP | YES | - |  |
| `reviewed_by_id` | INTEGER | YES | - | FK → `users.id` |
| `review_comments` | TEXT | YES | - |  |
| `approved_at` | TIMESTAMP | YES | - |  |
| `approved_by_id` | INTEGER | YES | - | FK → `users.id` |
| `approval_comments` | TEXT | YES | - |  |
| `e_signature_data` | JSON | YES | - |  |
| `published_at` | TIMESTAMP | YES | - |  |
| `published_by_id` | INTEGER | YES | - | FK → `users.id` |
| `rejected_at` | TIMESTAMP | YES | - |  |
| `rejected_by_id` | INTEGER | YES | - | FK → `users.id` |
| `rejection_reason` | TEXT | YES | - |  |
| `archived_at` | TIMESTAMP | YES | - |  |
| `archived_by_id` | INTEGER | YES | - | FK → `users.id` |
| `created_at` | TIMESTAMP | NO | app-level |  |
| `updated_at` | TIMESTAMP | NO | app-level |  |
| `lock_version` | INTEGER | NO | app-level | optimistic locking |
| `version_string` | VARCHAR(20) | YES | - | added in 007 |
| `parent_version_id` | INTEGER | YES | - | FK → `document_versions.id` (added in 007) |
| `is_latest` | BOOLEAN | NO | `1` | added in 007 |
| `replaced_by_version_id` | INTEGER | YES | - | FK → `document_versions.id` (added in 007) |
| `change_reason` | TEXT | YES | - | added in 007 |
| `change_type` | VARCHAR(10) | YES | - | added in 007 |
| `effective_date` | TIMESTAMP | YES | - | added in 007 |
| `obsolete_date` | TIMESTAMP | YES | - | added in 007 |

- **PK**: (`id`)
- **FKs**:
  - `document_id` → `documents.id` (CASCADE)
  - `docx_attachment_id` → `attachments.id`
  - `created_by_id`, `submitted_by_id`, `reviewed_by_id`, `approved_by_id`, `published_by_id`, `rejected_by_id`, `archived_by_id` → `users.id`
  - `parent_version_id` → `document_versions.id`
  - `replaced_by_version_id` → `document_versions.id`
- **Indexes**: `ix_document_versions_id`, `ix_document_versions_document_id`, `ix_document_versions_status`, `ix_document_versions_version_string`, `ix_document_versions_is_latest`

### 4.7.7 `attachments`

| Column | Type | Null | Default | Notes |
|---|---|---:|---|---|
| `id` | INTEGER | NO | - | PK |
| `filename` | VARCHAR(500) | NO | - | stored filename |
| `original_filename` | VARCHAR(500) | NO | - | uploaded filename |
| `mime_type` | VARCHAR(200) | NO | - |  |
| `file_size` | BIGINT | NO | - | bytes |
| `storage_path` | VARCHAR(1000) | NO | - |  |
| `storage_type` | VARCHAR(50) | NO | - | e.g., local |
| `checksum_sha256` | VARCHAR(64) | NO | - |  |
| `document_version_id` | INTEGER | YES | - | FK → `document_versions.id` |
| `document_id` | INTEGER | YES | - | FK → `documents.id` |
| `uploaded_by_id` | INTEGER | NO | - | FK → `users.id` |
| `uploaded_at` | TIMESTAMP | NO | app-level |  |
| `description` | VARCHAR(1000) | YES | - |  |
| `attachment_type` | VARCHAR(50) | YES | - |  |
| `scan_status` | VARCHAR(50) | YES | - |  |
| `scan_result` | VARCHAR(500) | YES | - |  |
| `scanned_at` | TIMESTAMP | YES | - |  |
| `is_deleted` | BOOLEAN | NO | app-level |  |
| `deleted_at` | TIMESTAMP | YES | - |  |
| `deleted_by_id` | INTEGER | YES | - | FK → `users.id` |

- **PK**: (`id`)
- **FKs**:
  - `document_version_id` → `document_versions.id`
  - `document_id` → `documents.id`
  - `uploaded_by_id` → `users.id`
  - `deleted_by_id` → `users.id`
- **Indexes**: `ix_attachments_id`, `ix_attachments_document_version_id`, `ix_attachments_document_id`

### 4.7.8 `edit_locks`

| Column | Type | Null | Default | Notes |
|---|---|---:|---|---|
| `id` | INTEGER | NO | - | PK |
| `document_version_id` | INTEGER | NO | - | FK → `document_versions.id` (CASCADE), unique |
| `user_id` | INTEGER | NO | - | FK → `users.id` |
| `lock_token` | VARCHAR(64) | NO | - | unique |
| `acquired_at` | TIMESTAMP | NO | app-level |  |
| `expires_at` | TIMESTAMP | NO | - |  |
| `last_heartbeat` | TIMESTAMP | NO | app-level |  |
| `session_id` | VARCHAR(100) | YES | - |  |
| `ip_address` | VARCHAR(45) | YES | - |  |
| `user_agent` | VARCHAR(500) | YES | - |  |

- **PK**: (`id`)
- **Constraints**: `uq_edit_locks_document_version_id` (unique `document_version_id`)
- **Indexes**: `ix_edit_locks_id`, `ix_edit_locks_document_version_id`, `ix_edit_locks_expires_at`, `ix_edit_locks_lock_token` (**unique**)

### 4.7.9 `document_comments`

| Column | Type | Null | Default | Notes |
|---|---|---:|---|---|
| `id` | INTEGER | NO | - | PK |
| `document_version_id` | INTEGER | NO | - | FK → `document_versions.id` (CASCADE) |
| `user_id` | INTEGER | NO | - | FK → `users.id` |
| `comment_text` | TEXT | NO | - |  |
| `selected_text` | TEXT | YES | - |  |
| `selection_start` | INTEGER | YES | - |  |
| `selection_end` | INTEGER | YES | - |  |
| `text_context` | TEXT | YES | - |  |
| `is_resolved` | BOOLEAN | YES | `false` | (migration uses `default=False`) |
| `resolved_at` | TIMESTAMP | YES | - |  |
| `resolved_by_id` | INTEGER | YES | - | FK → `users.id` |
| `created_at` | TIMESTAMP | NO | app-level |  |
| `updated_at` | TIMESTAMP | NO | app-level |  |

- **PK**: (`id`)
- **FKs**: `document_version_id` → `document_versions.id`, `user_id` → `users.id`, `resolved_by_id` → `users.id`
- **Indexes**: `ix_document_comments_version_id`, `ix_document_comments_user_id`, `ix_document_comments_is_resolved`

### 4.7.10 `document_views`

| Column | Type | Null | Default | Notes |
|---|---|---:|---|---|
| `id` | INTEGER | NO | - | PK |
| `document_id` | INTEGER | NO | - | FK → `documents.id` (CASCADE) |
| `version_id` | INTEGER | NO | - | FK → `document_versions.id` (CASCADE) |
| `user_id` | INTEGER | NO | - | FK → `users.id` (CASCADE) |
| `viewed_at` | TIMESTAMP | NO | `CURRENT_TIMESTAMP` |  |

- **PK**: (`id`)
- **Constraints**: `uq_version_user_view` (unique `version_id`, `user_id`)
- **Indexes**: `ix_document_views_document_id`, `ix_document_views_version_id`, `ix_document_views_user_id`, `ix_document_views_viewed_at`, `idx_document_version_user`

### 4.7.11 `templates`

| Column | Type | Null | Default | Notes |
|---|---|---:|---|---|
| `id` | INTEGER | NO | - | PK |
| `name` | VARCHAR(255) | NO | - |  |
| `template_code` | VARCHAR(100) | YES | - | unique index added in 006 |
| `description` | TEXT | YES | - |  |
| `category` | VARCHAR(100) | YES | - |  |
| `department` | VARCHAR(100) | YES | - |  |
| `confidentiality` | VARCHAR(50) | YES | `Internal` |  |
| `created_by_id` | INTEGER | NO | - | FK → `users.id` |
| `owner_id` | INTEGER | NO | - | FK → `users.id` |
| `current_published_version_id` | INTEGER | YES | - | intended FK → `template_versions.id` |
| `template_type` | VARCHAR(50) | NO | `block_builder` |  |
| `created_at` | TIMESTAMP | NO | app-level |  |
| `updated_at` | TIMESTAMP | NO | app-level |  |
| `is_deleted` | BOOLEAN | NO | app-level |  |
| `deleted_at` | TIMESTAMP | YES | - |  |
| `deleted_by_id` | INTEGER | YES | - | FK → `users.id` |

- **PK**: (`id`)
- **FKs**: `created_by_id`, `owner_id`, `deleted_by_id` → `users.id`
- **Indexes**: `ix_templates_id`, `ix_templates_name`, `ix_templates_category`, `ix_templates_department`, `ix_templates_template_code` (**unique**)
- **FK note**: migration `005_add_templates.py` attempts to add FK for `current_published_version_id` but may be skipped on SQLite.

### 4.7.12 `template_versions`

**Enum**: `templatestatus` = (`Draft`, `UnderReview`, `PendingApproval`, `Rejected`, `Published`)

| Column | Type | Null | Default | Notes |
|---|---|---:|---|---|
| `id` | INTEGER | NO | - | PK |
| `template_id` | INTEGER | NO | - | FK → `templates.id` (CASCADE) |
| `version_number` | INTEGER | NO | - |  |
| `revision` | VARCHAR(50) | YES | - |  |
| `docx_file_path` | VARCHAR(500) | YES | - | made nullable in 006 |
| `preview_html_path` | VARCHAR(500) | YES | - |  |
| `template_data` | JSON | YES | - |  |
| `generated_docx_path` | VARCHAR(500) | YES | - |  |
| `generated_pdf_path` | VARCHAR(500) | YES | - |  |
| `status` | `templatestatus` | NO | - |  |
| `created_by_id` | INTEGER | NO | - | FK → `users.id` |
| `submitted_for_review_at` | TIMESTAMP | YES | - |  |
| `submitted_for_review_by_id` | INTEGER | YES | - | FK → `users.id` |
| `submitted_for_approval_at` | TIMESTAMP | YES | - |  |
| `submitted_for_approval_by_id` | INTEGER | YES | - | FK → `users.id` |
| `published_at` | TIMESTAMP | YES | - |  |
| `published_by_id` | INTEGER | YES | - | FK → `users.id` |
| `rejected_at` | TIMESTAMP | YES | - |  |
| `rejected_by_id` | INTEGER | YES | - | FK → `users.id` |
| `rejection_reason` | TEXT | YES | - |  |
| `sample_values` | JSON | YES | - |  |
| `created_at` | TIMESTAMP | NO | app-level |  |
| `updated_at` | TIMESTAMP | NO | app-level |  |

- **PK**: (`id`)
- **FKs**: `template_id` → `templates.id` (CASCADE), `created_by_id` → `users.id`, other `*_by_id` → `users.id`
- **Indexes**: `ix_template_versions_id`, `ix_template_versions_template_id`, `ix_template_versions_status`

### 4.7.13 `template_reviews`

| Column | Type | Null | Default | Notes |
|---|---|---:|---|---|
| `id` | INTEGER | NO | - | PK |
| `template_version_id` | INTEGER | NO | - | FK → `template_versions.id` (CASCADE) |
| `reviewer_id` | INTEGER | NO | - | FK → `users.id` |
| `comment` | TEXT | NO | - |  |
| `created_at` | TIMESTAMP | NO | app-level |  |
| `updated_at` | TIMESTAMP | NO | app-level |  |

- **PK**: (`id`)
- **Indexes**: `ix_template_reviews_id`, `ix_template_reviews_template_version_id`

### 4.7.14 `template_approvals`

| Column | Type | Null | Default | Notes |
|---|---|---:|---|---|
| `id` | INTEGER | NO | - | PK |
| `template_version_id` | INTEGER | NO | - | FK → `template_versions.id` (CASCADE) |
| `approver_id` | INTEGER | NO | - | FK → `users.id` |
| `decision` | VARCHAR(20) | NO | - |  |
| `comment` | TEXT | YES | - |  |
| `e_signature_data` | TEXT | YES | - | stored JSON string |
| `created_at` | TIMESTAMP | NO | app-level |  |

- **PK**: (`id`)
- **Indexes**: `ix_template_approvals_id`, `ix_template_approvals_template_version_id`

### 4.7.15 `notification_logs`

| Column | Type | Null | Default | Notes |
|---|---|---:|---|---|
| `id` | INTEGER | NO | - | PK |
| `document_id` | INTEGER | NO | - | FK → `documents.id` (CASCADE) |
| `version_id` | INTEGER | YES | - | FK → `document_versions.id` (CASCADE) |
| `event_type` | VARCHAR(50) | NO | - |  |
| `recipient_email` | VARCHAR(255) | NO | - |  |
| `recipient_user_id` | INTEGER | YES | - | FK → `users.id` (SET NULL) |
| `subject` | VARCHAR(500) | NO | - |  |
| `body_html` | TEXT | YES | - |  |
| `status` | VARCHAR(20) | NO | - |  |
| `sent_at` | TIMESTAMP | YES | - |  |
| `error_message` | TEXT | YES | - |  |
| `created_at` | TIMESTAMP | NO | app-level |  |

- **PK**: (`id`)
- **Indexes**: `ix_notification_logs_id`, `ix_notification_logs_document_id`, `ix_notification_logs_version_id`, `ix_notification_logs_event_type`, `ix_notification_logs_recipient_email`, `ix_notification_logs_recipient_user_id`, `ix_notification_logs_status`, `ix_notification_logs_created_at`

### 4.7.16 Print control tables

#### `print_requests`

| Column | Type | Null | Default | Notes |
|---|---|---:|---|---|
| `id` | INTEGER | NO | - | PK |
| `document_id` | INTEGER | NO | - | FK → `documents.id` (CASCADE) |
| `version_id` | INTEGER | NO | - | FK → `document_versions.id` (CASCADE) |
| `event_type` | VARCHAR(50) | NO | - |  |
| `business_justification` | TEXT | NO | - |  |
| `copies_requested` | INTEGER | NO | `1` |  |
| `copies_approved` | INTEGER | YES | - |  |
| `intended_use_location` | VARCHAR(500) | NO | - |  |
| `validity_type` | VARCHAR(50) | NO | `One-time` |  |
| `valid_until` | TIMESTAMP | YES | - |  |
| `task_reference` | VARCHAR(255) | YES | - |  |
| `printer_type` | VARCHAR(50) | NO | `Secure Network Printer` |  |
| `printer_name` | VARCHAR(255) | YES | - |  |
| `requestor_id` | INTEGER | NO | - | FK → `users.id` |
| `requestor_declaration` | BOOLEAN | NO | `false` |  |
| `requested_at` | TIMESTAMP | NO | app-level |  |
| `status` | VARCHAR(50) | NO | `Pending` |  |
| `level1_approver_id` | INTEGER | YES | - | FK → `users.id` |
| `level1_approved_at` | TIMESTAMP | YES | - |  |
| `level1_comments` | TEXT | YES | - |  |
| `level1_signature` | TEXT | YES | - |  |
| `level2_approver_id` | INTEGER | YES | - | FK → `users.id` |
| `level2_approved_at` | TIMESTAMP | YES | - |  |
| `level2_comments` | TEXT | YES | - |  |
| `level2_signature` | TEXT | YES | - |  |
| `level2_copies_approved` | INTEGER | YES | - |  |
| `level2_validity_override` | TIMESTAMP | YES | - |  |
| `rejected_by_id` | INTEGER | YES | - | FK → `users.id` |
| `rejected_at` | TIMESTAMP | YES | - |  |
| `rejection_reason` | TEXT | YES | - |  |
| `created_at` | TIMESTAMP | NO | app-level |  |
| `updated_at` | TIMESTAMP | YES | - |  |
| `completed_at` | TIMESTAMP | YES | - |  |

- **Indexes**: `ix_print_requests_id`, `ix_print_requests_status`, `ix_print_requests_document_id`

#### `print_tokens`

| Column | Type | Null | Default | Notes |
|---|---|---:|---|---|
| `id` | INTEGER | NO | - | PK |
| `print_request_id` | INTEGER | NO | - | FK → `print_requests.id` (CASCADE) |
| `copy_number` | INTEGER | NO | - |  |
| `token` | VARCHAR(64) | NO | - | unique |
| `token_hash` | VARCHAR(128) | NO | - |  |
| `single_use` | BOOLEAN | NO | `true` |  |
| `expires_at` | TIMESTAMP | NO | - |  |
| `printer_bound` | VARCHAR(255) | YES | - |  |
| `status` | VARCHAR(50) | NO | `Active` |  |
| `used_at` | TIMESTAMP | YES | - |  |
| `used_by_id` | INTEGER | YES | - | FK → `users.id` |
| `printer_used` | VARCHAR(255) | YES | - |  |
| `pages_printed` | INTEGER | YES | - |  |
| `invalidated_at` | TIMESTAMP | YES | - |  |
| `invalidation_reason` | VARCHAR(500) | YES | - |  |
| `created_at` | TIMESTAMP | NO | app-level |  |

- **Indexes**: `ix_print_tokens_id`, `ix_print_tokens_token` (**unique**), `ix_print_tokens_status`

#### `print_copy_tracking`

| Column | Type | Null | Default | Notes |
|---|---|---:|---|---|
| `id` | INTEGER | NO | - | PK |
| `token_id` | INTEGER | NO | - | FK → `print_tokens.id` (CASCADE), unique |
| `copy_number` | INTEGER | NO | - |  |
| `document_code` | VARCHAR(100) | NO | - |  |
| `version_string` | VARCHAR(50) | NO | - |  |
| `printed_by_id` | INTEGER | NO | - | FK → `users.id` |
| `printed_at` | TIMESTAMP | NO | - |  |
| `print_event_type` | VARCHAR(50) | NO | - |  |
| `watermark_text` | TEXT | NO | - |  |
| `status` | VARCHAR(50) | NO | `Active` |  |
| `destruction_reminder_sent` | BOOLEAN | YES | `false` |  |
| `destruction_reminder_sent_at` | TIMESTAMP | YES | - |  |
| `destruction_due_date` | TIMESTAMP | YES | - |  |
| `acknowledged_no_duplication` | BOOLEAN | YES | `false` |  |
| `acknowledged_destruction` | BOOLEAN | YES | `false` |  |
| `acknowledged_loss_reporting` | BOOLEAN | YES | `false` |  |
| `acknowledged_at` | TIMESTAMP | YES | - |  |
| `destroyed_at` | TIMESTAMP | YES | - |  |
| `destroyed_by_id` | INTEGER | YES | - | FK → `users.id` |
| `destruction_verified_by_id` | INTEGER | YES | - | FK → `users.id` |
| `destruction_verified_at` | TIMESTAMP | YES | - |  |
| `lost_reported_at` | TIMESTAMP | YES | - |  |
| `lost_reported_by_id` | INTEGER | YES | - | FK → `users.id` |
| `deviation_reference` | VARCHAR(100) | YES | - |  |
| `expired_at` | TIMESTAMP | YES | - |  |
| `created_at` | TIMESTAMP | NO | app-level |  |
| `updated_at` | TIMESTAMP | YES | - |  |

- **Indexes**: `ix_print_copy_tracking_id`, `ix_print_copy_tracking_status`

#### `print_audit_logs`

| Column | Type | Null | Default | Notes |
|---|---|---:|---|---|
| `id` | INTEGER | NO | - | PK |
| `event_type` | VARCHAR(100) | NO | - |  |
| `event_description` | TEXT | NO | - |  |
| `print_request_id` | INTEGER | YES | - | FK → `print_requests.id` (SET NULL) |
| `token_id` | INTEGER | YES | - | FK → `print_tokens.id` (SET NULL) |
| `document_id` | INTEGER | YES | - | FK → `documents.id` (SET NULL) |
| `version_id` | INTEGER | YES | - | FK → `document_versions.id` (SET NULL) |
| `user_id` | INTEGER | NO | - | FK → `users.id` |
| `user_role` | VARCHAR(100) | NO | - |  |
| `ip_address` | VARCHAR(45) | YES | - |  |
| `device_info` | VARCHAR(500) | YES | - |  |
| `printer_identity` | VARCHAR(255) | YES | - |  |
| `data_snapshot` | TEXT | YES | - |  |
| `timestamp` | TIMESTAMP | NO | - |  |
| `log_hash` | VARCHAR(128) | YES | - |  |

- **Indexes**: `ix_print_audit_logs_id`, `ix_print_audit_logs_event_type`, `ix_print_audit_logs_timestamp`

#### `print_policies`

| Column | Type | Null | Default | Notes |
|---|---|---:|---|---|
| `id` | INTEGER | NO | - | PK |
| `name` | VARCHAR(100) | NO | - | unique |
| `description` | TEXT | YES | - |  |
| `max_copies_per_request` | INTEGER | NO | `10` |  |
| `max_active_copies_per_document` | INTEGER | NO | `50` |  |
| `level1_approval_required` | BOOLEAN | YES | `false` |  |
| `level2_approval_required` | BOOLEAN | YES | `true` |  |
| `default_validity_hours` | INTEGER | NO | `24` |  |
| `max_validity_hours` | INTEGER | NO | `168` |  |
| `event_rules` | TEXT | YES | - | JSON string |
| `allow_obsolete_with_override` | BOOLEAN | YES | `true` |  |
| `require_secure_printer` | BOOLEAN | YES | `false` |  |
| `require_destruction_confirmation` | BOOLEAN | YES | `true` |  |
| `destruction_reminder_days` | INTEGER | YES | `7` |  |
| `is_active` | BOOLEAN | YES | `true` |  |
| `created_at` | TIMESTAMP | NO | app-level |  |
| `updated_at` | TIMESTAMP | YES | - |  |

- **Indexes**: `ix_print_policies_id`

---

## 5) API surface (by module)

Base URL: `http://<host>:8000/api/v1`

### 5.1 Authentication

- `POST /auth/login`
- `GET /auth/me`
- `POST /auth/logout`
- `GET /auth/validate-session`

### 5.2 Users (admin)

- `POST /users`
- `GET /users`
- `GET /users/{user_id}`
- `PUT /users/{user_id}`
- `PATCH /users/{user_id}/activate`
- `PATCH /users/{user_id}/deactivate`
- `POST /users/{user_id}/reset-password`
- `DELETE /users/{user_id}`

### 5.3 Audit logs (admin)

- `GET /audit-logs`
- `GET /audit-logs/actions`
- `GET /audit-logs/entity-types`

### 5.4 Documents

- `POST /documents`
- `GET /documents`
- `GET /documents/{document_id}`
- `PATCH /documents/{document_id}`
- `DELETE /documents/{document_id}`

### 5.5 Document versions & workflow

- `POST /documents/{document_id}/versions`
- `GET /documents/{document_id}/versions`
- `GET /documents/{document_id}/versions/{version_id}`
- `PATCH /documents/{document_id}/versions/{version_id}`
- `POST /documents/{document_id}/versions/{version_id}/save`
- `GET /documents/{document_id}/versions/history`
- `POST /documents/{document_id}/versions/{version_id}/create-new`
- `POST /documents/{document_id}/versions/{version_id}/submit`
- `POST /documents/{document_id}/versions/{version_id}/approve`
- `POST /documents/{document_id}/versions/{version_id}/reject`
- `POST /documents/{document_id}/versions/{version_id}/publish`
- `POST /documents/{document_id}/versions/{version_id}/mark-viewed`
- `POST /documents/{document_id}/versions/{version_id}/archive`
- `POST /documents/{document_id}/versions/{version_id}/restore`

### 5.6 Edit locks

- `POST /documents/{document_id}/versions/{version_id}/lock`
- `GET /documents/{document_id}/versions/{version_id}/lock`
- `POST /documents/{document_id}/versions/{version_id}/lock/heartbeat`
- `DELETE /documents/{document_id}/versions/{version_id}/lock`

### 5.7 Attachments

- `POST /attachments`
- `GET /attachments/{attachment_id}`
- `GET /attachments/{attachment_id}/download`
- `DELETE /attachments/{attachment_id}`
- `GET /attachments/document/{document_id}/list`

### 5.8 Comments

- `POST /documents/{document_id}/versions/{version_id}/comments`
- `GET /documents/{document_id}/versions/{version_id}/comments`
- `PATCH /documents/{document_id}/versions/{version_id}/comments/{comment_id}`
- `DELETE /documents/{document_id}/versions/{version_id}/comments/{comment_id}`

### 5.9 DOCX import/export (optional module)

- `POST /documents/{document_id}/versions/{version_id}/export/docx`
- `POST /documents/{document_id}/versions/{version_id}/import/docx`

### 5.10 Templates (classic)

- `POST /templates/upload`
- `GET /templates`
- `GET /templates/published`
- `GET /templates/{template_id}/versions`
- `GET /templates/{template_id}/versions/{version_id}`
- `POST /templates/{template_id}/versions/{version_id}/submit-for-review`
- `POST /templates/{template_id}/versions/{version_id}/reviews`
- `POST /templates/{template_id}/versions/{version_id}/submit-for-approval`
- `POST /templates/{template_id}/versions/{version_id}/approve`
- `POST /templates/{template_id}/versions/{version_id}/publish`
- `GET /templates/{template_id}/versions/{version_id}/html`
- `GET /templates/{template_id}/images/{filename}`

### 5.11 Template Builder (block-based)

- `POST /template-builder/create`
- `GET /template-builder/{template_id}`
- `PUT /template-builder/{template_id}`
- `POST /template-builder/{template_id}/preview`
- `POST /template-builder/{template_id}/generate`
- `GET /template-builder/{template_id}/download`
- `GET /template-builder/{template_id}/tokens`
- `GET /template-builder/tokens/library`

### 5.12 AI insights

- `GET /ai/status`
- `POST /ai/...` (insight generation endpoint)
- `DELETE /ai/cache`

### 5.13 Print control

- `POST /print/requests`
- `GET /print/requests`
- `GET /print/requests/{request_id}`
- `POST /print/requests/{request_id}/approve-level1`
- `POST /print/requests/{request_id}/approve-level2`
- `POST /print/requests/{request_id}/reject`
- `POST /print/requests/{request_id}/cancel`
- `POST /print/execute`
- `GET /print/tokens/my-tokens`
- `GET /print/copies/my-copies`
- `POST /print/copies/{copy_id}/acknowledge`
- `POST /print/copies/{copy_id}/destroy`
- `POST /print/copies/{copy_id}/report-lost`
- `GET /print/statistics`
- `GET /print/audit-logs`

---

## 6) Known schema/implementation mismatches (worth reviewing)



- **`versionstatus` values**:
  - migration `002_document_models.py` creates enum values like `DRAFT`, `UNDER_REVIEW`, `PENDING_APPROVAL`, `APPROVED`, `PUBLISHED`, `REJECTED`, `ARCHIVED`, `OBSOLETE`
  - model `DocumentVersion.VersionStatus` includes `EFFECTIVE` (and may not include `PUBLISHED`)
- **Print-control enums**:
  - migration uses `String(...)` columns for `event_type`, `validity_type`, `printer_type`, `status`
  - models use `Enum(...)` types, which may serialize differently unless explicitly configured
- **Alembic history**:
  - `add_print_control_tables.py` is not chained to the main revision graph (`down_revision = None`)




