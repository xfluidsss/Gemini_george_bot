import os
import logging
from typing import List, Tuple

tool_type_for_TOOL_MANAGER = "os"
tool_save_to_file_short_description = "Saves content to files, creating folders as needed. Handles multiple files and contents robustly."

def tool_save_to_file(
    contents: List[str],  # Requires contents to be provided
    file_names: List[str] = None,
    file_paths: List[str] = None,
    encoding: str = 'utf-8',
    create_folders: bool = True,
    overwrite: bool = False, #New: Handle overwrite behavior
) -> dict:
    """Saves content to files, creating directories as needed.  Handles multiple files robustly.

    Args:
        contents: List of strings to save to files.  *Must be provided*.
        file_names: List of file names. Defaults to 'content_n.txt' if not provided.  Must be same length as contents.
        file_paths: List of file paths. Defaults to current working directory if not provided. Must be same length as contents.
        encoding: Encoding to use for files (default: 'utf-8').
        create_folders: Create missing parent directories (default: True).
        overwrite: Overwrite existing files if True (default: False).

    Returns:
        Dictionary with 'status' ('success', 'failure', 'partial_success'), 'message', and 'saved_files' (list of successfully saved paths).
    """
    logging.info("Entering: save_to_file")

    if not contents:
        error_message = "Error: 'contents' list cannot be empty."
        logging.error(error_message)
        return {"status": "failure", "message": error_message}

    num_files = len(contents)
    file_names = file_names or [f"content_{i}.txt" for i in range(num_files)]
    file_paths = file_paths or [os.getcwd()] * num_files


    if not all(len(x) == num_files for x in [file_names, file_paths]):
      error_message = "Error: 'file_names' and 'file_paths' must be the same length as 'contents'."
      logging.error(error_message)
      return {"status": "failure", "message": error_message}


    saved_files = []
    failed_files = []
    for content, file_name, file_path in zip(contents, file_names, file_paths):
        full_path = os.path.join(file_path, file_name)
        try:
            if create_folders:
                os.makedirs(os.path.dirname(full_path), exist_ok=True)

            # Check for overwrite explicitly
            if os.path.exists(full_path) and not overwrite:
                raise IOError(f"File already exists and overwrite is False: {full_path}")

            with open(full_path, 'w', encoding=encoding) as f:
                f.write(content)
            saved_files.append(full_path)
        except IOError as e:
            logging.error(f"IOError saving {full_path}: {e}")
            failed_files.append((full_path, str(e)))  #More detail on failure
        except Exception as e:
            logging.exception(f"Unexpected error saving {full_path}: {e}") #Log full traceback for debugging
            failed_files.append((full_path, str(e)))


    if failed_files:
        message = f"Partial success: {len(saved_files)} files saved. Errors encountered: {failed_files}"
        status = "partial_success"
    else:
        message = f"Successfully saved {len(saved_files)} files: {saved_files}"
        status = "success"

    logging.info(message)
    return {"status": status, "message": message, "saved_files": saved_files}