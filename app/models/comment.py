"""
Document Comment Model
Represents inline comments and annotations on document versions
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class DocumentComment(Base):
    """
    Inline comment on a document version
    Used by reviewers/approvers to annotate specific text
    """
    __tablename__ = "document_comments"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Reference to document version
    document_version_id = Column(Integer, ForeignKey("document_versions.id"), nullable=False)
    
    # Comment author
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Comment content
    comment_text = Column(Text, nullable=False)
    
    # Text selection info (for highlighting)
    selected_text = Column(Text, nullable=True)  # The actual text that was highlighted
    selection_start = Column(Integer, nullable=True)  # Character offset start
    selection_end = Column(Integer, nullable=True)  # Character offset end
    
    # Optional: Store HTML path/selector for more precise highlighting
    text_context = Column(Text, nullable=True)  # Surrounding text for finding position
    
    # Status
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    version = relationship("DocumentVersion", back_populates="comments")
    author = relationship("User", foreign_keys=[user_id], backref="authored_comments")
    resolver = relationship("User", foreign_keys=[resolved_by_id], backref="resolved_comments")

