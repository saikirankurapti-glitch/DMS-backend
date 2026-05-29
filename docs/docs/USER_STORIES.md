# User Stories - Phase 1: User Management

Complete mapping of User Requirements Specifications (URS) to User Stories with implementation status.

## URS-1 — System shall allow Admin to create user accounts ✅

### US-1.1 ✅
**As an Admin, I want to create new users so that they can access the DMS system.**

**Implementation:**
- Endpoint: `POST /api/v1/users`
- Validates username and email uniqueness
- Enforces password strength requirements
- Records creation in audit log
- Returns created user with assigned ID

**Acceptance Criteria:**
- ✅ Admin can create user with username, email, password, name, department
- ✅ System validates all required fields
- ✅ System prevents duplicate usernames
- ✅ System prevents duplicate emails
- ✅ Password is hashed before storage
- ✅ Creation is logged in audit trail

### US-1.2 ✅
**As an Admin, I want to assign one or more roles (Author/Reviewer/Approver/Admin) during user creation so they get correct access.**

**Implementation:**
- Endpoint: `POST /api/v1/users`
- Field: `role_ids` (list of role IDs)
- Validates all role IDs exist
- Creates many-to-many relationships
- Supports multiple roles per user

**Acceptance Criteria:**
- ✅ Admin can assign one or more roles during creation
- ✅ System validates role IDs exist
- ✅ System creates user-role associations
- ✅ Role assignments are reflected immediately
- ✅ Role assignments are logged in audit trail

---

## URS-2 — System shall allow Admin to view a list of all users ✅

### US-2.1 ✅
**As an Admin, I want to see all users so that I can manage them easily.**

**Implementation:**
- Endpoint: `GET /api/v1/users`
- Returns paginated list of users
- Shows user details including roles
- Default page size: 50 users
- Maximum page size: 100 users

**Acceptance Criteria:**
- ✅ Admin can view list of all users
- ✅ List shows username, email, name, roles, status
- ✅ List is paginated for performance
- ✅ System returns total count for pagination

### US-2.2 ✅
**As an Admin, I want to filter users by role/status so that I can find the right user quickly.**

**Implementation:**
- Endpoint: `GET /api/v1/users`
- Query parameters:
  - `role`: Filter by role name
  - `is_active`: Filter by active status (true/false)
  - `search`: Search by username, email, or name
  - `page`: Page number
  - `page_size`: Items per page

**Acceptance Criteria:**
- ✅ Admin can filter by role
- ✅ Admin can filter by active/inactive status
- ✅ Admin can search by username, email, or name
- ✅ Filters can be combined
- ✅ Results maintain pagination

---

## URS-3 — System shall allow Admin to edit/update user details ✅

### US-3.1 ✅
**As an Admin, I want to update user information (name, email, department, role) so that user profiles stay current.**

**Implementation:**
- Endpoint: `PUT /api/v1/users/{user_id}`
- Supports partial updates (optional fields)
- Validates email uniqueness on change
- Tracks changes for audit log

**Acceptance Criteria:**
- ✅ Admin can update email, first name, last name, department, phone
- ✅ System validates email uniqueness
- ✅ System prevents invalid email formats
- ✅ Changes are logged in audit trail with old/new values
- ✅ Updated user information is returned

### US-3.2 ✅
**As an Admin, I want to modify a user's assigned roles so that I can change their responsibilities.**

**Implementation:**
- Endpoint: `PUT /api/v1/users/{user_id}`
- Field: `role_ids` (list of role IDs)
- Replaces existing roles with new ones
- Validates all role IDs exist
- Logs role changes

**Acceptance Criteria:**
- ✅ Admin can update user's roles
- ✅ System validates role IDs exist
- ✅ Old roles are replaced with new roles
- ✅ Role changes are logged with old/new values
- ✅ Changes take effect immediately

---

## URS-4 — System shall allow Admin to deactivate/activate user accounts ✅

### US-4.1 ✅
**As an Admin, I want to deactivate a user so that they cannot log in anymore.**

**Implementation:**
- Endpoint: `PATCH /api/v1/users/{user_id}/deactivate`
- Sets `is_active` to false
- Prevents admin from deactivating themselves
- Logs deactivation action

**Acceptance Criteria:**
- ✅ Admin can deactivate user accounts
- ✅ Deactivated users cannot log in
- ✅ Admin cannot deactivate their own account
- ✅ Deactivation is logged in audit trail
- ✅ User data is preserved (not deleted)

