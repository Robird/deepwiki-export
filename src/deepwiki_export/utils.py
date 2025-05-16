# This file will contain utility functions for the deepwiki_export package.
import re
from pathlib import Path
from urllib.parse import urlparse

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