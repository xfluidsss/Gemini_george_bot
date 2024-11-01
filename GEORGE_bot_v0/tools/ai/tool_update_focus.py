tool_type_for_TOOL_MANAGER = "focus"
tool_tool_update_focusshort_description = """updates foucs"""

import json
import os
import time
from typing import List, Dict, Any

# Define the schema for the focus file
focus_schema = {
    "user_goal": str,
    "steps_to_achieve_goal": List[str],
    "current_focus": str,
    "accomplished": List[str],
    "obtained_data": List[str],
    "additional_info": str,  # For storing additional notes or information
    "switch_task": str  # Flag to indicate whether the user wants to switch tasks (YES/NO)
}

def tool_update_focus(
    user_goal: str = "",
    steps_to_achieve_goal: List[str] = [],
    current_focus: str = "",
    accomplished: List[str] = [],
    obtained_data: List[str] = [],
    additional_info: str = "",  # Additional information
    switch_task: str = "NO"  # Flag for switching tasks (YES/NO)
) -> Dict[str, Any]:
    """
    Updates the focus file with new focus information.
    Overwrites the entire file with the provided data and the focus schema. this  enalbes for  long term  focus on tasks

    Args:
        user_goal (str): The overall goal the user wants to achieve.
        steps_to_achieve_goal (List[str]): List of steps to achieve the goal.
        current_focus (str): The current focus.
        accomplished (List[str]): List of tasks that have been completed.
        obtained_data (List[str]): List of data obtained during the focus session.
        additional_info (str): Additional information related to the focus.
        switch_task (str): Flag to indicate whether the user wants to switch tasks YES,NO.

    Returns:
     status of the operation,
    """

    # Create a new dictionary with the focus schema and populate it with the provided data
    updated_focus_data = {
        "user_goal": user_goal,
        "steps_to_achieve_goal": steps_to_achieve_goal,
        "current_focus": current_focus,
        "accomplished": accomplished,
        "obtained_data": obtained_data,
        "additional_info": additional_info,
        "switch_task": switch_task.upper
    }

    focus_file_path = "focus/focus.json"

    try:
        # Write the updated focus data to the file
        with open(focus_file_path, "w") as f:
            json.dump(updated_focus_data, f, indent=4)

        return {
            "status": "success",
            "message": "Focus updated."}



    except json.JSONDecodeError as e:
        return {"status": "failure", "message": f"Error decoding JSON: {str(e)}"}
    except IOError as e:
        return {"status": "failure", "message": f"Error writing to file: {str(e)}"}
    except Exception as e:
        return {"status": "failure", "message": f"Unknown error updating focus: {str(e)}"}