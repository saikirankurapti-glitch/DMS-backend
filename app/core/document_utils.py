"""
Utility functions for document management
"""
import hashlib
import re
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Document


def compute_content_hash(content: str) -> str:
    """
    Compute SHA-256 hash of content for optimistic concurrency control
    
    Args:
        content: HTML or SFDT content string
        
    Returns:
        SHA-256 hash as hex string
    """
    if not content:
        content = ""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def normalize_document_number(doc_number: str) -> str:
    """
    Normalize document number format
    
    Args:
        doc_number: Raw document number
        
    Returns:
        Normalized document number
    """
    # Remove extra whitespace and convert to uppercase
    return re.sub(r'\s+', '-', doc_number.strip()).upper()


def generate_document_number(db: Session, prefix: str = "SOP", department: str = None) -> str:
    """
    Auto-generate a unique document number
    
    Format: SOP-DEPT-YYYYMMDD-NNNN
    Example: SOP-QA-20251129-0001
    
    Args:
        db: Database session
        prefix: Document prefix (default: SOP)
        department: Department code (optional)
        
    Returns:
        Unique document number
    """
    today = datetime.utcnow()
    date_str = today.strftime("%Y%m%d")
    
    # Build base pattern
    if department:
        dept_code = department[:4].upper().replace(' ', '')
        pattern = f"{prefix}-{dept_code}-{date_str}-"
    else:
        pattern = f"{prefix}-{date_str}-"
    
    # Find the highest sequence number for today
    existing = db.query(Document).filter(
        Document.document_number.like(f"{pattern}%")
    ).order_by(Document.document_number.desc()).first()
    
    if existing:
        # Extract sequence number and increment
        try:
            last_seq = int(existing.document_number.split('-')[-1])
            next_seq = last_seq + 1
        except (ValueError, IndexError):
            next_seq = 1
    else:
        next_seq = 1
    
    # Generate new document number with zero-padded sequence
    return f"{pattern}{next_seq:04d}"


def verify_content_hash(content: str, expected_hash: str) -> bool:
    """
    Verify content hash matches expected value
    
    Args:
        content: Content to verify
        expected_hash: Expected hash value
        
    Returns:
        True if hash matches, False otherwise
    """
    actual_hash = compute_content_hash(content)
    return actual_hash == expected_hash


def sanitize_html_content(html: str) -> str:
    """
    Basic HTML sanitization for security
    Note: For production, use a proper HTML sanitization library like bleach
    
    Args:
        html: HTML content
        
    Returns:
        Sanitized HTML
    """
    # For now, just strip potentially dangerous tags
    # In production, use bleach or similar library
    dangerous_tags = ['script', 'iframe', 'object', 'embed', 'applet']
    sanitized = html
    for tag in dangerous_tags:
        sanitized = re.sub(f'<{tag}[^>]*>.*?</{tag}>', '', sanitized, flags=re.DOTALL | re.IGNORECASE)
        sanitized = re.sub(f'<{tag}[^>]*/?>', '', sanitized, flags=re.IGNORECASE)
    return sanitized


def get_next_version_number(db: Session, document_id: int) -> int:
    """
    Get the next version number for a document
    
    Args:
        db: Database session
        document_id: Document ID
        
    Returns:
        Next version number
    """
    from app.models import DocumentVersion
    
    max_version = db.query(DocumentVersion).filter(
        DocumentVersion.document_id == document_id
    ).order_by(DocumentVersion.version_number.desc()).first()
    
    if max_version:
        return max_version.version_number + 1
    return 1


