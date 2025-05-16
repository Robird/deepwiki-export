import requests
import logging # Added for logging
from pathlib import Path # Added for Path object
from .extract_markdown_from_html import MARKDOWN_CHUNK_REGEX,DEFAULT_ENCODING,extract_chunks_from_html # DEFAULT_SEP and save_chunks_to_path removed
from .chunk_processor import save_chunks_to_dir
from .utils import derive_filename_from_chunk_content # For deriving individual Chunk filenames
# derive_filename_from_url might still be useful for the original HTML filename if desired
from .utils import derive_filename_from_url

DEEPWIKI_BASE_URL = "https://deepwiki.com/"
GITHUB_BASE_URL = "https://github.com/"

def save_markdown_from_url(
    target_url: str,
    target_output_directory: Path, # Changed from markdown_output_path
    keep_original_html: bool = False,
    # original_html_save_path is removed, HTML will be saved in target_output_directory
    # sep parameter is removed as Chunks are saved individually
    html_content_encoding: str = DEFAULT_ENCODING,
    markdown_file_encoding: str|None = None,
    request_headers: dict[str, str]|None = None,
    request_timeout: int = 30  # seconds
) -> bool|None:
    """
    Downloads HTML from a target URL (DeepWiki or GitHub), extracts content Chunks,
    and saves them as individual Markdown files in a specified directory.
    Optionally saves the original HTML in the same directory.

    The target_url must start with "https://deepwiki.com/" or "https://github.com/".
    GitHub URLs will be transformed to DeepWiki URLs. Other URLs will be rejected.

    Args:
        target_url: The URL to process (must be DeepWiki or GitHub).
        target_output_directory: Path to the directory where output files will be saved.
        keep_original_html: If True, saves the downloaded HTML in the target_output_directory.
        # original_html_save_path removed
        # sep removed
        html_content_encoding: Encoding for decoding downloaded HTML and saving original HTML.
        markdown_file_encoding: Encoding for the output Markdown file. Defaults to html_content_encoding.
        request_headers: Optional dictionary of headers for the HTTP GET request.
        request_timeout: Timeout in seconds for the HTTP GET request.

    Returns:
        True if processing was successful, False otherwise.
    """

    if MARKDOWN_CHUNK_REGEX is None:
        logging.critical("Critical Error: The global REGEX pattern is not compiled. Aborting operation.")
        return False

    download_url: str
    # Normalize target_url slightly by ensuring it doesn't have query params/fragments for prefix check
    url_for_prefix_check = target_url.split('?', 1)[0].split('#', 1)[0]

    if url_for_prefix_check.startswith(DEEPWIKI_BASE_URL):
        download_url = target_url # Use original target_url to preserve query params etc.
        logging.debug(f"Using DeepWiki URL directly: '{download_url}'")
    elif url_for_prefix_check.startswith(GITHUB_BASE_URL):
        # Preserve the part of the URL after the GITHUB_BASE_URL
        # e.g. "RooVetGit/Roo-Code" or "RooVetGit/Roo-Code?query=param"
        path_and_query = target_url[len(GITHUB_BASE_URL):]
        download_url = DEEPWIKI_BASE_URL + path_and_query
        logging.debug(f"Transformed GitHub URL '{target_url}' to DeepWiki URL: '{download_url}'")
    else:
        logging.error(f"Error: Invalid URL. Target URL must start with '{DEEPWIKI_BASE_URL}' or '{GITHUB_BASE_URL}'.")
        logging.error(f"Received URL: '{target_url}'")
        return False

    logging.debug(f"Attempting to download HTML from: '{download_url}'")
    html_text: str = ""  # Initialize to ensure definition
    try:
        # Default User-Agent, can be overridden by request_headers
        effective_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        if request_headers:
            effective_headers.update(request_headers)

        response = requests.get(download_url, headers=effective_headers, timeout=request_timeout)
        response.raise_for_status()  # Raises HTTPError for bad responses (4XX or 5XX)
        
        html_text = response.content.decode(html_content_encoding, errors='replace')
        logging.debug(f"Successfully downloaded HTML content (length: {len(html_text)} characters).")

    except requests.exceptions.Timeout:
        logging.error(f"Error: Request to '{download_url}' timed out after {request_timeout} seconds.")
        return False
    except requests.exceptions.HTTPError as e:
        logging.error(f"Error: HTTP error occurred while fetching '{download_url}': {e.response.status_code if e.response is not None else 'N/A'} {e.response.reason if e.response is not None else ''}")
        return False
    except requests.exceptions.RequestException as e:
        logging.error(f"Error: Could not download HTML from '{download_url}'. {e}")
        return False
    except Exception as e: # Catch any other unexpected error during download
        logging.error(f"An unexpected error occurred during download from '{download_url}': {e}")
        return False

    logging.debug("Extracting Chunks from HTML content...")
    markdown_chunks = extract_chunks_from_html(html_text)

    # Ensure output_dir exists
    if markdown_chunks or keep_original_html:
        try:
            logging.info(f"Ensuring output directory: '{target_output_directory}'")
            target_output_directory.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logging.critical(f"Could not create output directory '{target_output_directory}': {e}")
            return False

    if keep_original_html:
        # Save original HTML in the target_output_directory
        # Use a fixed name or derive from URL, e.g., "_original_page.html"
        # For consistency, let's use a name derived from the original URL's filename part
        original_html_filename_base = derive_filename_from_url(target_url, extension="") # Get base without .md
        if not original_html_filename_base or original_html_filename_base == "untitled":
            original_html_filename = "_original_page.html"
        else:
            original_html_filename = f"{original_html_filename_base}_original.html"
            
        save_path_html = target_output_directory / original_html_filename
        
        logging.debug(f"Attempting to save original HTML to: '{save_path_html.resolve()}'")
        try:
            # target_output_directory is assumed to be created by cli_tool.py
            # target_output_directory.mkdir(parents=True, exist_ok=True) # Redundant if cli_tool creates it

            with open(save_path_html, 'w', encoding=html_content_encoding, errors='replace') as f:
                f.write(html_text)
            logging.info(f"Original HTML saved to: '{save_path_html.resolve()}'")
        except IOError as e:
            logging.warning(f"Warning: Could not save original HTML to '{save_path_html.resolve()}'. {e}")
            # Continue processing as this is optional
        except Exception as e:
            logging.error(f"Exception while saving original HTML: {e}")    
    
    if not markdown_chunks:
        logging.info(f"No Chunks found in '{download_url}'")
        # No files will be created if no Chunks, which is fine.
        return None # 特殊值，非异常，但也没生成结果
    else:
        logging.debug(f"Found {len(markdown_chunks)} content Chunks to save.")

    actual_markdown_encoding = markdown_file_encoding if markdown_file_encoding is not None else html_content_encoding
    
    logging.debug(f"Attempting save Chunks into: '{target_output_directory.resolve()}' with encoding {actual_markdown_encoding}")
    
    save_success = save_chunks_to_dir(
        chunks=markdown_chunks,
        output_dir=target_output_directory,
        filename_deriver=derive_filename_from_chunk_content, # from .utils
        file_extension=".md", # Ensure leading dot
        encoding=actual_markdown_encoding
    )

    if save_success:
        logging.debug(f"Success all Chunks saved into '{target_output_directory.resolve()}'")
        return True
    else:
        logging.error(f"Failed to save same Chunks into '{target_output_directory.resolve()}'")
        return False

