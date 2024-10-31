tool_type_for_TOOL_MANAGER = "os"
tool_get_directory_structure_short_description = """Get directory structure with formatted tree view and contents, including both full and relative paths."""

import os
import json
from pathlib import Path

def tool_get_directory_structure(directory: str = "../../", levels: int = 2,
                                 include_contents: bool = False,
                                 print_output: bool = True):
    """Gets directory structure and optionally prints or returns it.

    Args:
        directory (str, optional): The directory to analyze. Defaults to "../../".
        levels (int, optional): The number of directory levels to show. Defaults to 2.
        include_contents (bool, optional): Whether to include file contents. Defaults to False.
        print_output (bool, optional): Whether to print the output or return it as a dictionary.
                                        Defaults to True.
    """

    def _format_size(size_bytes):
        """Format file size."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    def _get_relative_path(full_path, base_path):
        """Get relative path from base directory."""
        try:
            return os.path.relpath(full_path, base_path)
        except ValueError:
            return full_path  # Return full path if relative path cannot be computed

    def _walk_directory(dir_path, base_path, level=0, indent=""):
        """Recursive directory walk with formatted output, excluding __pycache__."""
        if level > levels:
            return ""

        output = ""
        try:
            entries = sorted(os.scandir(dir_path), key=lambda e: (not e.is_dir(), e.name.lower()))
            for entry in entries:
                if entry.name == "__pycache__" or entry.name.startswith('.'):
                    continue  # Skip __pycache__ and hidden directories/files

                relative_path = _get_relative_path(entry.path, base_path)

                if entry.is_file():
                    stat = entry.stat()
                    size = _format_size(stat.st_size)
                    modified_time = os.path.getmtime(entry.path)
                    modified_str = f"Modified: {os.path.getctime(entry.path):.0f}"

                    output += (f"{indent}📄 {entry.name} ({size})\n"
                               f"{indent}  Full path: {entry.path}\n"
                               f"{indent}  Relative path: {relative_path}\n"
                               f"{indent}  {modified_str}\n")

                    if include_contents:
                        try:
                            with open(entry.path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                output += f"{indent}  Content Preview:\n"
                                # Show first 500 characters of content with line breaks
                                preview = content[:500].replace('\n', f'\n{indent}    ')
                                output += f"{indent}    {preview}\n"
                                if len(content) > 500:
                                    output += f"{indent}    ... (truncated)\n"
                        except Exception as e:
                            output += f"{indent}  ⚠️ Error reading file: {str(e)}\n"

                elif entry.is_dir():
                    output += (f"{indent}📁 {entry.name}/\n"
                               f"{indent}  Full path: {entry.path}\n"
                               f"{indent}  Relative path: {relative_path}\n")
                    output += _walk_directory(entry.path, base_path, level + 1, indent + "  ")
        except PermissionError:
            output += f"{indent}⚠️ Permission denied: {dir_path}\n"
        except Exception as e:
            output += f"{indent}⚠️ Error accessing directory: {str(e)}\n"

        return output

    # Normalize and resolve the directory path
    directory = os.path.abspath(os.path.expanduser(directory))

    output = "📊 Directory Analysis Summary\n"
    output += "=" * 30 + "\n"
    output += f"Base Directory: {directory}\n"

    total_size = 0
    file_count = 0
    dir_count = 0
    file_types = {}
    largest_files = []

    # Collect statistics
    for root, dirs, files in os.walk(directory):
        # Remove hidden directories and __pycache__ in place
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']

        if root.count(os.sep) - directory.count(os.sep) > levels:
            continue

        dir_count += len(dirs)
        file_count += len(files)

        for file in files:
            if file.startswith('.'):
                continue

            file_path = os.path.join(root, file)
            try:
                file_size = os.path.getsize(file_path)
                total_size += file_size

                # Track file types
                ext = os.path.splitext(file)[1].lower() or 'no extension'
                file_types[ext] = file_types.get(ext, 0) + 1

                # Track largest files
                largest_files.append((file_path, file_size))
                largest_files.sort(key=lambda x: x[1], reverse=True)
                largest_files = largest_files[:5]  # Keep only top 5
            except (OSError, PermissionError):
                continue

    output += f"\n📈 Statistics:\n"
    output += f"Total Folders: {dir_count:,}\n"
    output += f"Total Files: {file_count:,}\n"
    output += f"Total Size: {_format_size(total_size)}\n"

    output += "\n📁 File Types:\n"
    for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True):
        output += f"{ext}: {count:,} files\n"

    output += "\n📦 Largest Files:\n"
    for file_path, size in largest_files:
        rel_path = _get_relative_path(file_path, directory)
        output += f"{_format_size(size)}: {rel_path}\n"

    output += "\n📂 Directory Structure:\n"
    output += "=" * 30 + "\n"
    output += _walk_directory(directory, directory)

    if print_output:
        print(output)
    else:
        return {
            'full_summary': output,
            'statistics': {
                'total_dirs': dir_count,
                'total_files': file_count,
                'total_size': total_size,
                'file_types': file_types,
                'largest_files': [(path, size) for path, size in largest_files]
            }
        }


if __name__ == "__main__":
    # Example usage:
    tool_get_directory_structure(directory="../../", levels=2, include_contents=False)