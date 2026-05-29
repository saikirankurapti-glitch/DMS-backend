"""
Token/Placeholder system for templates
Handles token extraction, validation, and replacement
"""
import re
from typing import List, Dict, Set, Tuple, Any
from collections import defaultdict


# Token format: {{TOKEN_NAME}}
TOKEN_PATTERN = re.compile(r'\{\{([A-Z0-9_]+)\}\}')

# Token categories and definitions
TOKEN_LIBRARY = {
    # Metadata tokens
    "TEMPLATE_TITLE": {"category": "Metadata", "description": "Template title", "required": True},
    "TEMPLATE_CODE": {"category": "Metadata", "description": "Template code (e.g., SP-KQA-007-01)", "required": True},
    "REVISION": {"category": "Metadata", "description": "Revision number", "required": True},
    "EFFECTIVE_DATE": {"category": "Dates", "description": "Effective date", "required": True},
    "NEXT_REVIEW_DATE": {"category": "Dates", "description": "Next review date", "required": False},
    "CC_NUMBER": {"category": "Metadata", "description": "CC number", "required": False},
    "DEPARTMENT": {"category": "Metadata", "description": "Department name", "required": True},
    "CONFIDENTIALITY": {"category": "Metadata", "description": "Confidentiality level", "required": False},
    
    # Content tokens
    "OBJECTIVE": {"category": "Content", "description": "Objective/Purpose", "required": False},
    "SCOPE": {"category": "Content", "description": "Scope", "required": False},
    "PROCEDURE": {"category": "Content", "description": "Procedure content", "required": False},
    "RESPONSIBILITY": {"category": "Content", "description": "Responsibility section", "required": False},
    "ACCOUNTABILITY": {"category": "Content", "description": "Accountability section", "required": False},
    
    # Signatory tokens
    "SIGNATORY_PREPARED_NAME": {"category": "Signatories", "description": "Prepared by name", "required": False},
    "SIGNATORY_PREPARED_DESIGNATION": {"category": "Signatories", "description": "Prepared by designation", "required": False},
    "SIGNATORY_PREPARED_DEPARTMENT": {"category": "Signatories", "description": "Prepared by department", "required": False},
    "SIGNATORY_PREPARED_DATE": {"category": "Signatories", "description": "Prepared by date", "required": False},
    "SIGNATORY_CHECKED_NAME": {"category": "Signatories", "description": "Checked by name", "required": False},
    "SIGNATORY_CHECKED_DESIGNATION": {"category": "Signatories", "description": "Checked by designation", "required": False},
    "SIGNATORY_CHECKED_DEPARTMENT": {"category": "Signatories", "description": "Checked by department", "required": False},
    "SIGNATORY_CHECKED_DATE": {"category": "Signatories", "description": "Checked by date", "required": False},
    "SIGNATORY_APPROVED_NAME": {"category": "Signatories", "description": "Approved by name", "required": False},
    "SIGNATORY_APPROVED_DESIGNATION": {"category": "Signatories", "description": "Approved by designation", "required": False},
    "SIGNATORY_APPROVED_DEPARTMENT": {"category": "Signatories", "description": "Approved by department", "required": False},
    "SIGNATORY_APPROVED_DATE": {"category": "Signatories", "description": "Approved by date", "required": False},
    
    # System tokens
    "PAGE_NUMBER": {"category": "System", "description": "Current page number", "required": False},
    "TOTAL_PAGES": {"category": "System", "description": "Total page count", "required": False},
    "CURRENT_DATE": {"category": "System", "description": "Current date", "required": False},
    "CURRENT_TIME": {"category": "System", "description": "Current time", "required": False},
    
    # Table tokens
    "ANNEXURES_TABLE": {"category": "Tables", "description": "Annexures table", "required": False},
    "SIGNATORY_TABLE": {"category": "Tables", "description": "Signatory table", "required": False},
    "REFERENCE_TABLE": {"category": "Tables", "description": "Reference documents table", "required": False},
    "DISTRIBUTION_TABLE": {"category": "Tables", "description": "Distribution list table", "required": False},
    "CHANGE_HISTORY_TABLE": {"category": "Tables", "description": "Change history table", "required": False},
}

