"""
Template Converter Utilities
Handles DOCX to HTML conversion, validation, and storage path management
"""
import os
import mammoth
import bleach
from typing import Dict, Tuple, List
from pathlib import Path


def get_template_storage_paths(template_id: int, version_number: int) -> Dict[str, str]:
    """
    Get storage paths for template files
    
    Returns:
        dict with keys: 'originals', 'previews', 'images'
    """
    base_dir = Path("storage/templates")
    
    return {
        "originals": str(base_dir / "originals" / f"template_{template_id}_v{version_number}.docx"),
        "previews": str(base_dir / "previews" / f"template_{template_id}_v{version_number}.html"),
        "images": str(base_dir / "images" / f"template_{template_id}_v{version_number}"),
    }


def convert_docx_to_html(
    docx_path: str,
    html_output_path: str,
    images_dir: str
) -> Tuple[str, Dict[str, str]]:
    """
    Convert DOCX file to HTML
    
    Args:
        docx_path: Path to input DOCX file
        html_output_path: Path to output HTML file
        images_dir: Directory to save extracted images
    
    Returns:
        Tuple of (html_content, image_map) where image_map maps image names to paths
    """
    # Create images directory
    os.makedirs(images_dir, exist_ok=True)
    
    # Convert DOCX to HTML using mammoth
    with open(docx_path, "rb") as docx_file:
        result = mammoth.convert_to_html(
            docx_file,
            convert_image=mammoth.images.img_element(lambda image: save_image(image, images_dir))
        )
        html_content = result.value
    
    # Sanitize HTML
    html_content = bleach.clean(
        html_content,
        tags=[
            'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'ul', 'ol', 'li', 'table', 'thead', 'tbody', 'tr', 'td', 'th',
            'img', 'a', 'div', 'span'
        ],
        attributes={
            'img': ['src', 'alt', 'width', 'height'],
            'a': ['href', 'target'],
            'table': ['border', 'cellpadding', 'cellspacing'],
            'td': ['colspan', 'rowspan'],
            'th': ['colspan', 'rowspan'],
        },
        strip=True
    )
    
    # Save HTML to file
    os.makedirs(os.path.dirname(html_output_path), exist_ok=True)
    with open(html_output_path, "w", encoding="utf-8") as html_file:
        html_file.write(html_content)
    
    # Return HTML content and empty image map (mammoth handles images internally)
    return html_content, {}


def save_image(image, images_dir: str) -> Dict[str, str]:
    """
    Save image from DOCX to disk
    
    Args:
        image: Image object from mammoth
        images_dir: Directory to save images
    
    Returns:
        dict with 'src' key pointing to image path
    """
    image_path = os.path.join(images_dir, image.name)
    with open(image_path, "wb") as img_file:
        img_file.write(image.open().read())
    
    # Return relative path for HTML
    return {"src": image_path}


def validate_required_headings(html_content: str, required_headings: List[str]) -> Tuple[bool, List[str]]:
    """
    Validate that HTML content contains required headings
    
    Args:
        html_content: HTML content to validate
        required_headings: List of required heading texts (case-insensitive)
    
    Returns:
        Tuple of (is_valid, missing_headings)
    """
    if not required_headings:
        return True, []
    
    # Convert HTML to lowercase for case-insensitive matching
    html_lower = html_content.lower()
    
    missing = []
    for heading in required_headings:
        # Check for heading tags with the text
        heading_lower = heading.lower()
        found = False
        
        # Check in various heading formats
        for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            if f'<{tag}' in html_lower and heading_lower in html_lower:
                # More precise check: heading should be in the tag content
                import re
                pattern = f'<{tag}[^>]*>.*?{re.escape(heading_lower)}.*?</{tag}>'
                if re.search(pattern, html_lower, re.IGNORECASE | re.DOTALL):
                    found = True
                    break
        
        if not found:
            missing.append(heading)
    
    return len(missing) == 0, missing


