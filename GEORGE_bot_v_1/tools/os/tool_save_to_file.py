import os
import logging
from typing import List, Optional

tool_type_for_TOOL_MANAGER = "os"
tool_tool_save_to_file_short_description = "Saves content to files and creates folders if needed."

def tool_save_to_file(
    contents: List[str],
    file_paths: Optional[List[str]] = None,
    file_names: Optional[List[str]] = None,
    content_types: Optional[List[str]] = None,  # Simplified to strings
    encoding: str = 'utf-8',
    create_folders: bool = True,
    overwrite: bool = False,
    append_mode: bool = False  # New argument for append mode
) -> dict:
    """Saves content to files, creating folders as needed.

    Args:
        contents (List[str]): List of strings to save to files.
        file_paths (Optional[List[str]]): List of paths to the directories where files should be saved.
            If not provided, the current working directory will be used for all files.
        file_names (Optional[List[str]]): List of file names. If not provided, default names like "content_0.txt",
            "content_1.txt" will be used.
        content_types (Optional[List[str]]): List of content types (e.g., "text", "json", "html").
            If not provided, "text" will be assumed for all files.
        encoding (str): Encoding to use for saving the files. Defaults to 'utf-8'.
        create_folders (bool): If True, creates necessary folders if they don't exist. Defaults to True.
        overwrite (bool): If True, overwrites existing files. Defaults to False.
        append_mode (bool): If True, appends content to existing files instead of overwriting. Defaults to False.

    Returns:
        dict: A dictionary with the following keys:
            - status: "success", "partial_success", or "failure"
            - message: A message describing the outcome.
            - saved_files: A list of paths to the successfully saved files.
            - failed_files: A list of tuples (file_path, error_message) for failed files.
    """

    if not contents:
        return {"status": "error", "message": "Contents list cannot be empty."}

    num_files = len(contents)
    file_paths = file_paths or [os.getcwd()] * num_files
    file_names = file_names or [f"content_{i}.txt" for i in range(num_files)]
    content_types = content_types or ["text"] * num_files # Default to "text"

    # Ensure all input lists have the same length
    if not all(len(lst) == num_files for lst in [file_paths, file_names, content_types]):
        return {"status": "error", "message": "Input lists must have the same length."}

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')

    saved_files = []
    failed_files = []

    for i, (content, file_path, file_name, content_type) in enumerate(zip(contents, file_paths, file_names, content_types)):
        full_path = os.path.join(file_path, file_name)

        try:
            if create_folders:
                os.makedirs(os.path.dirname(full_path), exist_ok=True)

            if os.path.exists(full_path) and not overwrite and not append_mode:  # Check for overwrite or append
                raise FileExistsError(f"File already exists: {full_path}")

            mode = "w" if not append_mode else "a"  # 'w' for overwrite, 'a' for append

            with open(full_path, mode, encoding=encoding) as f:
                # Correctly handle both \n and \\n
                content = content.replace("\\n", "\n").replace("\\\\n", "\n")
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