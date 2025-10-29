"""Text processing utilities."""

import hashlib
import re


def normalize_text(text: str) -> str:
    """Normalize text by removing extra whitespace and cleaning up.
    
    Args:
        text: Input text
        
    Returns:
        Normalized text
        
    Example:
        >>> normalize_text("  Hello\\n\\n  World  ")
        'Hello World'
    """
    # Replace multiple whitespace with single space
    text = re.sub(r"\s+", " ", text)
    # Strip leading/trailing whitespace
    text = text.strip()
    return text


def make_id(text: str, prefix: str = "") -> str:
    """Generate a deterministic ID from text using hash.
    
    Args:
        text: Input text to hash
        prefix: Optional prefix for the ID
        
    Returns:
        Deterministic ID string
        
    Example:
        >>> make_id("Hello world")
        '3e25960a79dbc6'
        >>> make_id("Hello world", prefix="doc")
        'doc|3e25960a79dbc6'
    """
    # Create hash of text
    hash_obj = hashlib.sha256(text.encode("utf-8"))
    hash_str = hash_obj.hexdigest()[:14]  # Take first 14 chars
    
    if prefix:
        return f"{prefix}|{hash_str}"
    return hash_str
