tool_type_for_TOOL_MANAGER = "script_execution"
tool_update_focust_short_description = "Updates the focus file with new focus information"

import json
import os
import time
from typing import List, Dict, Any, Optional

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
    steps_to_achieve_goal: Optional[List[str]] = None,
    current_focus: str = "",
    accomplished: Optional[List[str]] = None,
    obtained_data: Optional[List[str]] = None,
    additional_info: str = "",
    switch_task: str = "NO"
) -> Dict[str, Any]:
    """
    Updates the focus file with new focus information.
    Handles potential issues with data types and ensures correct file updates.

    Args:
        user_goal (str): The overall goal the user wants to achieve. MANDATORY!
        steps_to_achieve_goal (List[str], optional): List of steps to achieve the goal. 
        current_focus (str): The current focus. MANDATORY!
        accomplished (List[str], optional): List of tasks that have been completed.
        obtained_data (List[str], optional): List of data obtained during the focus session.
        additional_info (str): Additional information related to the focus. MANDATORY!
        switch_task (str): Flag to indicate whether the user wants to switch tasks (YES/NO). MANDATORY!

    Returns:
        dict: A dictionary containing the status ("success" or "failure") and a message.
    """

    # Validate mandatory arguments
    if not user_goal or not current_focus or not additional_info or not switch_task:
        return {"status": "failure", "message": "Missing mandatory arguments: user_goal, current_focus, additional_info, switch_task."}

    # Handle optional arguments
    steps_to_achieve_goal = steps_to_achieve_goal or []
    accomplished = accomplished or []
    obtained_data = obtained_data or []

    # Create a new dictionary with the focus schema
    updated_focus_data = {
        "user_goal": user_goal,
        "steps_to_achieve_goal": steps_to_achieve_goal,
        "current_focus": current_focus,
        "accomplished": accomplished,
        "obtained_data": obtained_data,
        "additional_info": additional_info,
        "switch_task": switch_task.upper()
    }

    focus_file_path = "focus/focus.json"

    try:
        # Write the updated focus data to the file
        with open(focus_file_path, "w") as f:
            json.dump(updated_focus_data, f, indent=4)

        return {"status": "success", "message": "Focus updated."}

    except json.JSONDecodeError as e:
        return {"status": "failure", "message": f"Error decoding JSON: {str(e)}"}
    except IOError as e:
        return {"status": "failure", "message": f"Error writing to file: {str(e)}"}
    except Exception as e:
        return {"status": "failure", "message": f"Unknown error updating focus: {str(e)}"}