### US-4.2 ✅
**As an Admin, I want to reactivate a user if needed so they can resume workflow activities.**

**Implementation:**
- Endpoint: `PATCH /api/v1/users/{user_id}/activate`
- Sets `is_active` to true
- Logs activation action
- User can log in immediately after activation

**Acceptance Criteria:**
- ✅ Admin can reactivate inactive users
- ✅ Activated users can log in immediately
- ✅ Activation is logged in audit trail
- ✅ All user data and roles are preserved

---

## URS-5 — System shall allow Users to log in securely using password authentication ✅

### US-5.1 ✅
**As a User, I want to log in with my username and password so that I can access the system.**

**Implementation:**
- Endpoint: `POST /api/v1/auth/login`
- Accepts username and password
- Verifies password using bcrypt
- Returns JWT access token
- Updates last login timestamp
- Logs successful login

**Acceptance Criteria:**
- ✅ User can log in with valid credentials
- ✅ System returns JWT access token
- ✅ Token includes user information and roles
- ✅ Last login timestamp is updated
- ✅ Login is logged in audit trail

### US-5.2 ✅
**As a User, I want to receive an error if my credentials are invalid so I know something is wrong.**

**Implementation:**
- Returns HTTP 401 for invalid credentials
- Generic error message (security best practice)
- Logs failed login attempt with reason
- Does not reveal if username or password is wrong

**Acceptance Criteria:**
- ✅ Invalid username returns error
- ✅ Invalid password returns error
- ✅ Error message doesn't reveal which is wrong
- ✅ Failed attempts are logged
- ✅ Inactive accounts cannot log in

---

## URS-6 — System shall enforce Role-Based Access Control (RBAC) ✅

### US-6.1 ✅
**As a System, I want to ensure only Admin users can manage user accounts so that unauthorized access is prevented.**

**Implementation:**
- Dependency: `require_admin()`
- Applied to all user management endpoints
- Validates user has DMS_Admin role
- Returns HTTP 403 if not authorized

**Acceptance Criteria:**
- ✅ Only DMS_Admin can access user management endpoints
- ✅ Non-admin users receive 403 Forbidden
- ✅ RBAC is enforced at API level
- ✅ Authorization failures are logged

### US-6.2 ✅
**As an Author/Reviewer/Approver, I want to access only the features allowed for my role so that I operate within my permissions.**

**Implementation:**
- Role capabilities defined in `core/rbac.py`
- Permission checks via `has_permission()`
- Each role has specific capabilities
- Extensible for future document permissions

**Acceptance Criteria:**
- ✅ Each role has defined capabilities
- ✅ Users can only access permitted features
- ✅ Permission denied returns 403 Forbidden
- ✅ System ready for document-level permissions (Phase 2)

---

## URS-7 — System shall hash & securely store user passwords ✅

### US-7.1 ✅
**As a System, I want to store passwords as hashed values so that user credentials remain secure.**

**Implementation:**
- Uses bcrypt for password hashing
- Salt automatically generated per password
- Password never stored in plain text
- Implemented in `core/security.py`

**Acceptance Criteria:**
- ✅ Passwords are hashed before storage
- ✅ Bcrypt is used with automatic salting
- ✅ Plain text passwords never stored
- ✅ Hash verification works correctly

### US-7.2 ✅
**As an Admin, I want to ensure no one (including Admins) can view user passwords.**

**Implementation:**
- Password field excluded from all API responses
- Only hashed_password stored in database
- No password retrieval endpoints
- Admin can only reset, not view passwords

**Acceptance Criteria:**
- ✅ Passwords never returned in API responses
- ✅ No endpoint to retrieve passwords
- ✅ Admin can reset but not view passwords
- ✅ Password hashes not exposed in logs

---

## URS-8 — System shall allow only Admin to reset user passwords ✅

### US-8.1 ✅
**As an Admin, I want to reset a user's password so that I can help them regain access when required.**

**Implementation:**
- Endpoint: `POST /api/v1/users/{user_id}/reset-password`
- Admin-only endpoint
- Accepts new password
- Validates password strength
- Option to force password change on next login

**Acceptance Criteria:**
- ✅ Admin can reset any user's password
- ✅ New password must meet strength requirements
- ✅ Password is hashed before storage
- ✅ User can log in with new password immediately

### US-8.2 ✅
**As an Admin, I want password reset actions to be fully logged in the audit trail so that compliance is maintained.**

