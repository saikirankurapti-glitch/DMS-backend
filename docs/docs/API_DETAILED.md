# Enhanced API Reference - All Endpoints

This comprehensive API reference documents every endpoint in Q-Docs with request/response examples, status codes, and authentication requirements.

---

## Authentication Endpoints

Base path: `/api/v1/auth`

### POST /login
**Single-session enforcement login with optional force override**

- **Authentication:** None (public endpoint)
- **Status Codes:**
  - 200 OK — Successful login
  - 409 CONFLICT — Session conflict (another session active)
  - 401 UNAUTHORIZED — Invalid credentials
  - 403 FORBIDDEN — Account inactive

Request:
```json
{
  "username": "admin",
  "password": "Admin@123456",
  "force_login": false
}
```

Response (200):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInVzZXJfaWQiOjEsInJvbGVzIjpbIkRNU0FkbWluIl0sImV4cCI6fQ.signature",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@pharma-dms.com",
    "full_name": "Administrator",
    "roles": ["DMS_Admin"],
    "is_active": true
  },
  "requires_password_change": false
}
```

Response (409 - Session Conflict):
```json
{
  "session_conflict": true,
  "message": "Another session is already active",
  "existing_session_created_at": "2024-01-15T10:30:00",
  "detail": "You are already logged in from another device/tab. Do you want to end that session and continue here?"
}
```

---

### GET /me
**Get current authenticated user's profile**

- **Authentication:** Required (Bearer token)
- **Status Codes:**
  - 200 OK
  - 401 UNAUTHORIZED — Invalid token
  - 403 FORBIDDEN — Inactive account

Response (200):
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@pharma-dms.com",
  "full_name": "Administrator",
  "roles": ["DMS_Admin"],
  "is_active": true
}
```

---

### POST /logout
**Logout and clear active session**

- **Authentication:** Required (Bearer token)
- **Status Codes:**
  - 200 OK
  - 401 UNAUTHORIZED

Response (200):
```json
{
  "message": "Successfully logged out"
}
```

---

### GET /validate-session
**Validate if current token's session is still active**

- **Authentication:** Optional (checks session validity)
- **Status Codes:**
  - 200 OK

Response (200 - Valid):
```json
{
  "valid": true
}
```

Response (200 - Invalid):
```json
{
  "valid": false,
  "reason": "Session invalidated",
  "message": "Your session has been ended because you logged in from another device/tab."
}
```

---

## User Management Endpoints (Admin Only)

Base path: `/api/v1/users` | **Requires:** DMS_Admin role

### POST / (Create User)

**Create a new user with roles**

- **Authentication:** Required (DMS_Admin)
- **Status Codes:**
  - 201 CREATED
  - 400 BAD_REQUEST — User exists or invalid role
  - 401 UNAUTHORIZED
  - 403 FORBIDDEN

Request:
```json
{
  "username": "jdoe",
  "email": "john.doe@company.com",
  "password": "SecurePass123",
  "first_name": "John",
  "last_name": "Doe",
  "department": "QA",
  "phone": "+1-555-0100",
  "role_ids": [2, 3],
  "is_active": true
}
```

Response (201):
```json
{
  "id": 5,
  "username": "jdoe",
  "email": "john.doe@company.com",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "department": "QA",
  "phone": "+1-555-0100",
  "roles": [
    {"id": 2, "name": "Reviewer"},
    {"id": 3, "name": "Approver"}
  ],
  "is_active": true,
  "created_at": "2024-01-15T10:30:00"
}
```

---

### GET / (List Users)

**List all users with filtering and pagination**

- **Authentication:** Required (DMS_Admin)
- **Query Parameters:**
  - `page` (int, default: 1) — page number
  - `page_size` (int, default: 50, max: 100)
  - `role` (string, optional) — filter by role name (e.g., "Author")
  - `is_active` (boolean, optional) — filter by active status
  - `search` (string, optional) — search username/email/name

Response (200):
```json
{
  "users": [
    {
      "id": 1,
      "username": "admin",
      "email": "admin@pharma-dms.com",
      "full_name": "Administrator",
      "department": "IT",
      "roles": [{"id": 1, "name": "DMS_Admin"}],
      "is_active": true,
      "created_at": "2024-01-10T00:00:00"
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 50
}
```

---

### GET /{user_id}

**Get user details by ID**

- **Status Codes:** 200 OK, 404 NOT_FOUND

---

### PUT /{user_id}

**Update user information and roles**

Request:
```json
{
  "email": "john.d@company.com",
  "first_name": "Jonathan",
  "last_name": "Doe",
  "department": "R&D",
  "phone": "+1-555-0101",
  "is_active": true,
  "role_ids": [2]
}
```

---

### PATCH /{user_id}/activate

**Activate a deactivated user account**

- **Status Codes:** 200 OK, 400 BAD_REQUEST (already active), 404 NOT_FOUND

