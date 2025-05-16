# cli_tool.py

import typer
import sys # Added for sys.exit and sys.stderr
from pathlib import Path
from typing import Optional, Dict
import logging # Added for logging

from .extract_markdown_from_html import DEFAULT_ENCODING,DEFAULT_SEP,MARKDOWN_CHUNK_REGEX
from .save_markdown_from_url import save_markdown_from_url
from .utils import (
    derive_filename_from_url, # Still used for fallback or original HTML name
    derive_username_from_url,
    derive_reponame_from_url
)

# --- Version ---
__version__ = "0.2.0" # Initial version for the CLI tool

# Filename derivation functions moved to .utils

# --- Typer CLI Application ---
app = typer.Typer(
    name="deepwiki-export",
    help="Downloads and processes content from DeepWiki/GitHub URLs into Markdown.",
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
    pretty_exceptions_enable=False # Disable rich exceptions
)

def version_callback(value: bool):
    if value:
        logging.info(f"{app.info.name} version: {__version__}")
        sys.exit()

@app.command()
def main(
    url: str = typer.Argument(
        ...,
        help="The GitHub or DeepWiki URL to process. GitHub URLs are transformed to DeepWiki."
    ),
    output_base_dir: Path = typer.Option(
        Path("."), # Default to current directory
        "--output-base-dir", "-o",
        help="Base directory. A new subdirectory (e.g., username/reponame or derived_name) will be created here to store the output files.",
        dir_okay=True,
        file_okay=False, # Must be a directory
        writable=True,
        resolve_path=True,
        show_default=True
    ),
    keep_html: bool = typer.Option(
        False,
        "--keep-html",
        help="Save the original downloaded HTML file (will be saved in the auto-generated output subdirectory)."
    ),
    # html_output option is removed as HTML will be saved in the same auto-generated subdirectory
    # Separator option is removed as chunks are saved into individual files
    html_encoding: str = typer.Option(
        DEFAULT_ENCODING,
        "--html-encoding",
        metavar="ENCODING",
        help=f"Encoding of the downloaded HTML content. Default: {DEFAULT_ENCODING}"
    ),
    md_encoding: Optional[str] = typer.Option(
        None,
        "--md-encoding",
        metavar="ENCODING",
        help="Encoding for the output Markdown file. Defaults to HTML encoding if not set."
    ),
    user_agent: Optional[str] = typer.Option(
        None,
        "--user-agent",
        metavar="STRING",
        help="Custom User-Agent string for the HTTP request. Overrides the default."
    ),
    timeout: int = typer.Option(
        30,
        "--timeout",
        min=1,
        metavar="SECONDS",
        help="HTTP request timeout in seconds. Default: 30"
    ),
    version: Optional[bool] = typer.Option(
        None, "--version", callback=version_callback, is_eager=True, help="Show application version and exit."
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Enable verbose output (DEBUG level logging).",
        show_default=False
    )
):
    """
    Downloads and processes content from specified DeepWiki or GitHub URLs
    and saves specific extracted JavaScript data as a Markdown file.
    GitHub URLs are automatically transformed to DeepWiki URLs.
    """
    # Configure logging
    log_level = logging.DEBUG if verbose else logging.INFO
    # Basic configuration outputs to stderr by default. For stdout:
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s' if verbose else '%(message)s', stream=sys.stdout)
    # For more granular control, get a specific logger:
    # logger = logging.getLogger("deepwiki_export")
    # logger.setLevel(log_level)
    # handler = logging.StreamHandler(sys.stdout) # Output to stdout
    # formatter = logging.Formatter('%(levelname)s: %(message)s' if verbose else '%(message)s')
    # handler.setFormatter(formatter)
    # if not logger.hasHandlers(): # Avoid adding multiple handlers if re-run/imported
    #     logger.addHandler(handler)


    if MARKDOWN_CHUNK_REGEX is None:
        logging.critical("Critical Configuration Error: The core REGEX pattern failed to compile. Cannot proceed.")
        sys.exit(2)
    # --- Determine final output directory ---
    logging.debug(f"Base output directory specified: {output_base_dir.resolve()}")

    username_part = derive_username_from_url(url)
    reponame_part = derive_reponame_from_url(url) # This will provide a sanitized name
    logging.debug(f"Derived username_part: '{username_part}'")
    logging.debug(f"Derived reponame_part: '{reponame_part}'")

    if username_part:
        target_subdir_path = Path(username_part) / reponame_part
    else:
        target_subdir_path = Path(reponame_part)
    
    # output_base_dir is already resolved by Typer
    final_output_directory = output_base_dir / target_subdir_path
    
    logging.info(f"Ensuring output directory exists: {final_output_directory.resolve()}")
    try:
        final_output_directory.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logging.critical(f"Could not create output directory {final_output_directory.resolve()}: {e}")
        sys.exit(3)
        
    # actual_original_html_save_path is no longer needed here,
    # save_markdown_from_url will handle saving HTML inside final_output_directory if keep_html is True.
    
    final_request_headers: Optional[Dict[str, str]] = None
    if user_agent:
        final_request_headers = {"User-Agent": user_agent}

    # Call the core processing function
    success = save_markdown_from_url(
        target_url=url,
        # Pass the final directory to save_markdown_from_url
        target_output_directory=final_output_directory,
        keep_original_html=keep_html,
        # original_html_save_path is now handled internally by save_markdown_from_url
        # sep is removed
        html_content_encoding=html_encoding,
        markdown_file_encoding=md_encoding,
        request_headers=final_request_headers,
        request_timeout=timeout
    )

    if success:
        logging.info(f"Success: Processed '{url}'. Markdown files saved in directory '{final_output_directory.resolve()}'.")
        if keep_html:
             # The actual path of the HTML file will be logged by save_markdown_from_url
             logging.info(f"Original HTML (if saved) is also in '{final_output_directory.resolve()}'.")
        
        sys.exit(0)
    else:
        logging.error(f"Error: Failed to process '{url}'. Output might be incomplete in '{final_output_directory.resolve()}'. See messages above for details.")
        sys.exit(1)

def _main(*args):
    app()

if __name__ == "__main__":
    # This makes the script executable.
    # For actual distribution, you'd set up an entry point in pyproject.toml or setup.py
    app()