**Implementation:**
- Action logged as "PASSWORD_RESET"
- Records admin who performed reset
- Records target user
- Records whether force_change was enabled
- Includes timestamp, IP, user agent

**Acceptance Criteria:**
- ✅ Password resets are logged
- ✅ Log includes admin and target user
- ✅ Log includes force_change flag
- ✅ Log includes timestamp and context
- ✅ Audit trail is immutable

### US-8.3 ✅
**As an Admin, I want the system to enforce temporary/reset passwords (force first login password change) so the user can set a unique and secure password.**

**Implementation:**
- Field: `is_temp_password` (boolean)
- Set to true when force_change enabled
- Returned in login response as `requires_password_change`
- Frontend should prompt for password change

**Acceptance Criteria:**
- ✅ Admin can force password change on reset
- ✅ Flag is stored with user
- ✅ Flag is returned in login response
- ✅ System ready for password change enforcement

---

## URS-9 — System shall maintain an audit log for user-related actions ✅

### US-9.1 ✅
**As a Compliance Officer, I want to see audit logs for actions like user creation, deactivation, role change so that I can verify system integrity.**

**Implementation:**
- Endpoint: `GET /api/v1/audit-logs`
- Returns paginated audit logs
- Supports filtering by:
  - Action type
  - Entity type
  - User ID
  - Username
  - Date range
- Ordered by timestamp (newest first)

**Acceptance Criteria:**
- ✅ All user actions are logged
- ✅ Logs include: user, action, entity, timestamp, details
- ✅ Logs are searchable and filterable
- ✅ Logs are immutable (no updates/deletes)
- ✅ IP address and user agent captured

### US-9.2 ✅
**As an Admin, I want changes I make to be logged so that we maintain regulatory compliance.**

**Implementation:**
- Automatic logging for all admin actions
- Logged actions:
  - USER_CREATED
  - USER_UPDATED
  - USER_ACTIVATED
  - USER_DEACTIVATED
  - USER_DELETED
  - PASSWORD_RESET
  - USER_LOGIN
  - LOGIN_FAILED
- Each log includes structured details (JSON)

**Acceptance Criteria:**
- ✅ All admin actions are logged automatically
- ✅ Logs include old/new values for updates
- ✅ Logs include structured details
- ✅ Logs support compliance reporting
- ✅ Logs are tamper-evident

---

## URS-10 — System shall provide user profile details ✅

### US-10.1 ✅
**As a User, I want to see my own profile so that I can confirm my account details.**

**Implementation:**
- Endpoint: `GET /api/v1/auth/me`
- Returns current user's profile
- Includes roles and status
- Does not require admin privileges

**Acceptance Criteria:**
- ✅ User can view own profile
- ✅ Profile includes all relevant information
- ✅ Password is not included in response
- ✅ Roles are included
- ✅ Active status is shown

### US-10.2 ✅
**As an Admin, I want to view a user's profile including roles and active status so that I understand their permissions and workflow involvement.**

**Implementation:**
- Endpoint: `GET /api/v1/users/{user_id}`
- Admin-only endpoint
- Returns complete user profile
- Includes all roles with descriptions
- Shows active status and timestamps

**Acceptance Criteria:**
- ✅ Admin can view any user's profile
- ✅ Profile includes all user information
- ✅ Profile includes all assigned roles
- ✅ Profile includes active status
- ✅ Profile includes timestamps (created, updated, last login)

---

## Summary

**Total User Stories: 20**
**Implemented: 20 (100%)**
**Status: Phase 1 Complete ✅**

All user requirements for Phase 1 have been fully implemented and tested. The system is production-ready for user management and RBAC functionality.

### Coverage by URS

- URS-1 (User Creation): ✅ 2/2 stories
- URS-2 (User Listing): ✅ 2/2 stories
- URS-3 (User Updates): ✅ 2/2 stories
- URS-4 (User Activation): ✅ 2/2 stories
- URS-5 (User Login): ✅ 2/2 stories
- URS-6 (RBAC): ✅ 2/2 stories
- URS-7 (Password Security): ✅ 2/2 stories
- URS-8 (Password Reset): ✅ 3/3 stories
- URS-9 (Audit Logging): ✅ 2/2 stories
- URS-10 (User Profiles): ✅ 2/2 stories

### Next Phase

Phase 2 will implement document management with the following URS:
- Document creation and editing
- Document versioning
- Document metadata
- File upload and storage
- Document lifecycle states (Draft → Review → Approval → Published → Archived)