---

### PATCH /{user_id}/deactivate

**Deactivate a user account (prevents login)**

- **Status Codes:** 200 OK, 400 BAD_REQUEST (already inactive or self-deactivation)

---

### POST /{user_id}/reset-password

**Admin resets user's password**

- **Status Codes:** 200 OK, 404 NOT_FOUND

Request:
```json
{
  "new_password": "NewSecurePass456",
  "force_change": true
}
```

Response (200):
```json
{
  "message": "Password reset successfully",
  "requires_password_change": true
}
```

---

### DELETE /{user_id}

**Delete a user (permanent)**

- **Status Codes:** 204 NO_CONTENT, 404 NOT_FOUND

---

## Document Management Endpoints

Base path: `/api/v1/documents`

### POST / (Create Document)

**Create a new document (Author/Admin)**

- **Authentication:** Required (Author or DMS_Admin)
- **Status Codes:**
  - 201 CREATED
  - 400 BAD_REQUEST — Invalid data
  - 403 FORBIDDEN — Insufficient permissions

Request:
```json
{
  "title": "SOP-Quality Assurance Procedures",
  "document_number": "QA-SOP-001",
  "description": "Standard Operating Procedures for Quality Assurance",
  "department": "Quality Assurance",
  "tags": ["SOP", "QA", "Critical"],
  "owner_id": null
}
```

Response (201):
```json
{
  "id": 1,
  "document_number": "SOP-2024-001",
  "title": "SOP-Quality Assurance Procedures",
  "description": "Standard Operating Procedures for Quality Assurance",
  "department": "Quality Assurance",
  "tags": ["SOP", "QA", "Critical"],
  "status": "DRAFT",
  "owner_id": 2,
  "owner_username": "jdoe",
  "owner_full_name": "John Doe",
  "created_by_id": 2,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00",
  "version_count": 0
}
```

---

### GET / (List Documents)

**List and search documents with filters**

- **Query Parameters:**
  - `title` (string, optional) — partial match
  - `document_number` (string, optional)
  - `department` (string, optional)
  - `status` (string, optional) — DRAFT, EFFECTIVE, ARCHIVED, etc.
  - `owner_id` (int, optional)
  - `show_all_statuses` (boolean, default: false)
  - `page`, `page_size`

Response (200):
```json
{
  "items": [
    {
      "id": 1,
      "document_number": "SOP-2024-001",
      "title": "SOP-Quality Assurance Procedures",
      "department": "Quality Assurance",
      "status": "EFFECTIVE",
      "owner_username": "jdoe",
      "version_count": 3,
      "created_at": "2024-01-10T10:00:00",
      "updated_at": "2024-01-15T14:00:00"
    }
  ],
  "total": 5,
  "page": 1,
  "size": 20,
  "pages": 1
}
```

---

### GET /{document_id}

**Get document details with version history**

Response (200):
```json
{
  "id": 1,
  "document_number": "SOP-2024-001",
  "title": "SOP-Quality Assurance Procedures",
  "description": "...",
  "department": "Quality Assurance",
  "status": "EFFECTIVE",
  "tags": ["SOP", "QA"],
  "owner_id": 2,
  "owner_username": "jdoe",
  "version_count": 3,
  "versions": [
    {
      "id": 1,
      "version_number": 1,
      "status": "Draft",
      "change_summary": "Initial draft",
      "created_by_username": "jdoe",
      "created_at": "2024-01-10T10:00:00"
    },
    {
      "id": 2,
      "version_number": 2,
      "status": "Effective",
      "change_summary": "Final approved version",
      "created_by_username": "jdoe",
      "created_at": "2024-01-15T14:00:00"
    }
  ]
}
```

---

### PATCH /{document_id}

**Update document metadata**

- **Status Codes:** 200 OK, 403 FORBIDDEN (not owner), 404 NOT_FOUND

---

### DELETE /{document_id}

**Soft delete document (drafts/rejected only)**

- **Status Codes:** 204 NO_CONTENT, 400 BAD_REQUEST (cannot delete published)

---

## Document Versions Endpoints

Base path: `/api/v1/documents/{document_id}/versions`

### POST / (Create Version)

**Create a new version for document**

Request:
```json
{
  "change_summary": "Updated procedures based on user feedback",
  "content": "New version content..."
}
```

---

### GET /

**List all versions of a document**

---

### GET /{version_id}

**Get specific version details**

---

### PATCH /{version_id}/approve

**Approve version (Approver role)**

Request:
```json
{
  "signature": "digital-signature-token",
  "approval_notes": "Approved for implementation"
}
```

---

### PATCH /{version_id}/reject

**Reject version**

Request:
```json
{
  "rejection_reason": "Needs more testing"
}
```

---

## Comments Endpoints

Base path: `/api/v1/documents/{document_id}/comments`

