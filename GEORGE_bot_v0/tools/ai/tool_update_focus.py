import json
import os
from typing import List, Dict, Any

# Define the schema for the focus file
focus_schema = {
    "current_focus": str,
    "user_goal": str,
    "frustration": float,
    "focus_strength": float,
    "defocus_threshold": float,
    "importance": float,
    "progress": float,
    "additional": str,
    "verbose": str,
    "tasks": {
        "current_task": str,
        "task_list_to_accomplish_user_goal": List[str],
        "tasks_in_progress": List[str],
        "finished_tasks": List[str],
        "failed_tasks": List[str]
    },
    "should_defocus": bool
}

def tool_update_focus(
    new_focus: str,
    user_goal: str,
    frustration_level: float,
    focus_strength: float,
    defocus_threshold: float,
    importance: float,
    progress: float,
    additional: str,
    verbose: str,
    current_task: str,
    task_list_to_accomplish_user_goal: List[str],
    tasks_in_progress: List[str],
    finished_tasks: List[str],
    failed_tasks: List[str],
    should_defocus: bool
) -> dict:
    """
    Updates the focus file with new focus information, including task management.

    Args:
        new_focus (str): The new focus text to be added to the focus file.
        user_goal (str): The overall goal the user wants to achieve.
        frustration_level (float): Level of frustration (0-1).
        focus_strength (float): Strength of focus (0-1).
        defocus_threshold (float): Threshold for defocusing (0-1).
        importance (float): Importance of focus (0-1).
        progress (float): Progress on the focus (0-1).
        additional (str): Additional information related to the focus.
        verbose (str): Detailed description of the focus.
        current_task (str): The task currently being worked on.
        task_list_to_accomplish_user_goal (List[str]): List of tasks required to achieve the user's goal.
        tasks_in_progress (List[str]): List of tasks currently in progress.
        finished_tasks (List[str]): List of completed tasks.
        failed_tasks (List[str]): List of tasks that failed.
        should_defocus (bool): Whether to defocus from the current focus.

    Returns:
        dict: A dictionary containing the status of the operation, a message, and the updated focus text.
    """

    focus_file_path = "focus/focus.json"

    # Check if the file exists, if not, create an empty file
    if not os.path.exists(focus_file_path):
        with open(focus_file_path, "w") as f:
            json.dump({}, f, indent=4)

    try:
        # Read the existing focus from the file
        with open(focus_file_path, "r") as f:
            focus_data = json.load(f)

        # **Initialize focus_data with the schema if it's empty**
        if not focus_data:
            focus_data = focus_schema.copy()

        # Update the focus data with new values
        focus_data["current_focus"] = new_focus
        focus_data["user_goal"] = user_goal
        focus_data["frustration"] = frustration_level
        focus_data["focus_strength"] = focus_strength
        focus_data["defocus_threshold"] = defocus_threshold
        focus_data["importance"] = importance
        focus_data["progress"] = progress
        focus_data["additional"] = additional
        focus_data["verbose"] = verbose

        # Update the task lists
        focus_data["tasks"]["current_task"] = current_task
        focus_data["tasks"]["task_list_to_accomplish_user_goal"] = task_list_to_accomplish_user_goal
        focus_data["tasks"]["tasks_in_progress"] = tasks_in_progress
        focus_data["tasks"]["finished_tasks"] = finished_tasks
        focus_data["tasks"]["failed_tasks"] = failed_tasks

        # Update should_defocus
        focus_data["should_defocus"] = should_defocus

        # Write the updated focus back to the file
        with open(focus_file_path, "w") as f:
            json.dump(focus_data, f, indent=4)

        return {
            "status": "success",
            "message": f"Focus updated with: '{new_focus}'",
            "updated_focus": focus_data,
        }

    except Exception as e:
        return {"status": "failure", "message": f"Error updating focus: {str(e)}"}

if __name__ == "__main__":
    # Example usage:
    result = tool_update_focus(
        new_focus="Download images of main characters of Dragon Ball",
        user_goal="Create a collection of Dragon Ball character images",
        frustration_level=0.2,
        focus_strength=0.8,
        defocus_threshold=0.5,
        importance=0.9,
        progress=0.1,
        additional="I'm looking for high-quality images from reliable sources.",
        verbose="I want to create a collection of Dragon Ball character images for a personal project.",
        current_task="Download images of Goku",
        task_list_to_accomplish_user_goal=["Research Dragon Ball characters", "Download images", "Organize images"],
        tasks_in_progress=["Download images of Vegeta"],
        finished_tasks=["Research Dragon Ball characters"],
        failed_tasks=[],
        should_defocus=False
    )
    print(result)