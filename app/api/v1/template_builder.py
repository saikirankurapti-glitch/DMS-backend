"""
Template Builder API Endpoints
Handles block-based template creation, editing, preview, and generation
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import os
import json

from app.api.deps import get_db, get_current_user, get_client_ip, get_user_agent
from app.models import User, Template, TemplateVersion, TemplateStatus
from app.schemas.template_builder import (
    TemplateCreateRequest,
    TemplateUpdateRequest,
    TemplatePreviewRequest,
    TemplateGenerateRequest,
    TemplateResponse,
    TokenUsageResponse,
)
from app.utils.template_tokens import (
    extract_tokens_from_blocks,
    validate_tokens,
    get_token_categories,
    get_token_info,
    replace_tokens,
)
from app.utils.template_docx_generator import generate_docx_from_template
from app.utils.template_code_generator import generate_template_code
from app.core.audit import AuditLogger

router = APIRouter()


def can_create_template(user: User) -> bool:
    """Check if user can create templates (Author or Admin)"""
    return user.has_role("Author") or user.is_admin()


@router.post("/create", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request,
    template_in: TemplateCreateRequest,
):
    """
    Create a new block-based template
    
    Requires: Author or Admin
    """
    if not can_create_template(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Authors and Admins can create templates"
        )
    
    try:
        # Get category from metadata or config
        category = None
        if template_in.template_data.config and hasattr(template_in.template_data.config, 'category'):
            category = template_in.template_data.config.category
        elif hasattr(template_in.template_data.metadata, 'category'):
            category = template_in.template_data.metadata.category
        
        # Default to SOP if no category provided
        if not category:
            category = 'SOP'
        
        # Generate a unique template code for the template itself (not for documents)
        # This will be used as a placeholder
        base_code = f"TEMPLATE-{category}-{datetime.now().strftime('%Y%m%d')}"
        template_code = base_code
        
        # Check if code exists and append sequence number if needed
        existing_template = db.query(Template).filter(
            Template.template_code == template_code,
            Template.is_deleted == False
        ).first()
        
        if existing_template:
            # Find the highest sequence number for this base code
            similar_templates = db.query(Template).filter(
                Template.template_code.like(f"{base_code}-%"),
                Template.is_deleted == False
            ).all()
            
            max_seq = 0
            for t in similar_templates:
                if t.template_code and t.template_code.startswith(base_code + "-"):
                    try:
                        seq = int(t.template_code.split("-")[-1])
                        max_seq = max(max_seq, seq)
                    except ValueError:
                        pass
            
            template_code = f"{base_code}-{max_seq + 1:03d}"
        
        # Get template title
        template_title = None
        if hasattr(template_in.template_data.metadata, 'template_title'):
            template_title = template_in.template_data.metadata.template_title
        
        if not template_title:
            template_title = f"SOP Template - {category}"
        
        # Create template with minimal metadata
        template = Template(
            name=template_title,
            template_code=template_code,
            category=category,
            department=None,  # Will be filled when creating documents
            confidentiality="Internal",
            owner_id=current_user.id,
            created_by_id=current_user.id,
            template_type='block_builder',
        )
        
        try:
            db.add(template)
            db.flush()
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving template to database: {str(e)}"
            )
        
        # Create first version
        # Use model_dump() for Pydantic v2, fallback to dict() for v1
        try:
            if hasattr(template_in.template_data.metadata, 'model_dump'):
                metadata_dict = template_in.template_data.metadata.model_dump()
            elif hasattr(template_in.template_data.metadata, 'dict'):
                metadata_dict = template_in.template_data.metadata.dict()
            else:
                # Fallback: manual extraction
                metadata_dict = {
                    "template_title": getattr(template_in.template_data.metadata, 'template_title', None),
                    "category": category,
                }
        except Exception as e:
            # Fallback: manual extraction
            metadata_dict = {
                "template_title": template_title,
                "category": category,
            }
        
        blocks_list = []
        for block in template_in.template_data.blocks:
            try:
                if isinstance(block, dict):
                    block_dict = block
                elif hasattr(block, 'model_dump'):
                    block_dict = block.model_dump()
                elif hasattr(block, 'dict'):
                    block_dict = block.dict()
                else:
                    # Fallback: manual extraction
                    block_dict = {
                        "id": getattr(block, 'id', ''),
                        "type": getattr(block, 'type', 'paragraph'),
                        "html": getattr(block, 'html', ''),
                        "order": getattr(block, 'order', 0),
                        "metadata": getattr(block, 'metadata', {}),
                    }
            except Exception as e:
                # Fallback: manual extraction
                block_dict = {
                    "id": getattr(block, 'id', ''),
                    "type": getattr(block, 'type', 'paragraph'),
                    "html": getattr(block, 'html', ''),
                    "order": getattr(block, 'order', 0),
                    "metadata": getattr(block, 'metadata', {}),
                }
            blocks_list.append(block_dict)
        
        template_data_dict = {
            "metadata": metadata_dict,
            "blocks": blocks_list,
        }
        
        # Add config if provided
        if template_in.template_data.config:
            try:
                if isinstance(template_in.template_data.config, dict):
                    config_dict = template_in.template_data.config
                elif hasattr(template_in.template_data.config, 'model_dump'):
                    config_dict = template_in.template_data.config.model_dump()
                elif hasattr(template_in.template_data.config, 'dict'):
                    config_dict = template_in.template_data.config.dict()
                else:
                    # Fallback: manual extraction
                    config_dict = {
                        "required_metadata_fields": [
                            {
                                "key": getattr(f, 'key', ''),
                                "label": getattr(f, 'label', ''),
                                "required": getattr(f, 'required', False)
                            } for f in getattr(template_in.template_data.config, 'required_metadata_fields', [])
                        ],
                        "category": category,
                    }
            except Exception as e:
                # Fallback: manual extraction
                config_dict = {
                    "required_metadata_fields": [
                        {
                            "key": getattr(f, 'key', ''),
                            "label": getattr(f, 'label', ''),
                            "required": getattr(f, 'required', False)
                        } for f in getattr(template_in.template_data.config, 'required_metadata_fields', [])
                    ],
                    "category": category,
                }
            template_data_dict["config"] = config_dict
        
        # Ensure all data is JSON serializable
        try:
            json.dumps(template_data_dict)  # Test serialization
        except (TypeError, ValueError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Template data contains non-serializable values: {str(e)}"
            )
        
        try:
            template_version = TemplateVersion(
                template_id=template.id,
                version_number=1,
                revision=None,  # Revision will be set when creating documents
                template_data=template_data_dict,
                sample_values=template_in.sample_values,
                status=TemplateStatus.DRAFT,  # Pass enum object, SQLAlchemy will use .value
                created_by_id=current_user.id,
            )
            db.add(template_version)
            db.commit()
            db.refresh(template_version)
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating template version: {str(e)}"
            )
        
        # Audit log
        AuditLogger.log(
            db=db,
            user_id=current_user.id,
            username=current_user.username,
            action="TEMPLATE_CREATED",
            entity_type="Template",
            entity_id=template.id,
            description=f"Created template '{template.name}' (code: {template.template_code})",
            details={
                "template_id": template.id,
                "template_code": template.template_code,
                "category": template.category,
            },
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )
        
        # Prepare response
        response = TemplateResponse(
            id=template.id,
            name=template.name,
            template_code=template.template_code,
            category=template.category,
            department=template.department,
            template_type=template.template_type,
            status=template_version.status.value,
            version_number=template_version.version_number,
            revision=template_version.revision,
            template_data=template_version.template_data,
            created_by_id=current_user.id,
            created_by_username=current_user.username,
            created_at=template.created_at,
            updated_at=template.updated_at,
        )
        
        return response
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log the full error for debugging
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error creating template: {str(e)}")
        print(f"Traceback: {error_trace}")
        
        # Rollback any pending transaction
        try:
            db.rollback()
        except:
            pass
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating template: {str(e)}"
        )


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    template_id: int,
):
    """Get template by ID"""
    template = db.query(Template).filter(
        Template.id == template_id,
        Template.is_deleted == False
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Get latest version
    version = db.query(TemplateVersion).filter(
        TemplateVersion.template_id == template_id
    ).order_by(TemplateVersion.version_number.desc()).first()
    
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template version not found"
        )
    
    response = TemplateResponse(
        id=template.id,
        name=template.name,
        template_code=template.template_code,
        category=template.category,
        department=template.department,
        template_type=template.template_type,
        status=version.status.value,
        version_number=version.version_number,
        revision=version.revision,
        template_data=version.template_data,
        created_by_id=version.created_by_id,
        created_by_username=version.created_by.username if version.created_by else None,
        created_at=version.created_at,
        updated_at=version.updated_at,
    )
    
    return response


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request,
    template_id: int,
    template_in: TemplateUpdateRequest,
):
    """
    Update template (creates new version if published)
    
    Requires: Author (owner) or Admin
    """
    template = db.query(Template).filter(
        Template.id == template_id,
        Template.is_deleted == False
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Check permissions
    if template.owner_id != current_user.id and not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this template"
        )
    
    # Get current version
    current_version = db.query(TemplateVersion).filter(
        TemplateVersion.template_id == template_id
    ).order_by(TemplateVersion.version_number.desc()).first()
    
    # If published, create new version; otherwise update current
    if current_version and current_version.status == TemplateStatus.PUBLISHED:
        # Create new version
        new_version_number = current_version.version_number + 1
        new_revision = str(int(current_version.revision or "01") + 1).zfill(2)
        
        # Serialize template data
        try:
            if hasattr(template_in.template_data.metadata, 'model_dump'):
                metadata_dict = template_in.template_data.metadata.model_dump()
            else:
                metadata_dict = template_in.template_data.metadata.dict()
        except:
            metadata_dict = {
                "template_title": getattr(template_in.template_data.metadata, 'template_title', None),
                "category": getattr(template_in.template_data.metadata, 'category', 'SOP'),
            }
        
        blocks_list = []
        for block in template_in.template_data.blocks:
            try:
                if isinstance(block, dict):
                    blocks_list.append(block)
                elif hasattr(block, 'model_dump'):
                    blocks_list.append(block.model_dump())
                else:
                    blocks_list.append(block.dict())
            except:
                blocks_list.append({
                    "id": getattr(block, 'id', ''),
                    "type": getattr(block, 'type', 'paragraph'),
                    "html": getattr(block, 'html', ''),
                    "order": getattr(block, 'order', 0),
                    "metadata": getattr(block, 'metadata', {}),
                })
        
        template_data_dict = {
            "metadata": metadata_dict,
            "blocks": blocks_list,
        }
        
        # Add config if provided
        if template_in.template_data.config:
            try:
                if isinstance(template_in.template_data.config, dict):
                    config_dict = template_in.template_data.config
                elif hasattr(template_in.template_data.config, 'model_dump'):
                    config_dict = template_in.template_data.config.model_dump()
                else:
                    config_dict = template_in.template_data.config.dict()
            except:
                config_dict = {
                    "required_metadata_fields": [
                        {
                            "key": getattr(f, 'key', ''),
                            "label": getattr(f, 'label', ''),
                            "required": getattr(f, 'required', False)
                        } for f in template_in.template_data.config.required_metadata_fields
                    ],
                    "category": getattr(template_in.template_data.config, 'category', 'SOP'),
                }
            template_data_dict["config"] = config_dict
        
        template_version = TemplateVersion(
            template_id=template.id,
            version_number=new_version_number,
            revision=new_revision,
            template_data=template_data_dict,
            sample_values=template_in.sample_values,
            status=TemplateStatus.DRAFT,  # Pass enum object, SQLAlchemy will use .value
            created_by_id=current_user.id,
        )
        db.add(template_version)
    else:
        # Update current version
        if current_version:
            # Serialize template data
            try:
                if hasattr(template_in.template_data.metadata, 'model_dump'):
                    metadata_dict = template_in.template_data.metadata.model_dump()
                else:
                    metadata_dict = template_in.template_data.metadata.dict()
            except:
                metadata_dict = {
                    "template_title": getattr(template_in.template_data.metadata, 'template_title', None),
                    "category": getattr(template_in.template_data.metadata, 'category', 'SOP'),
                }
            
            blocks_list = []
            for block in template_in.template_data.blocks:
                try:
                    if isinstance(block, dict):
                        blocks_list.append(block)
                    elif hasattr(block, 'model_dump'):
                        blocks_list.append(block.model_dump())
                    else:
                        blocks_list.append(block.dict())
                except:
                    blocks_list.append({
                        "id": getattr(block, 'id', ''),
                        "type": getattr(block, 'type', 'paragraph'),
                        "html": getattr(block, 'html', ''),
                        "order": getattr(block, 'order', 0),
                        "metadata": getattr(block, 'metadata', {}),
                    })
            
            template_data_dict = {
                "metadata": metadata_dict,
                "blocks": blocks_list,
            }
            
            # Add config if provided
            if template_in.template_data.config:
                try:
                    if isinstance(template_in.template_data.config, dict):
                        config_dict = template_in.template_data.config
                    elif hasattr(template_in.template_data.config, 'model_dump'):
                        config_dict = template_in.template_data.config.model_dump()
                    else:
                        config_dict = template_in.template_data.config.dict()
                except:
                    config_dict = {
                        "required_metadata_fields": [
                            {
                                "key": getattr(f, 'key', ''),
                                "label": getattr(f, 'label', ''),
                                "required": getattr(f, 'required', False)
                            } for f in template_in.template_data.config.required_metadata_fields
                        ],
                        "category": getattr(template_in.template_data.config, 'category', 'SOP'),
                    }
                template_data_dict["config"] = config_dict
            
            current_version.template_data = template_data_dict
            current_version.sample_values = template_in.sample_values
            current_version.updated_at = datetime.utcnow()
    
    # Update template metadata - handle optional fields
    template.name = template_in.template_data.metadata.template_title or f"SOP Template - {template_in.template_data.metadata.category}"
    template.category = template_in.template_data.metadata.category
    # These fields may not exist in minimal metadata
    if hasattr(template_in.template_data.metadata, 'template_code') and template_in.template_data.metadata.template_code:
        template.template_code = template_in.template_data.metadata.template_code
    if hasattr(template_in.template_data.metadata, 'department') and template_in.template_data.metadata.department:
        template.department = template_in.template_data.metadata.department
    if hasattr(template_in.template_data.metadata, 'confidentiality') and template_in.template_data.metadata.confidentiality:
        template.confidentiality = template_in.template_data.metadata.confidentiality
    
    db.commit()
    db.refresh(template)
    
    # Get updated version
    version = db.query(TemplateVersion).filter(
        TemplateVersion.template_id == template_id
    ).order_by(TemplateVersion.version_number.desc()).first()
    
    # Audit log
    AuditLogger.log(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="TEMPLATE_UPDATED",
        entity_type="Template",
        entity_id=template.id,
        description=f"Updated template '{template.name}'",
        details={"template_id": template.id},
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )
    
    response = TemplateResponse(
        id=template.id,
        name=template.name,
        template_code=template.template_code,
        category=template.category,
        department=template.department,
        template_type=template.template_type,
        status=version.status.value,
        version_number=version.version_number,
        revision=version.revision,
        template_data=version.template_data,
        created_by_id=version.created_by_id,
        created_by_username=version.created_by.username if version.created_by else None,
        created_at=version.created_at,
        updated_at=version.updated_at,
    )
    
    return response


@router.post("/{template_id}/preview", response_model=dict)
async def preview_template(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    template_id: int,
    preview_in: TemplatePreviewRequest,
):
    """
    Generate HTML preview of template with token replacement
    """
    template = db.query(Template).filter(
        Template.id == template_id,
        Template.is_deleted == False
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    version = db.query(TemplateVersion).filter(
        TemplateVersion.template_id == template_id
    ).order_by(TemplateVersion.version_number.desc()).first()
    
    if not version or not version.template_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template data not found"
        )
    
    # Get token values (merge sample_values with preview_in values)
    token_values = version.sample_values or {}
    if preview_in.sample_values:
        token_values.update(preview_in.sample_values)
    
    # Replace tokens in blocks
    blocks = version.template_data.get('blocks', [])
    preview_blocks = []
    for block in blocks:
        html_content = block.get('html', '')
        preview_html = replace_tokens(html_content, token_values, strict=False)
        preview_blocks.append({
            **block,
            'html': preview_html
        })
    
    return {
        "metadata": version.template_data.get('metadata', {}),
        "blocks": preview_blocks,
        "token_values": token_values,
    }


@router.post("/{template_id}/generate", response_model=dict)
async def generate_document(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request,
    template_id: int,
    generate_in: TemplateGenerateRequest,
):
    """
    Generate DOCX/PDF/HTML document from template
    
    Requires: Template must be published or user must be owner/admin
    """
    template = db.query(Template).filter(
        Template.id == template_id,
        Template.is_deleted == False
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    version = db.query(TemplateVersion).filter(
        TemplateVersion.template_id == template_id
    ).order_by(TemplateVersion.version_number.desc()).first()
    
    if not version or not version.template_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template data not found"
        )
    
    # Check if template is published or user has permission
    if version.status != TemplateStatus.PUBLISHED:
        if template.owner_id != current_user.id and not current_user.is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only published templates can be used, or you must be the owner/admin"
            )
    
    # Generate document based on format
    if generate_in.format == 'docx':
        output_path = generate_docx_from_template(
            version.template_data,
            generate_in.token_values,
            strict=generate_in.strict_mode
        )
        
        # Update version with generated file path
        version.generated_docx_path = output_path
        db.commit()
        
        # Audit log
        AuditLogger.log(
            db=db,
            user_id=current_user.id,
            username=current_user.username,
            action="TEMPLATE_DOCUMENT_GENERATED",
            entity_type="TemplateVersion",
            entity_id=version.id,
            description=f"Generated DOCX from template '{template.name}'",
            details={
                "template_id": template.id,
                "format": "docx",
            },
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )
        
        return {
            "file_path": output_path,
            "format": "docx",
            "download_url": f"/api/v1/template-builder/{template_id}/download?format=docx",
        }
    elif generate_in.format == 'html':
        # Generate HTML
        blocks = version.template_data.get('blocks', [])
        html_content = ""
        for block in sorted(blocks, key=lambda b: b.get('order', 0)):
            html_content += replace_tokens(block.get('html', ''), generate_in.token_values, generate_in.strict_mode)
        
        return {
            "html_content": html_content,
            "format": "html",
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format: {generate_in.format}"
        )


@router.get("/{template_id}/download")
async def download_generated_document(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    template_id: int,
    format: str = "docx",
):
    """Download generated document"""
    template = db.query(Template).filter(
        Template.id == template_id,
        Template.is_deleted == False
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    version = db.query(TemplateVersion).filter(
        TemplateVersion.template_id == template_id
    ).order_by(TemplateVersion.version_number.desc()).first()
    
    if format == 'docx' and version.generated_docx_path:
        if os.path.exists(version.generated_docx_path):
            return FileResponse(
                version.generated_docx_path,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                filename=os.path.basename(version.generated_docx_path)
            )
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Generated document not found"
    )


@router.get("/{template_id}/tokens", response_model=TokenUsageResponse)
async def get_token_usage(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    template_id: int,
):
    """Get token usage information for template"""
    template = db.query(Template).filter(
        Template.id == template_id,
        Template.is_deleted == False
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    version = db.query(TemplateVersion).filter(
        TemplateVersion.template_id == template_id
    ).order_by(TemplateVersion.version_number.desc()).first()
    
    if not version or not version.template_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template data not found"
        )
    
    # Extract tokens
    blocks = version.template_data.get('blocks', [])
    tokens_found = extract_tokens_from_blocks(blocks)
    
    # Validate
    is_valid, missing_required, unknown_tokens = validate_tokens(tokens_found, strict=False)
    
    # Get token info
    tokens_used = []
    for token in tokens_found:
        info = get_token_info(token)
        tokens_used.append({
            "name": token,
            "category": info.get("category", "Unknown"),
            "description": info.get("description", ""),
            "example": f"{{{{{token}}}}}",
        })
    
    return TokenUsageResponse(
        tokens_found=list(tokens_found),
        tokens_used=tokens_used,
        missing_required=missing_required,
        unknown_tokens=unknown_tokens,
    )


@router.get("/tokens/library", response_model=dict)
async def get_token_library(
    current_user: User = Depends(get_current_user),
):
    """Get token library with categories"""
    from app.utils.template_tokens import TOKEN_LIBRARY
    
    categories = get_token_categories()
    token_library = {}
    
    for category, token_names in categories.items():
        token_library[category] = [
            {
                "name": token_name,
                "description": TOKEN_LIBRARY[token_name].get("description", ""),
                "required": TOKEN_LIBRARY[token_name].get("required", False),
                "example": f"{{{{{token_name}}}}}",
            }
            for token_name in token_names
        ]
    
    return token_library