### POST /

**Add a comment to document**

Request:
```json
{
  "content": "This section needs clarification",
  "comment_type": "COMMENT",
  "parent_id": null
}
```

Response (201):
```json
{
  "id": 1,
  "document_id": 1,
  "user_id": 2,
  "user_name": "jdoe",
  "content": "This section needs clarification",
  "comment_type": "COMMENT",
  "created_at": "2024-01-15T15:30:00",
  "is_resolved": false
}
```

---

### GET /

**List all comments on a document**

Query params: `page`, `page_size`, `is_resolved`

---

### PUT /{comment_id}

**Update comment**

Request:
```json
{
  "content": "Updated comment content"
}
```

---

### DELETE /{comment_id}

**Delete comment**

- **Status Codes:** 204 NO_CONTENT

---

## Attachments Endpoints

Base path: `/api/v1/attachments`

### POST / (Upload)

**Upload file attachment**

- **Content-Type:** multipart/form-data
- **Fields:**
  - `file` (binary) — file content
  - `document_id` (int)
  - `version_id` (int, optional)

Response (201):
```json
{
  "id": 1,
  "document_id": 1,
  "file_name": "supporting_document.pdf",
  "file_size": 245678,
  "content_type": "application/pdf",
  "uploaded_by": "jdoe",
  "uploaded_at": "2024-01-15T16:00:00"
}
```

---

### GET /{attachment_id}

**Download attachment**

- **Status Codes:** 200 OK, 404 NOT_FOUND

---

### DELETE /{attachment_id}

**Delete attachment**

- **Status Codes:** 204 NO_CONTENT

---

## Audit Logs Endpoints (Admin Only)

Base path: `/api/v1/audit-logs` | **Requires:** DMS_Admin

### GET /

**Get audit logs with filtering**

Query parameters:
- `page`, `page_size`
- `user_id` (int, optional)
- `action` (string, optional) — e.g., "USER_CREATED", "DOCUMENT_UPDATED"
- `entity_type` (string, optional) — e.g., "User", "Document"
- `start_date` (ISO string, optional)
- `end_date` (ISO string, optional)

Response (200):
```json
{
  "logs": [
    {
      "id": 1,
      "timestamp": "2024-01-15T10:30:00",
      "user_id": 1,
      "username": "admin",
      "action": "USER_CREATED",
      "entity_type": "User",
      "entity_id": 5,
      "description": "Created user 'jdoe' with roles: Reviewer, Approver",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "details": {
        "new_username": "jdoe",
        "roles": ["Reviewer", "Approver"]
      }
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 50
}
```

---

### GET /actions

**Get list of available action types**

Response (200):
```json
{
  "actions": [
    "USER_CREATED",
    "USER_UPDATED",
    "USER_ACTIVATED",
    "USER_DEACTIVATED",
    "PASSWORD_RESET",
    "USER_LOGIN",
    "LOGIN_FAILED",
    "DOCUMENT_CREATED",
    "DOCUMENT_UPDATED",
    "DOCUMENT_DELETED",
    "VERSION_CREATED",
    "VERSION_APPROVED",
    "VERSION_REJECTED",
    "COMMENT_ADDED",
    "ATTACHMENT_UPLOADED"
  ]
}
```

---

### GET /entity-types

**Get list of available entity types**

Response (200):
```json
{
  "entity_types": [
    "User",
    "Document",
    "DocumentVersion",
    "Comment",
    "Attachment",
    "System"
  ]
}
```

---

## Templates Endpoints

Base path: `/api/v1/templates`

### POST /

**Create document template**

Request:
```json
{
  "title": "Standard SOP Template",
  "description": "Generic template for SOPs",
  "category": "SOP",
  "content": "<html>...</html>"
}
```

---

### GET /

**List templates**

---

### GET /{template_id}

**Get template details**

---

---

## Status Code Reference

| Code | Meaning |
|------|---------|
| 200 | OK — Request successful |
| 201 | Created — Resource created successfully |
| 204 | No Content — Successful deletion |
| 400 | Bad Request — Validation or logical error |
| 401 | Unauthorized — Authentication required or failed |
| 403 | Forbidden — Authenticated but insufficient privileges |
| 404 | Not Found — Resource not found |
| 409 | Conflict — Session conflict or duplicate resource |
| 500 | Internal Server Error — Server error |

---

## Error Response Format

All error responses follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Or for validation errors:

```json
{
  "detail": [
    {
      "loc": ["body", "password"],
      "msg": "ensure this value has at least 8 characters",
      "type": "value_error"
    }
  ]
}
```

---

## Authentication

All protected endpoints require the `Authorization` header:

```
Authorization: Bearer <access_token>
```

Where `<access_token>` is the JWT obtained from `/api/v1/auth/login`.

---

**Version:** 1.0.0 | **Last Updated:** 2024
