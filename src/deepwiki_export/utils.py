# This file will contain utility functions for the deepwiki_export package.
import re
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional

# --- Helper Function for Filename Derivation (MOVED FROM cli_tool.py) ---
def sanitize_filename_component(name: str) -> str:
    """Sanitizes a string component to be safe for filenames."""
    if not name:
        return "untitled"
    # Replace sequences of non-alphanumeric characters (excluding hyphen, period, underscore) with a single underscore
    name = re.sub(r'[^a-zA-Z0-9._-]+', '_', name)
    name = name.strip('._') # Remove leading/trailing underscores or periods
    # Collapse multiple underscores that might have been formed
    name = re.sub(r'_+', '_', name)
    if not name or all(c in '._' for c in name): # If only dots/underscores remain or empty
        return "untitled"
    return name

def derive_filename_from_url(url_str: str, extension: str = ".md") -> str:
    """Derives a sanitized filename from a URL."""
    parsed_url = urlparse(url_str)
    path_obj = Path(parsed_url.path)
    
    name_base = path_obj.stem
    if name_base.startswith('.'): # Handle hidden-like file stems e.g. ".config" -> "config"
        name_base = name_base[1:]

    if not name_base or name_base == '/':
        path_segments = [seg for seg in path_obj.parts if seg and seg != '/']
        if path_segments:
            name_base_segment = path_segments[-1]
            # If this segment itself looks like a filename (e.g., "archive.tar"), get its stem
            name_base_segment_stem = Path(name_base_segment).stem
            if name_base_segment_stem and not name_base_segment_stem.startswith('.'):
                 name_base = name_base_segment_stem
            elif name_base_segment_stem.startswith('.'): # e.g. ".bashrc" -> "bashrc"
                 name_base = name_base_segment_stem[1:]
            else: # Fallback if stem is empty
                 name_base = name_base_segment
        else:
            name_base = parsed_url.netloc
            if not name_base: # Should not happen with valid http URLs
                name_base = "untitled_url"


    sanitized_name_base = sanitize_filename_component(name_base)
    max_len_base = 50
    return f"{sanitized_name_base[:max_len_base]}{extension}"

def derive_username_from_url(url_str: str) -> Optional[str]:
    """
    Derives a sanitized username from a GitHub URL.

    Args:
        url_str: The URL string.

    Returns:
        A sanitized username string if the URL is a GitHub URL and username can be extracted,
        otherwise None.
    """
    try:
        parsed_url = urlparse(url_str)
        path_parts = [part for part in parsed_url.path.strip('/').split('/') if part]
        
        # For specific known domains like github.com, deepwiki.com
        if parsed_url.netloc.lower() in ["github.com", "deepwiki.com"]:
            if len(path_parts) >= 1:
                # The first part of the path is considered the username/org
                return sanitize_filename_component(path_parts[0])
        # For other generic URLs, if path structure suggests user/repo (at least two parts)
        elif len(path_parts) >= 2:
            # Assume the first part is user-like if there are at least two path segments
            return sanitize_filename_component(path_parts[0])
            
    except Exception: # Broad exception to catch any parsing errors
        pass # Failed to parse or extract, will return None
    return None

def derive_reponame_from_url(url_str: str, default_name: str = "untitled_export") -> str:
    """
    Derives a sanitized repository name or a general identifier from a URL.
    For GitHub URLs, it attempts to extract the repository name.
    For other URLs, it uses parts of the path or hostname.

    Args:
        url_str: The URL string.
        default_name: The default name to return if no suitable name can be derived.

    Returns:
        A sanitized string suitable for use as a directory name.
    """
    name_to_sanitize = ""
    try:
        parsed_url = urlparse(url_str)
        path_parts = [part for part in parsed_url.path.strip('/').split('/') if part]

        if parsed_url.netloc.lower() == "github.com":
            if len(path_parts) >= 2:
                repo_name = path_parts[1]
                if repo_name.lower().endswith(".git"):
                    repo_name = repo_name[:-4]
                name_to_sanitize = repo_name
            elif len(path_parts) == 1: # Only username present, use it as a fallback
                name_to_sanitize = path_parts[0]
        
        if not name_to_sanitize and path_parts:
            # Use the last significant part of the path for non-GitHub URLs or if repo name missing
            name_to_sanitize = path_parts[-1]
            # If it looks like a filename, take its stem
            if '.' in name_to_sanitize:
                 name_to_sanitize = Path(name_to_sanitize).stem
        
        if not name_to_sanitize and parsed_url.netloc:
            # Fallback to hostname if path is empty or didn't yield a name
            name_to_sanitize = parsed_url.netloc.replace("www.", "")

    except Exception:
        pass # Fall through to default if parsing fails

    if not name_to_sanitize:
        name_to_sanitize = default_name
        
    sanitized = sanitize_filename_component(name_to_sanitize)
    return sanitized if sanitized else default_name # Ensure not empty after sanitization

def derive_filename_from_chunk_content(content: str, index: int, max_length: int = 50) -> str:
    """
    Derives a sanitized filename from the first line of a content chunk.
    Falls back to "chapter_{index+1}" if the first line is unsuitable.

    Args:
        content: The content chunk string.
        index: The index of the chunk (0-based), used for fallback naming.
        max_length: The maximum length for the derived filename (before extension).

    Returns:
        A sanitized string suitable for use as a base filename.
    """
    first_line = content.split('\n', 1)[0].strip()
    
    # Remove common markdown heading characters like #, ##, etc. from the beginning
    first_line_cleaned = re.sub(r"^\s*#+\s*", "", first_line).strip()

    base_name = ""
    if first_line_cleaned and len(first_line_cleaned) > 3: # Arbitrary threshold for a meaningful title
        base_name = sanitize_filename_component(first_line_cleaned)
        if len(base_name) > max_length:
            base_name = base_name[:max_length]
        # Further check if sanitization resulted in empty or just dots/underscores
        if not base_name or all(c in '._' for c in base_name):
            base_name = "" # Reset to trigger fallback

    if not base_name:
        base_name = f"chapter_{index + 1}"
        
    # Final sanitization pass for the fallback name too, though usually not needed for "chapter_N"
    final_sanitized_name = sanitize_filename_component(base_name)

    # Ensure it's not empty after all, though sanitize_filename_component should handle returning "untitled"
    return final_sanitized_name if final_sanitized_name else f"chapter_{index + 1}_fallback"