import json
import os


def create_focus_file(file_path="focus.json"):
    """
    Creates a new focus file with default values.

    Args:
      file_path (str): The path to the focus file.
    """

    focus_data = {
        "current_focus": "",  # Changed to empty string
        "user_goal": "",  # Changed to empty string
        "frustration": 0.2,
        "focus_strength": 0.8,
        "defocus_threshold": 0.5,
        "importance": 0.9,
        "progress": 0.1,
        "additional": "",  # Changed to empty string
        "verbose": "",  # Changed to empty string
        "tasks": {
            "current_task": "",  # Changed to empty string
            "task_list_to_accomplish_user_goal": [
                "",  # Changed to empty string
                "",  # Changed to empty string
                ""  # Changed to empty string
            ],
            "tasks_in_progress": [
                ""  # Changed to empty string
            ],
            "finished_tasks": [
                ""  # Changed to empty string
            ],
            "failed_tasks": []
        },
        "should_defocus": False,
        "obtained_data":{},
    }

    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, "w") as f:
        json.dump(focus_data, f, indent=4)

    print(f"Focus file created at: {file_path}")


if __name__ == "__main__":
    # Get the current working directory
    current_dir = os.getcwd()

    # Join the current directory with the desired filename to create the full path
    file_path = os.path.join(current_dir, "focus.json")

    create_focus_file(file_path)