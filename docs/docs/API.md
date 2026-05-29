# API Reference (selected endpoints)

This file documents key API endpoints exposed by the backend (FastAPI). The base prefix for the API is `/api/v1`.

## Authentication

### POST /api/v1/auth/login
- Description: Authenticate user and obtain JWT access token. Supports single-session enforcement.
- Request (application/json):

```json
{
  "username": "admin",
  "password": "Admin@123456",
  "force_login": false
}
```
- Responses:
  - 200: Token object (access_token, token_type, user info)
  - 401: Invalid credentials
  - 409: Session conflict (when another session is active)

Example success response:

```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": { "id": 1, "username": "admin", "roles": ["DMS_Admin"] }
}
```

### GET /api/v1/auth/me
- Description: Get profile of current authenticated user.
- Authentication: Bearer token required
- Responses: 200: User profile

### POST /api/v1/auth/logout
- Description: Clears current active session
- Responses: 200: {"message":"Successfully logged out"}

### GET /api/v1/auth/validate-session
- Description: Validate that the client's token is still the active session.
- Responses: {"valid": true|false, "reason": "..."}

## User Management (Admin)

All endpoints under `/api/v1/users` require admin privileges (see `require_admin` dependency).

### POST /api/v1/users
- Create a new user
- Request: `UserCreate` schema (username, email, password, role_ids...)
- Responses: 201 Created: User object

### GET /api/v1/users
- List users with pagination and filters
- Query params: `page`, `page_size`, `role`, `is_active`, `search`
- Responses: 200: `UserListResponse`

### GET /api/v1/users/{user_id}
- Get user by id (200) or 404 if not found

### PUT /api/v1/users/{user_id}
- Update a user (Admin only); returns updated user

### PATCH /api/v1/users/{user_id}/activate
### PATCH /api/v1/users/{user_id}/deactivate
- Activate or deactivate user accounts

### POST /api/v1/users/{user_id}/reset-password
- Admin resets a user's password; returns a message and `requires_password_change` flag

### DELETE /api/v1/users/{user_id}
- Delete a user (204 No Content)

## Document Management

Base path: `/api/v1/documents`

### POST /api/v1/documents
- Create a document
- Request: `DocumentCreate` (title, department, description, owner_id optional)
- Responses:
  - 201 Created: `DocumentResponse`
  - 403 Forbidden: insufficient privileges

### GET /api/v1/documents
- List/search documents. Query params include `title`, `document_number`, `department`, `status`, `owner_id`, `show_all_statuses`, `page`, `page_size`.

### GET /api/v1/documents/{document_id}
- Get document metadata and version history (200) or 404

### PATCH /api/v1/documents/{document_id}
- Update document metadata (owner change requires admin)

### DELETE /api/v1/documents/{document_id}
- Soft delete a document (only drafts or rejected allowed)

## Comments, Attachments, Versions, Templates

The API provides endpoints for comments, attachments, document versions, templates, template-builder, export, print control, and AI insights under the `/api/v1` router. Use the auto-generated Swagger UI at `/api/docs` for a full interactive listing.

## Status Codes (common)

- 200 OK — Successful GET/POST (non-creation)
- 201 Created — Resource created
- 204 No Content — Successful delete
- 400 Bad Request — Validation or logical error
- 401 Unauthorized — Authentication missing or invalid
- 403 Forbidden — Authenticated but lacks privileges
- 404 Not Found — Resource missing
- 409 Conflict — Session conflict or duplicate resource
# API Documentation

Complete API reference for Pharma DMS Phase 1: User Management

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All endpoints except `/auth/login` require authentication via JWT Bearer token.

**Header Format:**
```
Authorization: Bearer <access_token>
```

---

## Authentication Endpoints

### Login

**POST** `/auth/login`

Authenticate user and receive JWT access token.

