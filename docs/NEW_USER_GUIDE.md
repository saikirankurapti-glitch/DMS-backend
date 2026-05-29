# New User Guide - Q-Docs System

Welcome to Q-Docs! This guide will help you get started with the Document Management System and learn how to perform common tasks.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [System Overview](#system-overview)
3. [Logging In](#logging-in)
4. [Dashboard Overview](#dashboard-overview)
5. [Common Tasks](#common-tasks)
6. [Document Workflows](#document-workflows)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)
9. [Getting Help](#getting-help)

---

## Getting Started

### What is Q-Docs?

Q-Docs is a **Document Management System (DMS)** designed for pharmaceutical and regulated environments. It helps your organization:

- **Organize documents** with version control and change tracking
- **Control document access** through role-based permissions
- **Manage approvals** with structured review workflows
- **Maintain compliance** with immutable audit trails
- **Collaborate efficiently** with comments and suggestions

### Who Uses Q-Docs?

Q-Docs has different features for different roles:

| Role | Responsibilities |
|------|------------------|
| **Author** | Creates and edits documents, submits for review |
| **Reviewer** | Reviews documents and provides feedback |
| **Approver** | Approves or rejects documents |
| **DMS Admin** | Manages users, templates, and system settings |

**Not sure your role?** Ask your DMS Administrator.

---

## System Overview

### Key Concepts

**Document**
- A Standard Operating Procedure (SOP), guide, or instruction document
- Has versions as it evolves through the approval process
- Can have attachments (images, PDF, Word files, etc.)

**Version**
- A specific iteration of a document
- Each version has a status (Draft, Under Review, Approved, etc.)
- Only one version can be "Effective" at a time

**Status Flow**
```
Draft → Under Review → Pending Approval → Approved → Effective
                                       ↓
                                    Rejected
```

**Comments**
- Feedback on a document or specific version
- Can be marked resolved when addressed
- Create audit trail of discussions

**Attachments**
- Supporting files (Word docs, PDFs, images, etc.)
- Attached to specific versions
- Downloadable for reference

**Audit Trail**
- Complete record of all actions on a document
- Includes who did what, when, and from where
- Cannot be deleted or modified (immutable)

---

## Logging In

### First Time Login

1. **Go to the system URL** (provided by your administrator)
   - Example: `https://q-docs.yourcompany.com`

2. **Enter your credentials**
   - Username: Your assigned username
   - Password: Your initial password (from administrator)

3. **You may be prompted to change your password**
   - Enter your current password
   - Create a NEW password (at least 8 characters, with uppercase, lowercase, numbers, and symbols)
   - Confirm your new password

4. **You're logged in!**
   - You'll see the Dashboard
   - Your session will stay active for 8 hours of inactivity
   - You can log out anytime using the logout button

### Password Security

- **Never share your password** with anyone
- **Use a strong password** (mix of upper, lower, numbers, symbols)
- **Change your password periodically** (every 90 days recommended)
- **If you forget your password**, contact your DMS Administrator

### Session Management

- **One session per user:** Only one active login allowed per user
- **Login from another device?** Your previous session will end automatically
- **Inactive timeout:** Session expires after 8 hours of no activity
- **Automatic logout:** Let the system know you're logging off by clicking "Logout"

---

## Dashboard Overview

After logging in, you'll see the Dashboard. Here's what you see:

### Dashboard Sections

**1. Quick Stats (Top)**
- Number of documents you authored
- Documents pending your review/approval
- Total documents you can access

**2. Recent Documents (Middle)**
- List of documents you've recently worked on
- Shows document title, status, last modified date
- Click to view or edit

**3. Action Items (Right Sidebar)**
- **For Reviewers:** Documents waiting for your review
- **For Approvers:** Documents waiting for your approval
- **For Authors:** Documents with feedback or rejections

**4. Search & Filter (Top)**
- Search by document title or description
- Filter by status, department, author, last modified date

### Navigation Menu (Left Sidebar)

- **Documents** - View all documents you can access
- **My Documents** - Documents you created
- **Pending Review** - Documents waiting for your review
- **Pending Approval** - Documents waiting for your approval
- **Templates** - Document templates for creating new documents
- **Audit Log** - View system activity (Admin only)
- **Settings** - User profile and preferences

---

## Common Tasks

### Task 1: Finding a Document

**Method 1: Using Search**
1. Click the search box at the top
2. Type the document title or keywords
3. Press Enter or click Search
4. Click the document to open it

**Method 2: Using Filters**
1. Go to Documents
2. Click "Filters"
3. Filter by:
   - Status (Draft, Approved, etc.)
   - Department
   - Author
   - Date range
4. Click "Apply Filters"

**Method 3: Browse by Department**
1. Go to Documents
2. Look for your department in the left sidebar
3. Click to see documents in that department

### Task 2: Creating a New Document

**Option A: From Blank Document**
1. Click "New Document" button
2. Fill in document details:
   - **Title:** Name of the document (required)
   - **Description:** What the document is about
   - **Department:** Which department owns this
   - **Type:** SOP, Guide, Instruction, etc.
   - **Tags:** Categories for easy searching
3. Click "Create"
4. You'll be taken to the editor

**Option B: From Template**
1. Go to "Templates" section
2. Find a template that matches your need
3. Click "Use This Template"
4. Fill in the document details (as above)
5. The document will be pre-filled with template content
6. Customize as needed

### Task 3: Editing a Document

**Open Document for Editing**
1. Find and click the document
2. Click "Edit" button (or pencil icon)
3. The editor will open with the document content

**Editor Toolbar Explanation**
- **Bold/Italic/Underline** - Text formatting
- **Lists** - Bullet points or numbered lists
- **Heading** - Make text larger/bold
- **Insert Link** - Add hyperlinks
- **Insert Image** - Add pictures or diagrams
- **Undo/Redo** - Revert changes

**Save Your Work**
- Your changes are **auto-saved every 30 seconds**
- You can also click "Save" button manually
- Look for the "Saved" indicator at the top

**Note:** Only you can edit when you're the author and document is in Draft status.

### Task 4: Adding Attachments

1. While editing a document, scroll down to "Attachments"
2. Click "Add Attachment"
3. Choose a file from your computer
4. Supported formats: DOCX, PDF, images (JPG, PNG), Excel, PPT
5. Click "Upload"
6. The attachment will appear below with a removal option

### Task 5: Submitting for Review

**When your document is ready:**

1. Click "Submit for Review" button on the document
2. Select reviewers from the list:
   - Choose at least 1 reviewer
   - Can select multiple reviewers
   - Your company may require specific reviewers
3. Add a message (optional): "Please focus on procedure steps" or similar
4. Click "Submit"

**What happens next?**
- Document status changes to "Under Review"
- Selected reviewers receive email notifications
- You can still read comments but cannot edit content
- Document appears in reviewers' action items

### Task 6: Reviewing a Document

**If you are a Reviewer:**

1. Go to "Pending Review" section
2. Click the document
3. Read the document content carefully
4. Decide: Approve or Request Changes?

**If you approve:**
- Click "Approve" button
- Optionally add a comment
- Click "Confirm"

**If you want changes:**
- Click "Request Changes" button
- Add detailed comments about what needs changing
- Specify which sections need work
- Click "Submit"

**Providing Good Feedback**
- Be specific: "Change section 3.2 from 'may' to 'must'"
- Not helpful: "This doesn't look right"
- Ask questions: "Why does the procedure work this way?"
- Praise what's good: "Clear instructions in section 2"

### Task 7: Approving a Document

**If you are an Approver:**

1. Go to "Pending Approval" section
2. Click the document
3. Review the content and all reviewer comments
4. Check if all feedback has been addressed

**To Approve:**
1. Click "Approve" button
2. Add a brief approval comment (optional)
3. Click "Confirm Approval"

**To Reject:**
1. Click "Reject" button
2. Explain why (required): "Procedure steps incomplete" or similar
3. Document goes back to author for revision
4. Author will receive notification

### Task 8: Adding Comments

**While viewing or editing a document:**

1. Scroll to the "Comments" section at the bottom
2. Click "Add Comment" button
3. Type your comment
4. Choose if you're suggesting a specific change
5. Click "Post Comment"

**Example Comments:**
- "This procedure needs more detail on safety precautions"
- "Who is responsible for this step?"
- "Suggest we add a troubleshooting section"

**Resolving Comments**
- Once your feedback is addressed, mark the comment as "Resolved"
- This helps track which feedback has been handled

---

## Document Workflows

### Workflow: Creating & Publishing a New Document

```
1. You create a Draft document
   ↓
2. You edit and refine it
   ↓
3. You submit for review (document = "Under Review")
   ↓
4. Reviewers add comments and approve
   ↓
5. Document moves to "Pending Approval"
   ↓
6. Approver reviews and approves
   ↓
7. Document becomes "Approved"
   ↓
8. Admin or designated user makes it "Effective" (in use)
```

**Timeline Expectation:** 1-2 weeks (depends on review load)

### Workflow: Updating an Existing Document

```
1. Current version is "Effective"
   ↓
2. You create a new version (Draft)
   ↓
3. You make changes
   ↓
4. Submit for review (repeat above process)
   ↓
5. New version becomes Effective, old version becomes "Superseded"
```

### Workflow: Rejection & Revision

```
1. Document submitted for review
   ↓
2. Reviewer requests changes
   ↓
3. You receive notification with feedback
   ↓
4. You make requested changes
   ↓
5. You click "Resubmit for Review"
   ↓
6. Goes back to review queue
   ↓
7. Reviewer reviews again
```

**Tip:** If multiple issues are found, it's better to fix all at once and resubmit rather than iterating multiple times.

---

## Best Practices

### Writing Good Documents

✅ **DO:**
- Use clear, simple language
- Number steps sequentially (1, 2, 3...)
- Use bullet points for lists
- Include relevant images or diagrams
- Define abbreviations on first use
- Specify roles (e.g., "Quality Assurance Technician")

❌ **DON'T:**
- Use unclear pronouns ("they", "it" without referent)
- Make steps too long or complex
- Forget to save work regularly
- Include personal opinions
- Use different terminology for the same thing

### Requesting Review Effectively

✅ **Good request:**
- Submit when document is truly ready for feedback
- Select the right reviewers (those who understand the content)
- Include a message: "Please focus on technical accuracy and clarity"
- Respond promptly to reviewer feedback

❌ **Poor request:**
- Submitting incomplete/rough drafts
- Asking everyone to review (causes delays)
- No message or context provided
- Ignoring feedback for days

### Providing Feedback as a Reviewer

✅ **Good feedback:**
- Specific: "Section 3.2, change 'usually' to 'always'"
- Constructive: "Consider adding a troubleshooting section"
- Respectful: "I think we should add a safety step here because..."
- Timely: Review and comment within 2 business days

❌ **Poor feedback:**
- Vague: "Rewrite this"
- Critical: "This is wrong" (without explanation)
- Nitpicky: Correcting minor typos instead of substantive issues
- Slow: Reviewing a week later

---

## Troubleshooting

### "I can't find a document I created"

**Solution:**
1. Go to "My Documents" section
2. Check if document status is "Draft" (drafts only show you)
3. Use search box to find by title
4. Contact admin if still not found

### "I can't edit a document I own"

**Reason:** Document may be under review or already approved
**Solution:**
- If under review, wait for reviewers to finish
- To make changes after approval, create a new version
- Ask admin if unsure

### "My changes are not being saved"

**Check:**
1. Look for "Saved" indicator at top of page
2. Try clicking "Save" button manually
3. Check your internet connection
4. Refresh the page and try again
5. Try a different browser

### "I got rejected feedback but don't understand it"

**What to do:**
1. Click the comment to see full context
2. Reply to the comment with a question
3. Ask the reviewer for clarification
4. Contact DMS Administrator if unresolved

### "I forgot my password"

**Request a reset:**
1. On login page, click "Forgot Password?"
2. Enter your email address
3. Check your email for reset link
4. Click link and create new password

**If you can't find the email:**
- Check spam folder
- Contact your DMS Administrator
- They can reset your password directly

### "My session timed out"

**Why:** Left the system inactive for more than 8 hours
**Solution:**
1. Log in again with your credentials
2. You'll see your recent documents again
3. Any unsaved changes may be lost (use auto-save!)

### "I need access to a document I can't see"

**Request access:**
1. Contact your DMS Administrator
2. Provide: Document title, department
3. Admin will grant appropriate permissions
4. You'll receive email when access granted

---

## Getting Help

### Within the System

- **Help Icon** (?) - Check for contextual help on each page
- **Inbox/Notifications** - Messages about documents and approvals
- **Comment Section** - Ask questions about document content

### Contact Support

**For Technical Issues:**
- Email: `dms-support@pharma-company.com`
- Phone: `+1-555-0123` (ext. 4567)
- Response time: Within 4 business hours

**For Document/Content Questions:**
- Ask your department's Document Owner
- Contact the document author
- Reach out to Quality Assurance team

**For Access/Permission Questions:**
- Contact: DMS Administrator
- Email: `dms-admin@pharma-company.com`

### Training & Resources

- **Video Tutorials** - Available in Help section
- **Quick Reference Card** - One-page guide for common tasks
- **Group Training** - Monthly sessions for new users
- **Documentation** - Complete user manual (this file!)

---

## Quick Reference - Common Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Save Document | Ctrl + S |
| Search | Ctrl + F |
| Undo | Ctrl + Z |
| Redo | Ctrl + Y |
| Bold | Ctrl + B |
| Italic | Ctrl + I |
| Copy | Ctrl + C |
| Paste | Ctrl + V |

---

## Next Steps

1. **Explore the dashboard** - Familiarize yourself with the layout
2. **Find a template** - Create a document from a template to get comfortable
3. **Search for documents** - Browse documents in your department
4. **Read existing documents** - See how effective documents look
5. **Create your first document** - Draft a simple procedure
6. **Ask questions** - Don't hesitate to reach out

---

**Welcome to Q-Docs! Happy documenting!** 📄

For questions or feedback, contact the DMS team.

**Version:** 1.0.0 | **Last Updated:** February 2026 | **Next Review:** August 2026
