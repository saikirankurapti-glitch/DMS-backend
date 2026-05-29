"""
Email Templates
HTML email templates for workflow notifications
"""
from typing import Optional
from datetime import datetime


def get_base_template(content: str) -> str:
    """Base HTML template for all emails"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background-color: #2c3e50;
                color: white;
                padding: 20px;
                text-align: center;
                border-radius: 5px 5px 0 0;
            }}
            .content {{
                background-color: #f9f9f9;
                padding: 20px;
                border: 1px solid #ddd;
                border-top: none;
            }}
            .footer {{
                background-color: #ecf0f1;
                padding: 15px;
                text-align: center;
                font-size: 12px;
                color: #7f8c8d;
                border-radius: 0 0 5px 5px;
            }}
            .button {{
                display: inline-block;
                padding: 12px 24px;
                background-color: #3498db;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin: 10px 0;
            }}
            .info-box {{
                background-color: #e8f4f8;
                border-left: 4px solid #3498db;
                padding: 15px;
                margin: 15px 0;
            }}
            .warning-box {{
                background-color: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 15px;
                margin: 15px 0;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Document Management System</h1>
        </div>
        <div class="content">
            {content}
        </div>
        <div class="footer">
            <p>This is an automated notification from the Document Management System.</p>
            <p>Please do not reply to this email.</p>
        </div>
    </body>
    </html>
    """


def review_assigned_template(
    document_number: str,
    document_title: str,
    version_number: str,
    author_name: str,
    reviewer_name: str,
    document_url: Optional[str] = None,
    change_summary: Optional[str] = None
) -> str:
    """Template for when a document is assigned for review"""
    content = f"""
        <h2>New Document Pending for Review</h2>
        <p>Dear {reviewer_name},</p>
        
        <div class="info-box">
            <p><strong>Document:</strong> {document_number} - {document_title}</p>
            <p><strong>Version:</strong> {version_number}</p>
            <p><strong>Submitted by:</strong> {author_name}</p>
            <p><strong>Submitted at:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
        </div>
        
        {f'<p><strong>Change Summary:</strong> {change_summary}</p>' if change_summary else ''}
        
        <p>A new document has been submitted for your review. Please review the document content and provide your feedback.</p>
        
        {f'<p><a href="{document_url}" class="button">Review Document</a></p>' if document_url else ''}
        
        <p><strong>Action Required:</strong> Please review the document and either approve it for the next stage or reject it with comments.</p>
    """
    return get_base_template(content)


def review_rejected_template(
    document_number: str,
    document_title: str,
    version_number: str,
    reviewer_name: str,
    author_name: str,
    rejection_reason: Optional[str] = None,
    document_url: Optional[str] = None
) -> str:
    """Template for when review is rejected"""
    content = f"""
        <h2>Document Review Rejected</h2>
        <p>Dear {author_name},</p>
        
        <div class="warning-box">
            <p><strong>Document:</strong> {document_number} - {document_title}</p>
            <p><strong>Version:</strong> {version_number}</p>
            <p><strong>Rejected by:</strong> {reviewer_name}</p>
            <p><strong>Rejected at:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
        </div>
        
        {f'<p><strong>Rejection Reason:</strong> {rejection_reason}</p>' if rejection_reason else '<p>The document has been rejected during review. Please check the comments and make necessary corrections.</p>'}
        
        <p>Your document has been rejected during the review process. Please address the reviewer's comments and resubmit the document.</p>
        
        {f'<p><a href="{document_url}" class="button">View Document</a></p>' if document_url else ''}
        
        <p><strong>Action Required:</strong> Please review the feedback, make corrections, and resubmit the document.</p>
    """
    return get_base_template(content)


def review_approved_template(
    document_number: str,
    document_title: str,
    version_number: str,
    reviewer_name: str,
    approver_name: str,
    document_url: Optional[str] = None
) -> str:
    """Template for when review is approved (notifies approver)"""
    content = f"""
        <h2>Document Pending for Approval</h2>
        <p>Dear {approver_name},</p>
        
        <div class="info-box">
            <p><strong>Document:</strong> {document_number} - {document_title}</p>
            <p><strong>Version:</strong> {version_number}</p>
            <p><strong>Reviewed by:</strong> {reviewer_name}</p>
            <p><strong>Approved for approval at:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
        </div>
        
        <p>A document has been reviewed and approved, and is now pending your approval.</p>
        
        {f'<p><a href="{document_url}" class="button">Review Document</a></p>' if document_url else ''}
        
        <p><strong>Action Required:</strong> Please review the document and either approve it for publication or reject it with comments.</p>
    """
    return get_base_template(content)