**Request Body:**
```json
{
  "username": "admin",
  "password": "Admin@123456"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@pharma-dms.com",
    "full_name": "System Administrator",
    "roles": ["DMS_Admin"],
    "is_active": true
  },
  "requires_password_change": false
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid credentials
- `403 Forbidden`: Account inactive

---

### Get Current User Profile

**GET** `/auth/me`

Get currently authenticated user's profile.

**Response:** `200 OK`
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@pharma-dms.com",
  "full_name": "System Administrator",
  "roles": ["DMS_Admin"],
  "is_active": true
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid or expired token

---

### Logout

**POST** `/auth/logout`

Logout current user (for audit logging; token invalidation handled client-side).

**Response:** `200 OK`
```json
{
  "message": "Successfully logged out"
}
```

---

## User Management Endpoints

**Note:** All user management endpoints require `DMS_Admin` role.

### Create User

**POST** `/users`

Create a new user account with assigned roles.

**Request Body:**
```json
{
  "username": "author1",
  "email": "author1@pharma.com",
  "password": "Author@123",
  "first_name": "John",
  "last_name": "Doe",
  "department": "Quality Assurance",
  "phone": "+1-555-0123",
  "role_ids": [1],
  "is_active": true
}
```

**Field Validation:**
- `username`: 3-100 characters, unique
- `email`: Valid email format, unique
- `password`: Min 8 chars, 1 uppercase, 1 lowercase, 1 digit
- `first_name`: 1-100 characters
- `last_name`: 1-100 characters
- `department`: Optional, max 100 characters
- `phone`: Optional, max 20 characters
- `role_ids`: Array of valid role IDs (min 1)

**Response:** `201 Created`
```json
{
  "id": 2,
  "username": "author1",
  "email": "author1@pharma.com",
  "first_name": "John",
  "last_name": "Doe",
  "department": "Quality Assurance",
  "phone": "+1-555-0123",
  "is_active": true,
  "is_temp_password": false,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00",
  "last_login": null,
  "roles": [
    {
      "id": 1,
      "name": "Author",
      "description": "Can create, edit, and submit documents for review"
    }
  ]
}
```

**Error Responses:**
- `400 Bad Request`: Validation error or duplicate username/email
- `403 Forbidden`: Not admin

---

### List Users

**GET** `/users`

Get paginated list of users with optional filters.

**Query Parameters:**
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 50, max: 100)
- `role`: Filter by role name (e.g., "Author")
- `is_active`: Filter by status (true/false)
- `search`: Search by username, email, or name

**Example Request:**
```
GET /users?page=1&page_size=20&role=Author&is_active=true&search=john
```

**Response:** `200 OK`
```json
{
  "users": [
    {
      "id": 2,
      "username": "author1",
      "email": "author1@pharma.com",
      "first_name": "John",
      "last_name": "Doe",
      "department": "Quality Assurance",
      "phone": "+1-555-0123",
      "is_active": true,
      "is_temp_password": false,
      "created_at": "2024-01-15T10:30:00",
      "updated_at": "2024-01-15T10:30:00",
      "last_login": "2024-01-15T14:20:00",
      "roles": [
        {
          "id": 1,
          "name": "Author",
          "description": "Can create, edit, and submit documents for review"
        }
      ]
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

**Error Responses:**
- `403 Forbidden`: Not admin

---

### Get User Details

**GET** `/users/{user_id}`

Get details for a specific user.

**Response:** `200 OK`
```json
{
  "id": 2,
  "username": "author1",
  "email": "author1@pharma.com",
  "first_name": "John",
  "last_name": "Doe",
  "department": "Quality Assurance",
  "phone": "+1-555-0123",
  "is_active": true,
  "is_temp_password": false,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00",
  "last_login": "2024-01-15T14:20:00",
  "roles": [
    {
      "id": 1,
      "name": "Author",
      "description": "Can create, edit, and submit documents for review"
    }
  ]
}
```

**Error Responses:**
- `404 Not Found`: User not found
- `403 Forbidden`: Not admin

---

### Update User

**PUT** `/users/{user_id}`

Update user information and/or roles.

**Request Body:** (all fields optional)
```json
{
  "email": "john.doe@pharma.com",
  "first_name": "Jonathan",
  "last_name": "Doe",
  "department": "QA Department",
  "phone": "+1-555-0124",
  "role_ids": [1, 2],
  "is_active": true
}
```

**Response:** `200 OK`
```json
{
  "id": 2,
  "username": "author1",
  "email": "john.doe@pharma.com",
  "first_name": "Jonathan",
  "last_name": "Doe",
  "department": "QA Department",
  "phone": "+1-555-0124",
  "is_active": true,
  "is_temp_password": false,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T15:45:00",
  "last_login": "2024-01-15T14:20:00",
  "roles": [
    {
      "id": 1,
      "name": "Author",
      "description": "Can create, edit, and submit documents for review"
    },
    {
      "id": 2,
      "name": "Reviewer",
      "description": "Can review documents and provide comments/suggestions"
    }
  ]
}
```

**Error Responses:**
- `404 Not Found`: User not found
- `400 Bad Request`: Validation error or duplicate email
- `403 Forbidden`: Not admin

---

### Activate User

**PATCH** `/users/{user_id}/activate`

Activate an inactive user account.

**Response:** `200 OK`
```json
{
  "id": 2,
  "username": "author1",
  ...
  "is_active": true
}
```

**Error Responses:**
- `404 Not Found`: User not found
- `400 Bad Request`: User already active
- `403 Forbidden`: Not admin

---

### Deactivate User

**PATCH** `/users/{user_id}/deactivate`

Deactivate an active user account.

**Response:** `200 OK`
```json
{
  "id": 2,
  "username": "author1",
  ...
  "is_active": false
}
```

**Error Responses:**
- `404 Not Found`: User not found
- `400 Bad Request`: User already inactive or attempting self-deactivation
- `403 Forbidden`: Not admin

---

### Reset User Password

**POST** `/users/{user_id}/reset-password`

Reset a user's password (admin only).

**Request Body:**
```json
{
  "new_password": "NewPassword@123",
  "force_change": true
}
```

**Response:** `200 OK`
```json
{
  "message": "Password reset successfully",
  "requires_password_change": true
}
```

**Error Responses:**
- `404 Not Found`: User not found
- `400 Bad Request`: Password validation error
- `403 Forbidden`: Not admin

---

### Delete User

**DELETE** `/users/{user_id}`

Permanently delete a user account.

**⚠️ Warning:** Consider using deactivation instead for compliance.

**Response:** `204 No Content`

**Error Responses:**
- `404 Not Found`: User not found
- `400 Bad Request`: Attempting self-deletion
- `403 Forbidden`: Not admin

---

## Audit Log Endpoints

**Note:** All audit log endpoints require `DMS_Admin` role.

### Get Audit Logs

**GET** `/audit-logs`

Get paginated audit logs with filtering.

**Query Parameters:**
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 50, max: 100)
- `action`: Filter by action type (e.g., "USER_CREATED")
- `entity_type`: Filter by entity type (e.g., "User")
- `user_id`: Filter by user ID
- `username`: Filter by username (partial match)
- `start_date`: Filter by start date (ISO 8601)
- `end_date`: Filter by end date (ISO 8601)

**Example Request:**
```
GET /audit-logs?action=USER_CREATED&start_date=2024-01-01T00:00:00&page=1&page_size=50
```

**Response:** `200 OK`
```json
{
  "logs": [
    {
      "id": 1,
      "user_id": 1,
      "username": "admin",
      "action": "USER_CREATED",
      "entity_type": "User",
      "entity_id": 2,
      "description": "Created user 'author1' with roles: Author",
      "details": {
        "new_username": "author1",
        "roles": ["Author"]
      },
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "timestamp": "2024-01-15T10:30:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 50
}
```

**Error Responses:**
- `403 Forbidden`: Not admin

---

### Get Available Actions

**GET** `/audit-logs/actions`

Get list of all action types in audit log.

**Response:** `200 OK`
```json
{
  "actions": [
    "USER_CREATED",
    "USER_UPDATED",
    "USER_ACTIVATED",
    "USER_DEACTIVATED",
    "USER_DELETED",
    "PASSWORD_RESET",
    "USER_LOGIN",
    "LOGIN_FAILED"
  ]
}
```

---

### Get Available Entity Types

**GET** `/audit-logs/entity-types`

Get list of all entity types in audit log.

**Response:** `200 OK`
```json
{
  "entity_types": [
    "User"
  ]
}
```

---

## Roles

The system defines four roles:

### 1. Author (ID: 1)
**Description:** Can create, edit, and submit documents for review

**Permissions:**
- `document.create`
- `document.read`
- `document.update`
- `document.submit`
- `document.withdraw`

### 2. Reviewer (ID: 2)
**Description:** Can review documents and provide comments/suggestions

**Permissions:**
- `document.read`
- `document.review`
- `document.comment`
- `document.suggest_changes`

### 3. Approver (ID: 3)
**Description:** Can approve or reject documents with e-signature

**Permissions:**
- `document.read`
- `document.approve`
- `document.reject`
- `document.sign`

### 4. DMS_Admin (ID: 4)
**Description:** Full system administrator

**Permissions:**
- All user management permissions
- All document permissions
- `user.create`, `user.read`, `user.update`, `user.delete`
- `user.activate`, `user.deactivate`, `user.reset_password`
- `role.assign`
- `audit.view`

---

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message here"
}
```

### Common Status Codes

- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `204 No Content`: Successful deletion
- `400 Bad Request`: Validation error or invalid request
- `401 Unauthorized`: Authentication required or invalid token
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Request validation failed
- `500 Internal Server Error`: Server error

---

## Rate Limiting

**Status:** Not implemented in Phase 1

Consider implementing rate limiting in production:
- Login endpoint: 5 requests per minute
- Password reset: 3 requests per hour
- API endpoints: 100 requests per minute

---

## Pagination

All list endpoints support pagination with:

- `page`: Page number (starts at 1)
- `page_size`: Items per page (default and max vary by endpoint)

Response includes:
- `total`: Total number of items
- `page`: Current page number
- `page_size`: Items per page

---

## OpenAPI Documentation

Interactive API documentation available at:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
- OpenAPI JSON: http://localhost:8000/api/openapi.json

---

## Testing with cURL

### Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin@123456"}'
```

### Create User
```bash
TOKEN="your_access_token_here"

curl -X POST "http://localhost:8000/api/v1/users" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "author1",
    "email": "author1@pharma.com",
    "password": "Author@123",
    "first_name": "John",
    "last_name": "Doe",
    "department": "Quality",
    "role_ids": [1]
  }'
```

### List Users
```bash
curl -X GET "http://localhost:8000/api/v1/users?page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN"
```

### Get Audit Logs
```bash
curl -X GET "http://localhost:8000/api/v1/audit-logs?page=1&page_size=50" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Security Considerations

1. **Always use HTTPS in production**
2. **Keep JWT tokens secure** (store in httpOnly cookies or secure storage)
3. **Implement token refresh** for long-lived sessions
4. **Rate limit sensitive endpoints** (login, password reset)
5. **Monitor audit logs** for suspicious activity
6. **Rotate SECRET_KEY** periodically
7. **Use strong passwords** meeting policy requirements
8. **Implement IP whitelisting** if applicable


