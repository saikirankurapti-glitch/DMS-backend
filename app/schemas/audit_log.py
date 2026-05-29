"""
Audit Log Schemas
"""
from typing import Optional, List, Any, Dict
from datetime import datetime
from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    """Audit log entry response"""
    id: int
    user_id: Optional[int]
    username: str
    action: str
    entity_type: str
    entity_id: Optional[int]
    description: str
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str]
    user_agent: Optional[str]
    timestamp: datetime
    
    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Paginated list of audit logs"""
    logs: List[AuditLogResponse]
    total: int
    page: int
    page_size: int
    
    class Config:
        from_attributes = True