def approval_assigned_template(
    document_number: str,
    document_title: str,
    version_number: str,
    reviewer_name: str,
    approver_name: str,
    document_url: Optional[str] = None
) -> str:
    """Template for when document is assigned for approval"""
    content = f"""
        <h2>Document Pending for Approval</h2>
        <p>Dear {approver_name},</p>
        
        <div class="info-box">
            <p><strong>Document:</strong> {document_number} - {document_title}</p>
            <p><strong>Version:</strong> {version_number}</p>
            <p><strong>Reviewed by:</strong> {reviewer_name}</p>
            <p><strong>Assigned at:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
        </div>
        
        <p>A document has been reviewed and is now pending your approval.</p>
        
        {f'<p><a href="{document_url}" class="button">Review Document</a></p>' if document_url else ''}
        
        <p><strong>Action Required:</strong> Please review the document and either approve it for publication or reject it with comments.</p>
    """
    return get_base_template(content)


def approval_rejected_template(
    document_number: str,
    document_title: str,
    version_number: str,
    approver_name: str,
    author_name: str,
    rejection_reason: Optional[str] = None,
    document_url: Optional[str] = None
) -> str:
    """Template for when approval is rejected"""
    content = f"""
        <h2>Document Approval Rejected</h2>
        <p>Dear {author_name},</p>
        
        <div class="warning-box">
            <p><strong>Document:</strong> {document_number} - {document_title}</p>
            <p><strong>Version:</strong> {version_number}</p>
            <p><strong>Rejected by:</strong> {approver_name}</p>
            <p><strong>Rejected at:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
        </div>
        
        {f'<p><strong>Rejection Reason:</strong> {rejection_reason}</p>' if rejection_reason else '<p>The document has been rejected during approval. Please check the comments and make necessary corrections.</p>'}
        
        <p>Your document has been rejected during the approval process. Please address the approver's comments and resubmit the document.</p>
        
        {f'<p><a href="{document_url}" class="button">View Document</a></p>' if document_url else ''}
        
        <p><strong>Action Required:</strong> Please review the feedback, make corrections, and resubmit the document.</p>
    """
    return get_base_template(content)


def document_effective_template(
    document_number: str,
    document_title: str,
    version_number: str,
    effective_date: str,
    recipient_name: str,
    document_url: Optional[str] = None
) -> str:
    """Template for when document becomes effective"""
    content = f"""
        <h2>New Document Published</h2>
        <p>Dear {recipient_name},</p>
        
        <div class="info-box">
            <p><strong>Document:</strong> {document_number} - {document_title}</p>
            <p><strong>Version:</strong> {version_number}</p>
            <p><strong>Effective Date:</strong> {effective_date}</p>
            <p><strong>Published at:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
        </div>
        
        <p>A new document has been published and is now effective. Please review the document to ensure you are aware of the latest procedures and requirements.</p>
        
        {f'<p><a href="{document_url}" class="button">View Document</a></p>' if document_url else ''}
        
        <p><strong>Important:</strong> This document is now the official version and supersedes any previous versions.</p>
    """
    return get_base_template(content)


def version_obsoleted_template(
    document_number: str,
    document_title: str,
    old_version: str,
    new_version: str,
    recipient_name: str,
    document_url: Optional[str] = None
) -> str:
    """Template for when a version becomes obsolete"""
    content = f"""
        <h2>Document Version Obsoleted</h2>
        <p>Dear {recipient_name},</p>
        
        <div class="warning-box">
            <p><strong>Document:</strong> {document_number} - {document_title}</p>
            <p><strong>Obsoleted Version:</strong> {old_version}</p>
            <p><strong>New Effective Version:</strong> {new_version}</p>
            <p><strong>Obsoleted at:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
        </div>
        
        <p>A new version of this document has been published, and the previous version ({old_version}) is now obsolete.</p>
        
        {f'<p><a href="{document_url}" class="button">View New Version</a></p>' if document_url else ''}
        
        <p><strong>Important:</strong> Please ensure you are using the latest version ({new_version}) of this document.</p>
    """
    return get_base_template(content)