# Default values for tokens
DEFAULT_TOKEN_VALUES = {
    "TEMPLATE_TITLE": "-NA-",
    "TEMPLATE_CODE": "-NA-",
    "REVISION": "01",
    "EFFECTIVE_DATE": "",
    "NEXT_REVIEW_DATE": "",
    "CC_NUMBER": "-NA-",
    "DEPARTMENT": "-NA-",
    "CONFIDENTIALITY": "Internal",
    "OBJECTIVE": "-NA-",
    "SCOPE": "-NA-",
    "PROCEDURE": "-NA-",
    "RESPONSIBILITY": "-NA-",
    "ACCOUNTABILITY": "-NA-",
    "SIGNATORY_PREPARED_NAME": "-NA-",
    "SIGNATORY_PREPARED_DESIGNATION": "-NA-",
    "SIGNATORY_PREPARED_DEPARTMENT": "-NA-",
    "SIGNATORY_PREPARED_DATE": "",
    "SIGNATORY_CHECKED_NAME": "-NA-",
    "SIGNATORY_CHECKED_DESIGNATION": "-NA-",
    "SIGNATORY_CHECKED_DEPARTMENT": "-NA-",
    "SIGNATORY_CHECKED_DATE": "",
    "SIGNATORY_APPROVED_NAME": "-NA-",
    "SIGNATORY_APPROVED_DESIGNATION": "-NA-",
    "SIGNATORY_APPROVED_DEPARTMENT": "-NA-",
    "SIGNATORY_APPROVED_DATE": "",
    "PAGE_NUMBER": "1",
    "TOTAL_PAGES": "1",
    "CURRENT_DATE": "",
    "CURRENT_TIME": "",
    "ANNEXURES_TABLE": "",
    "SIGNATORY_TABLE": "",
    "REFERENCE_TABLE": "",
    "DISTRIBUTION_TABLE": "",
    "CHANGE_HISTORY_TABLE": "",
}


def extract_tokens(html_content: str) -> Set[str]:
    """
    Extract all tokens from HTML content
    
    Args:
        html_content: HTML string containing tokens like {{TOKEN_NAME}}
        
    Returns:
        Set of token names found
    """
    tokens = set()
    matches = TOKEN_PATTERN.findall(html_content)
    for match in matches:
        tokens.add(match)
    return tokens


def extract_tokens_from_blocks(blocks: List[Dict]) -> Set[str]:
    """
    Extract all tokens from template blocks
    
    Args:
        blocks: List of block dictionaries with 'html' field
        
    Returns:
        Set of all token names found
    """
    all_tokens = set()
    for block in blocks:
        if 'html' in block:
            tokens = extract_tokens(block['html'])
            all_tokens.update(tokens)
    return all_tokens


def validate_tokens(tokens: Set[str], strict: bool = False) -> Tuple[bool, List[str], List[str]]:
    """
    Validate tokens against token library
    
    Args:
        tokens: Set of token names to validate
        strict: If True, require all tokens to be in library
        
    Returns:
        Tuple of (is_valid, missing_required, unknown_tokens)
    """
    missing_required = []
    unknown_tokens = []
    
    # Check for required tokens
    for token_name, token_info in TOKEN_LIBRARY.items():
        if token_info.get("required", False) and token_name not in tokens:
            missing_required.append(token_name)
    
    # Check for unknown tokens
    for token in tokens:
        if token not in TOKEN_LIBRARY:
            unknown_tokens.append(token)
    
    is_valid = len(missing_required) == 0 and (not strict or len(unknown_tokens) == 0)
    
    return is_valid, missing_required, unknown_tokens


def replace_tokens(html_content: str, token_values: Dict[str, str], strict: bool = False) -> str:
    """
    Replace tokens in HTML content with values
    
    Args:
        html_content: HTML string with tokens
        token_values: Dictionary mapping token names to values
        strict: If True, raise error on missing tokens; if False, use defaults
        
    Returns:
        HTML with tokens replaced
    """
    def replace_token(match):
        token_name = match.group(1)
        if token_name in token_values:
            return token_values[token_name]
        elif not strict:
            # Use default value
            return DEFAULT_TOKEN_VALUES.get(token_name, f"<missing: {token_name}>")
        else:
            raise ValueError(f"Missing required token: {token_name}")
    
    return TOKEN_PATTERN.sub(replace_token, html_content)


def get_token_categories() -> Dict[str, List[str]]:
    """
    Get tokens grouped by category
    
    Returns:
        Dictionary mapping category names to lists of token names
    """
    categories = defaultdict(list)
    for token_name, token_info in TOKEN_LIBRARY.items():
        category = token_info.get("category", "Other")
        categories[category].append(token_name)
    return dict(categories)


def get_token_info(token_name: str) -> Dict[str, Any]:
    """
    Get information about a token
    
    Args:
        token_name: Name of the token
        
    Returns:
        Dictionary with token information
    """
    return TOKEN_LIBRARY.get(token_name, {
        "category": "Unknown",
        "description": "Unknown token",
        "required": False
    })

