import os

from rich import print
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

# Constants
SUMMARY_FILENAME = "summary.txt"
DEPTH_MODE = True  # Set to True to traverse all folders

# Exclusion lists
EXCLUDED_FILES = [
    "summary.txt",
    "Better_summariser.py",  # Or whatever your main script name is
    os.path.basename(__file__)  # Current script
]
EXCLUDED_FILE_EXTENSIONS = [
    ".iml", ".iws", ".ipr", ".keymap", ".xml", ".log", ".txt", ".pyc", ".pyd",
    ".egg-info", ".pth", ".egg"
]
EXCLUDED_DIRS = [".idea"]


def summarize_directory(directory, depth_mode=DEPTH_MODE):
    """Summarizes the contents of a directory."""
    summary_filepath = os.path.join(directory, SUMMARY_FILENAME)
    print_directory_tree(directory)

    with open(summary_filepath, "w", encoding="utf-8") as summary_file:
        write_tree_structure_to_file(summary_file, directory)
        summary_file.write(f"## Summary of '{directory}'\n\n")

        for root, dirs, files in os.walk(directory):
            if not depth_mode:
                dirs[:] = []  # Stop further traversal if depth_mode is False

            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

            for file in files:
                if file not in EXCLUDED_FILES and not any(file.endswith(ext) for ext in EXCLUDED_FILE_EXTENSIONS):
                    file_path = os.path.join(root, file)
                    summary_file.write(f"File: {file} ({file_path})\n")
                    write_file_content(summary_file, file_path)

        write_tree_structure_to_file(summary_file, directory)

    print(f"[bold green]Summary created: '{summary_filepath}'[/]")
    print_summary_from_file(summary_filepath)
    line_count = count_lines_in_file(summary_filepath)
    print(f"[bold blue]Total lines: {line_count}[/]")


def write_tree_structure_to_file(summary_file, directory):
    summary_file.write("## Directory Tree\n\n")
    _build_tree_for_file(directory, 0, summary_file)
    summary_file.write("\n")


def _build_tree_for_file(directory, level, summary_file):
    items = [item for item in os.listdir(directory)
             if item not in EXCLUDED_FILES and not any(item.endswith(ext) for ext in EXCLUDED_FILE_EXTENSIONS)
             and item not in EXCLUDED_DIRS]
    num_items = len(items)
    for i, item in enumerate(items):
        item_path = os.path.join(directory, item)
        is_last = i == num_items - 1
        prefix = "└── " if is_last else "├── "
        summary_file.write(f"{'    ' * level}{prefix}{item}\n")
        if os.path.isdir(item_path):
            _build_tree_for_file(item_path, level + 1, summary_file)


def write_file_content(summary_file, file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()  # Read the entire content
            summary_file.write(f"Content ({len(content)} characters):\n{content}\n\n")
    except UnicodeDecodeError as e:
        summary_file.write(f"Decoding error: {e}\n\n")


def print_summary_from_file(summary_filepath):
    """Prints a formatted summary from the summary file."""
    with open(summary_filepath, "r", encoding="utf-8") as summary_file:
        summary_content = summary_file.read()

    table = Table(title="[bold blue]Summary of Files and Directories[/]", expand=True, width=150)
    table.add_column("File/Directory", style="cyan", no_wrap=False)
    table.add_column("Path", style="magenta", no_wrap=False)

    for line in summary_content.splitlines():
        if "File:" in line:
            file_or_dir, path = extract_file_dir_info(line)
            table.add_row(file_or_dir, path)

    print(table)

    tree_structure = "\n".join(
        line for line in summary_content.splitlines() if "Subdirectory:" in line or "File:" in line
    )
    print(Panel(tree_structure, title="[bold green]Tree Structure[/]", expand=True, width=150))


def extract_file_dir_info(line):
    """Extracts file/directory info from a line."""
    file_or_dir = line.split(":")[1].strip()
    path = line.split("(")[1].strip().split(")")[0] if "(" in line else ""
    return file_or_dir, path


def count_lines_in_file(filepath):
    """Counts the number of lines in a file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return len(f.readlines())


def print_directory_tree(directory):
    """Prints the directory tree using Rich's Tree."""
    tree = Tree(f"[bold blue]{directory}[/]")
    _build_tree_for_rich(tree, directory)
    print(tree)


def _build_tree_for_rich(tree, directory):
    """Recursively builds the directory tree for Rich."""
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isdir(item_path):
            branch = tree.add(f"[bold green]{item}/[/]")
            _build_tree_for_rich(branch, item_path)
        elif os.path.isfile(item_path):
            tree.add(f"[cyan]{item}[/]")


if __name__ == "__main__":
    current_directory = os.getcwd()
    summarize_directory(current_directory)