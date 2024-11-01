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
    "should_defocus": bool,
    "obtained_data": List[str]
}

def tool_update_focus(
    current_focus: str = "",
    user_goal: str = "",
    frustration_level: float = 0.0,
    focus_strength: float = 0.0,
    defocus_threshold: float = 0.0,
    importance: float = 0.0,
    progress: float = 0.0,
    additional: str = "",
    verbose: str = "",
    current_task: str = "",
    task_list_to_accomplish_user_goal: List[str] = [],
    tasks_in_progress: List[str] = [],
    finished_tasks: List[str] = [],
    failed_tasks: List[str] = [],
    should_defocus: bool = False,
    obtained_data: List[str] = [],
    focus_file_path: str = "focus/focus.json"
) -> Dict[str, Any]:
    """
    Updates the focus file with new focus information, including task management.
    Overwrites the entire file with the provided data and the focus schema.

    Args:
        current_focus (str): The new focus text to be added to the focus file. Defaults to "".
        user_goal (str): The overall goal the user wants to achieve. Defaults to "".
        frustration_level (float): Level of frustration (0-1). Defaults to 0.0.
        focus_strength (float): Strength of focus (0-1). Defaults to 0.0.
        defocus_threshold (float): Threshold for defocusing (0-1). Defaults to 0.0.
        importance (float): Importance of focus (0-1). Defaults to 0.0.
        progress (float): Progress on the focus (0-1). Defaults to 0.0.
        additional (str): Additional information related to the focus. Defaults to "".
        verbose (str): Detailed description of the focus. Defaults to "".
        current_task (str): The task currently being worked on. Defaults to "".
        task_list_to_accomplish_user_goal (List[str]): List of tasks required to achieve the user's goal. Defaults to [].
        tasks_in_progress (List[str]): List of tasks currently in progress. Defaults to [].
        finished_tasks (List[str]): List of completed tasks. Defaults to [].
        failed_tasks (List[str]): List of tasks that failed. Defaults to [].
        should_defocus (bool): Whether to defocus from the current focus. Defaults to False.
        obtained_data (List[str]): List of data obtained during the focus session. Defaults to [].
        focus_file_path (str): The path to the focus file. Defaults to "focus/focus.json".

    Returns:
        Dict[str, Any]: A dictionary containing the status of the operation, a message, and the updated focus text.
    """

    # Validate input data
    for key, value in {
        "frustration_level": frustration_level,
        "focus_strength": focus_strength,
        "defocus_threshold": defocus_threshold,
        "importance": importance,
        "progress": progress
    }.items():
        if not 0 <= value <= 1:
            return {
                "status": "failure",
                "message": f"Invalid value for '{key}': {value}. Must be between 0 and 1."
            }

    # Create a new dictionary with the focus schema and populate it with the provided data
    updated_focus_data = {
        "current_focus": current_focus,
        "user_goal": user_goal,
        "frustration": frustration_level,
        "focus_strength": focus_strength,
        "defocus_threshold": defocus_threshold,
        "importance": importance,
        "progress": progress,
        "additional": additional,
        "verbose": verbose,
        "tasks": {
            "current_task": current_task,
            "task_list_to_accomplish_user_goal": task_list_to_accomplish_user_goal,
            "tasks_in_progress": tasks_in_progress,
            "finished_tasks": finished_tasks,
            "failed_tasks": failed_tasks
        },
        "should_defocus": should_defocus,
        "obtained_data": obtained_data
    }

    try:
        # Write the updated focus data to the file
        with open(focus_file_path, "w") as f:
            json.dump(updated_focus_data, f, indent=4)

        return {
            "status": "success",
            "message": f"Focus updated.",
            "updated_focus": updated_focus_data,
        }

    except json.JSONDecodeError as e:
        return {"status": "failure", "message": f"Error decoding JSON: {str(e)}"}
    except IOError as e:
        return {"status": "failure", "message": f"Error writing to file: {str(e)}"}
    except Exception as e:
        return {"status": "failure", "message": f"Unknown error updating focus: {str(e)}"}

if __name__ == "__main__":
    # Example usage:
    result = tool_update_focus(
        current_focus="Download images of main characters of Dragon Ball",
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
        should_defocus=False,
        obtained_data=["Image of Goku", "Image of Vegeta"]
    )
    print(result)