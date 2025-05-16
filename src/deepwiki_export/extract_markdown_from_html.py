from typing import List,TextIO
import re
import json
import html
import os

def unescape_javascript_string(s):
    """
    Unescapes a string that was a JavaScript string literal.
    Handles common escapes like \\n, \\", \\\\, and \\uXXXX.
    """
    # First, use json.loads to handle standard JSON escapes (like \\n, \\", \\\\, \\/, \\b, \\f, \\r, \\t, \\uXXXX)
    # We need to wrap the string in double quotes to make it a valid JSON string.
    try:
        # Replace any literal newlines or other problematic chars if not already escaped
        # This step might be tricky if the regex doesn't perfectly isolate the JS string literal content
        # For now, assume the regex gives us the "internal" part of the JS string.
        return json.loads(f'"{s}"')
    except json.JSONDecodeError:
        # Fallback for more complex cases or if not perfectly a JSON string part
        # This is a more aggressive unescape and might not always be correct
        # For example, it might unescape things that shouldn't be.
        # A truly robust solution might involve a proper JS parser or more specific regex.
        print("Warning: JSON decoding failed for a Chunk. Falling back to HTML unescape then unicode_escape.")
        temp_unescaped = html.unescape(s) # Handle HTML entities first if any
        try:
            # This handles \uXXXX, \n, \t etc. but can be problematic if there are raw backslashes
            # not part of a valid escape sequence.
            return temp_unescaped.encode('latin-1', 'backslashreplace').decode('unicode-escape')
        except UnicodeDecodeError:
            print("Warning: unicode_escape decoding failed. Returning as is after html.unescape.")
            return temp_unescaped


# Regex to find self.__next_f.push([1, "string_content"]) or self.__next_f.push([0, "string_content"]) etc.
# It captures the number (e.g., 1 or 0) in group 1, and the string content in group 2.
# This regex handles escaped quotes (\\") and other escaped characters (\\.) inside the string.
MARKDOWN_CHUNK_REGEX = re.compile(r'self\.__next_f\.push\(\[(\d+),\s*"(#(?:[^"\\]|\\.)+)"\]\)')
def extract_chunks_from_html(html_content:str) -> List[str]:
    """
    Extracts and concatenates Markdown content from self.__next_f.push calls
    in an HTML file.
    """    
    markdown_chunks = []
    for match in re.finditer(MARKDOWN_CHUNK_REGEX, html_content):
        # group(1) is the number (e.g., 1), group(2) is the escaped string content
        chunk_type = match.group(1) 
        escaped_markdown_chunk = match.group(2)
        
        # We are interested in the Chunks that are likely Markdown content.
        # Based on user's regex, these are typically associated with the number 1 as the first arg.
        # And often start with Markdown-like syntax.
        # For now, let's assume all string content pushed with [1, "..."] is relevant.
        unescaped_chunk = unescape_javascript_string(escaped_markdown_chunk)
        markdown_chunks.append(unescaped_chunk)
        if chunk_type != "1":
            print(f"  Warning! Unknown {chunk_type=} {unescaped_chunk[:8]}...{unescaped_chunk[-8:]}")
    return markdown_chunks

DEFAULT_ENCODING = 'utf-8'

def extract_chunks_from_html_file(fp:TextIO) -> List[str]:
    return extract_chunks_from_html(fp.read())

def extract_chunks_from_html_path(file_path:str, encoding:str=DEFAULT_ENCODING) -> List[str]:
    with open(file_path, 'rt', encoding=encoding) as fp:
        return extract_chunks_from_html_file(fp)

DEFAULT_SEP = "\n---\n"

def chunks_to_str(markdown_chunks:List[str], sep:str=DEFAULT_SEP) -> str:
    """Joins a list of string Chunks into a single string using a separator."""
    return sep.join(markdown_chunks)

def save_chunks_to_file(markdown_chunks:List[str], fp:TextIO, sep:str=DEFAULT_SEP) -> None:
    """Writes a list of string Chunks to an open file object, separated by sep."""
    not_first = False
    for chunk in markdown_chunks:
        if not_first:
            fp.write(sep)
        fp.write(chunk)
        not_first=True

def save_chunks_to_path(markdown_chunks:List[str],file_path:str,sep:str=DEFAULT_SEP, encoding:str=DEFAULT_ENCODING) -> None:
    """Saves a list of string Chunks to a new file at the given path."""
    if markdown_chunks:
        # Ensure directory exists
        output_dir = os.path.dirname(file_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        with open(file_path,'wt', encoding=encoding) as f:
            save_chunks_to_file(markdown_chunks,f,sep)

def convert_html_to_markdown(html_path:str,markdown_path:str,sep=DEFAULT_SEP,html_encoding=DEFAULT_ENCODING,markdown_encoding=DEFAULT_ENCODING) -> None:
    chunks = extract_chunks_from_html_path(html_path,encoding=html_encoding)
    save_chunks_to_path(chunks,markdown_path,sep=sep,encoding=markdown_encoding)
