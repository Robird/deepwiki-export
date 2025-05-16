import requests
import os
import logging # Added for logging
from .extract_markdown_from_html import MARKDOWN_CHUNK_REGEX,DEFAULT_SEP,DEFAULT_ENCODING,extract_chunks_from_html,save_chunks_to_path

DEEPWIKI_BASE_URL = "https://deepwiki.com/"
GITHUB_BASE_URL = "https://github.com/"

def save_markdown_from_url(
    target_url: str,
    markdown_output_path: str,
    keep_original_html: bool = False,
    original_html_save_path: str|None = None,
    sep: str = DEFAULT_SEP,
    html_content_encoding: str = DEFAULT_ENCODING,
    markdown_file_encoding: str|None = None,
    request_headers: dict[str, str]|None = None,
    request_timeout: int = 30  # seconds
) -> bool:
    """
    Downloads HTML from a target URL (DeepWiki or GitHub), extracts content chunks,
    and saves them as a Markdown file. Optionally saves the original HTML.

    The target_url must start with "https://deepwiki.com/" or "https://github.com/".
    GitHub URLs will be transformed to DeepWiki URLs. Other URLs will be rejected.

    Args:
        target_url: The URL to process (must be DeepWiki or GitHub).
        markdown_output_path: Path to save the processed Markdown file.
        keep_original_html: If True, saves the downloaded HTML.
        original_html_save_path: Path to save the original HTML.
                                 If keep_original_html is True and this is None,
                                 it defaults to markdown_output_path with "_original.html" suffix.
        sep: Separator for joining Markdown chunks.
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
        logging.debug(f"Using DeepWiki URL directly: {download_url}")
    elif url_for_prefix_check.startswith(GITHUB_BASE_URL):
        # Preserve the part of the URL after the GITHUB_BASE_URL
        # e.g. "RooVetGit/Roo-Code" or "RooVetGit/Roo-Code?query=param"
        path_and_query = target_url[len(GITHUB_BASE_URL):]
        download_url = DEEPWIKI_BASE_URL + path_and_query
        logging.debug(f"Transformed GitHub URL ({target_url}) to DeepWiki URL: {download_url}")
    else:
        logging.error(f"Error: Invalid URL. Target URL must start with '{DEEPWIKI_BASE_URL}' or '{GITHUB_BASE_URL}'.")
        logging.error(f"Received URL: {target_url}")
        return False

    logging.debug(f"Attempting to download HTML from: {download_url}")
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
        logging.error(f"Error: Request to {download_url} timed out after {request_timeout} seconds.")
        return False
    except requests.exceptions.HTTPError as e:
        logging.error(f"Error: HTTP error occurred while fetching {download_url}: {e.response.status_code if e.response is not None else 'N/A'} {e.response.reason if e.response is not None else ''}")
        return False
    except requests.exceptions.RequestException as e:
        logging.error(f"Error: Could not download HTML from {download_url}. {e}")
        return False
    except Exception as e: # Catch any other unexpected error during download
        logging.error(f"An unexpected error occurred during download from {download_url}: {e}")
        return False


    if keep_original_html:
        save_path_html = original_html_save_path
        if not save_path_html:
            base, ext = os.path.splitext(markdown_output_path)
            save_path_html = base + "_original.html"
        
        logging.debug(f"Attempting to save original HTML to: {save_path_html}")
        try:
            html_output_dir = os.path.dirname(save_path_html)
            if html_output_dir and not os.path.exists(html_output_dir): # Ensure dir_name is not empty
                os.makedirs(html_output_dir, exist_ok=True)
                logging.debug(f"Created directory for original HTML: {html_output_dir}")

            with open(save_path_html, 'w', encoding=html_content_encoding, errors='replace') as f:
                f.write(html_text)
            logging.debug(f"Original HTML saved successfully to: {save_path_html}")
        except IOError as e:
            logging.warning(f"Warning: Could not save original HTML to {save_path_html}. {e}")
            # Continue processing as this is optional
        except Exception as e:
            logging.error(f"An unexpected error occurred while saving original HTML: {e}")


    logging.debug("Extracting chunks from HTML content...")
    markdown_chunks = extract_chunks_from_html(html_text)
    
    if not markdown_chunks:
        logging.debug(f"No specific content chunks found in the HTML from {download_url} using the defined REGEX.")
        # save_chunks_to_path will create an empty file if markdown_chunks is empty.
    else:
        logging.debug(f"Found {len(markdown_chunks)} content chunks.")

    actual_markdown_encoding = markdown_file_encoding if markdown_file_encoding is not None else html_content_encoding
    
    logging.debug(f"Attempting to save Markdown to: {markdown_output_path} with encoding {actual_markdown_encoding}")
    try:
        save_chunks_to_path(markdown_chunks, markdown_output_path, sep=sep, encoding=actual_markdown_encoding)
        logging.debug("Markdown file saved successfully.")
        return True
    except IOError as e:
        logging.error(f"Error: Could not save Markdown to {markdown_output_path}. {e}")
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred while saving Markdown: {e}")
        return False

