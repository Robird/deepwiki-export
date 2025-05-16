import logging
from pathlib import Path
import sys
from typing import List, Callable

# Assuming utils.py will have derive_filename_from_chunk_content
# from .utils import derive_filename_from_chunk_content # This will be passed as a callable

def save_chunks_to_dir(
    chunks: List[str],
    output_dir: Path,
    filename_deriver: Callable[[str, int], str], 
    file_extension: str = ".md",
    encoding: str = "utf-8"
) -> bool:
    """
    Saves a list of string Chunks into individual files within a specified directory.

    Args:
        Chunks: A list of strings, where each string is a Chunk of content.
        output_dir: The pathlib.Path object representing the directory to save files in.
                    This function assumes the directory has already been created by the caller.
        filename_deriver: A callable that takes Chunk content (str) and its index (int)
                          and returns a sanitized base filename (str, without extension).
        file_extension: The file extension to use for the saved files (e.g., ".md").
                          It should include the leading dot if desired (e.g., ".md").
        encoding: The encoding to use when writing files.

    Returns:
        True if all Chunks were saved successfully, False otherwise.
    """    
    if not chunks:
        logging.debug(f"No Chunks provided to save into: '{output_dir}'")
        return True # Considered success as there's nothing to fail on.
    
    all_successful = True
    for i, chunk_content in enumerate(chunks):
        base_filename = f"chunk_{i}_unnamed" # Initialize base_filename before try block
        try:
            base_filename = filename_deriver(chunk_content, i)
            
            # The filename_deriver should ideally handle empty/default cases.
            # But as a final fallback here:
            if not base_filename:
                logging.warning(
                    f"Filename deriver returned an empty string for Chunk {i}. "
                    f"Using fallback: 'chapter_{i + 1}'."
                )
                base_filename = f"chapter_{i + 1}"
            
            # Ensure file_extension includes a dot if it's meant to be an extension
            actual_extension = file_extension if file_extension.startswith('.') else f".{file_extension}"
            
            output_file_path = output_dir / (base_filename + actual_extension)
            
            logging.debug(f"Attempting to save Chunk {i} to '{output_file_path}'")
            with open(output_file_path, "w", encoding=encoding, errors="replace") as f:
                f.write(chunk_content)
            logging.info(f"    Saved '{output_file_path.name}'")

        except Exception as e:
            logging.error(f"Failed to save Chunk {i} (derived base: '{base_filename}') to '{output_dir}': {e}")
            all_successful = False
            # Optionally, decide if one failure should stop the whole process or continue
            # For now, it continues and reports overall success/failure at the end.
            
    if all_successful:
        logging.info(f"All {len(chunks)} Chunks saved into: '{output_dir}'")
    else:
        logging.error(f"Some Chunks failed to save into: '{output_dir}'")
        
    return all_successful