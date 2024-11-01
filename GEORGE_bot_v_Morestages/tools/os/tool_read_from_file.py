tool_type_for_TOOL_MANAGER="os"
tool_read_from_file_short_description="Reads content from a file."

def tool_read_from_file(file_path: str):
    """
    Reads content from a file.

    Args:
        file_path (str): The path to the file to be read.

    Returns:
        str: The content of the file, or an error message if the file cannot be read.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"