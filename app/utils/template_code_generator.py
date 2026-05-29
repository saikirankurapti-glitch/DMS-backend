"""
Template Code Auto-Generation Utility
Generates template codes based on category, department, and sequential numbering
"""
from sqlalchemy.orm import Session
from app.models import Template
import re


# Department code mappings
DEPARTMENT_CODES = {
    'Quality Assurance': 'QA',
    'Quality Control': 'QC',
    'Production': 'PROD',
    'Packaging': 'PKG',
    'Research & Development': 'R&D',
    'R&D': 'R&D',
    'Regulatory': 'REG',
    'Regulatory Affairs': 'REG',
    'Manufacturing': 'MFG',
    'Engineering': 'ENG',
    'Safety': 'SAF',
    'Kurkumbh': 'KQA',  # Special case for Kurkumbh plant
}


def get_department_code(department: str) -> str:
    """
    Get department code from department name
    
    Args:
        department: Department name
        
    Returns:
        Department code (e.g., 'QA', 'PKG')
    """
    if not department:
        return 'GEN'  # General
    
    # Try exact match first
    if department in DEPARTMENT_CODES:
        return DEPARTMENT_CODES[department]
    
    # Try case-insensitive match
    department_upper = department.upper()
    for dept_name, code in DEPARTMENT_CODES.items():
        if dept_name.upper() == department_upper:
            return code
    
    # Extract first letters or use abbreviation
    words = department.split()
    if len(words) >= 2:
        return ''.join([w[0].upper() for w in words[:2]])
    elif len(words) == 1:
        return department[:3].upper()
    else:
        return 'GEN'


def generate_template_code(
    db: Session,
    category: str,
    department: str,
    revision: str = '01'
) -> str:
    """
    Auto-generate a unique template code
    
    Format:
    - Forms: SP-DEPT-NUM-F##-##
      Example: SP-QA-051-F01-01
    - SOP/STP/Report/Annexure: SP-DEPT-NUM-##
      Example: SP-PKG-002-01
    
    Args:
        db: Database session
        category: Template category (SOP, STP, Form, Report, Annexure)
        department: Department name
        revision: Revision number (default: '01')
        
    Returns:
        Unique template code
    """
    dept_code = get_department_code(department)
    
    # Determine if it's a Form
    is_form = category.upper() == 'FORM'
    
    if is_form:
        # Format: SP-DEPT-NUM-F##-##
        # Find the highest sequence number for this department and category
        pattern = f"SP-{dept_code}-"
        
        existing_templates = db.query(Template).filter(
            Template.template_code.like(f"{pattern}%"),
            Template.category == category,
            Template.is_deleted == False
        ).order_by(Template.template_code.desc()).all()
        
        # Extract form numbers
        form_numbers = []
        for template in existing_templates:
            if template.template_code:
                # Pattern: SP-DEPT-NUM-F##-##
                match = re.match(rf'SP-{dept_code}-(\d+)-F(\d+)-(\d+)', template.template_code)
                if match:
                    seq_num = int(match.group(1))
                    form_numbers.append(seq_num)
        
        # Get next sequence number
        if form_numbers:
            next_seq = max(form_numbers) + 1
        else:
            next_seq = 1
        
        # Format: SP-DEPT-NUM-F01-##
        form_num = '01'  # Default form number, can be incremented if needed
        return f"SP-{dept_code}-{next_seq:03d}-F{form_num}-{revision}"
    else:
        # Format: SP-DEPT-NUM-##
        # Find the highest sequence number for this department and category
        pattern = f"SP-{dept_code}-"
        
        existing_templates = db.query(Template).filter(
            Template.template_code.like(f"{pattern}%"),
            Template.category == category,
            Template.is_deleted == False
        ).order_by(Template.template_code.desc()).all()
        
        # Extract sequence numbers
        seq_numbers = []
        for template in existing_templates:
            if template.template_code:
                # Pattern: SP-DEPT-NUM-##
                match = re.match(rf'SP-{dept_code}-(\d+)-(\d+)', template.template_code)
                if match:
                    seq_num = int(match.group(1))
                    seq_numbers.append(seq_num)
        
        # Get next sequence number
        if seq_numbers:
            next_seq = max(seq_numbers) + 1
        else:
            next_seq = 1
        
        # Format: SP-DEPT-NUM-##
        return f"SP-{dept_code}-{next_seq:03d}-{revision}"


def validate_template_code_format(template_code: str, category: str) -> bool:
    """
    Validate template code format
    
    Args:
        template_code: Template code to validate
        category: Template category
        
    Returns:
        True if format is valid, False otherwise
    """
    if not template_code:
        return False
    
    is_form = category.upper() == 'FORM'
    
    if is_form:
        # Format: SP-DEPT-NUM-F##-##
        pattern = r'^SP-[A-Z0-9&]+-\d{3}-F\d{2}-\d{2}$'
    else:
        # Format: SP-DEPT-NUM-##
        pattern = r'^SP-[A-Z0-9&]+-\d{3}-\d{2}$'
    
    return bool(re.match(pattern, template_code))

