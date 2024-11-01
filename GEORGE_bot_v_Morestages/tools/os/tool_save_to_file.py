import os
import logging
from typing import List, Optional

def tool_save_to_file(
    contents: List[str],
    file_paths: Optional[List[str]] = None,
    file_names: Optional[List[str]] = None,
    content_types: Optional[List[str]] = None,  # Simplified to strings
    encoding: str = 'utf-8',
    create_folders: bool = True,
    overwrite: bool = False,
) -> dict:
    """Saves content to files, creating folders as needed."""

    if not contents:
        return {"status": "error", "message": "Contents list cannot be empty."}

    num_files = len(contents)
    file_paths = file_paths or [os.getcwd()] * num_files
    file_names = file_names or [f"content_{i}.txt" for i in range(num_files)]
    content_types = content_types or ["text"] * num_files # Default to "text"


    if not all(len(lst) == num_files for lst in [file_paths, file_names, content_types]):
        return {"status": "error", "message": "Input lists must have the same length."}

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')

    saved_files = []
    failed_files = []

    for content, file_path, file_name, content_type in zip(contents, file_paths, file_names, content_types):
        full_path = os.path.join(file_path, file_name)

        try:
            if create_folders:
                os.makedirs(os.path.dirname(full_path), exist_ok=True)

            if os.path.exists(full_path) and not overwrite:
                raise FileExistsError(f"File already exists: {full_path}")

            mode = "w"  # Default to write mode

            with open(full_path, mode, encoding=encoding) as f:
                f.write(content)

            saved_files.append(full_path)
            logging.info(f"Successfully saved: {full_path}")

        except Exception as e:
            logging.error(f"Error saving {full_path}: {e}")
            failed_files.append((full_path, str(e)))

    status = "success" if not failed_files else "partial_success" if saved_files else "failure"
    message = f"Saved {len(saved_files)} of {num_files} files." if saved_files else "No files were saved."

    return {
        "status": status,
        "message": message,
        "saved_files": saved_files,
        "failed_files": failed_files,
    }