# cli_tool.py

import typer
import sys # Added for sys.exit and sys.stderr
from pathlib import Path
from typing import Optional, Dict
import logging # Added for logging

from .extract_markdown_from_html import DEFAULT_ENCODING,DEFAULT_SEP,MARKDOWN_CHUNK_REGEX
from .save_markdown_from_url import save_markdown_from_url
from .utils import derive_filename_from_url

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
    output_path: Optional[Path] = typer.Argument(
        None,
        help="Output path. Can be a file or a directory. "
             "If a directory, filename is derived from URL. "
             "If not provided, saves to current directory with URL-derived filename.",
        dir_okay=True,
        file_okay=True,
        writable=True, # Typer checks if parent dir (if path exists) or current dir (if path is new) is writable
        resolve_path=True, # Resolve ., .., ~ etc. to absolute paths
        show_default=False # Custom help text is better
    ),
    keep_html: bool = typer.Option(
        False, 
        "--keep-html",
        help="Save the original downloaded HTML file."
    ),
    html_output: Optional[Path] = typer.Option(
        None,
        "--html-output",
        metavar="PATH_OR_DIR",
        help="Output path or directory for original HTML. Used only if --keep-html is set. "
             "If a directory, filename is derived from URL using '.html' extension. "
             "If --keep-html is set and this is not provided, path is derived from the final Markdown output path.",
        dir_okay=True,
        file_okay=True,
        writable=True,
        resolve_path=True,
        show_default=False
    ),
    separator: str = typer.Option(
        DEFAULT_SEP,
        "--separator", "--sep",
        metavar="STRING",
        help=f"Separator for Markdown chunks. Use '\\n' for newlines. Default: '{DEFAULT_SEP.replace('\n', r'\n')}'"
    ),
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
    # --- Determine final output paths ---

    derived_md_filename = derive_filename_from_url(url, ".md")

    if output_path is None:
        final_markdown_path = Path.cwd() / derived_md_filename
        logging.debug(f"Info: No output path specified. Defaulting Markdown output to: {final_markdown_path.resolve()}")
    elif output_path.is_dir(): # User provided a directory
        # Typer with resolve_path=True has made output_path absolute.
        # No need to call mkdir here if using writable=True, Typer checks parent.
        # However, explicit mkdir is safer if writable=True isn't fully comprehensive.
        output_path.mkdir(parents=True, exist_ok=True)
        final_markdown_path = output_path / derived_md_filename
    else: # User provided a file path
        final_markdown_path = output_path
        # Ensure parent directory exists for the file path if it's not the current dir
        final_markdown_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Determine final_original_html_save_path for the core function
    # The core function will use markdown_output_path to derive if this is None
    actual_original_html_save_path: Optional[Path] = None
    if keep_html:
        if html_output is None:
            # Pass None; core function will derive from final_markdown_path
            actual_original_html_save_path = None 
            logging.debug(f"Info: --keep-html is set; --html-output not specified. Original HTML path will be derived from: {final_markdown_path.name}")
        elif html_output.is_dir():
            html_output.mkdir(parents=True, exist_ok=True)
            derived_html_filename = derive_filename_from_url(url, ".html")
            actual_original_html_save_path = html_output / derived_html_filename
        else: # html_output is intended as a file path
            actual_original_html_save_path = html_output
            actual_original_html_save_path.parent.mkdir(parents=True, exist_ok=True)
    
    final_request_headers: Optional[Dict[str, str]] = None
    if user_agent:
        final_request_headers = {"User-Agent": user_agent}

    processed_separator = separator.replace("\\n", "\n")

    # Call the core processing function
    success = save_markdown_from_url(
        target_url=url,
        markdown_output_path=str(final_markdown_path),
        keep_original_html=keep_html,
        original_html_save_path=str(actual_original_html_save_path) if actual_original_html_save_path else None, # Can be None
        sep=processed_separator,
        html_content_encoding=html_encoding,
        markdown_file_encoding=md_encoding,
        request_headers=final_request_headers,
        request_timeout=timeout
    )

    if success:
        logging.info(f"Success: Processed '{url}' and saved Markdown to '{final_markdown_path.resolve()}'.")
        if keep_html and actual_original_html_save_path:
             logging.info(f"Original HTML saved to '{actual_original_html_save_path.resolve()}'.")
        elif keep_html and html_output is None: # Path was derived by core function
             derived_html_path_for_info = final_markdown_path.with_name(f"{final_markdown_path.stem}_original.html")
             logging.info(f"Original HTML (path derived) saved to '{derived_html_path_for_info.resolve()}'.")

        sys.exit(0)
    else:
        logging.error(f"Error: Failed to process '{url}'. See messages above for details.")
        sys.exit(1)

def _main(*args):
    app()

if __name__ == "__main__":
    # This makes the script executable.
    # For actual distribution, you'd set up an entry point in pyproject.toml or setup.py
    app()