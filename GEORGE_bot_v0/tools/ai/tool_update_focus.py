tool_type_for_TOOL_MANAGER = "focus"
tool_update_focus_short_description = """ Updates the focus file with new focus information."""

import json
import os


def tool_update_focus(
    new_focus: str,
    category: str = None,
    frustration_level: int = None,
    focus_strength: int = None,
    defocus_threshold: int = None,
    importance: float = None,  # Added importance parameter
    progress: float = None,  # Added progress parameter
    additional: str = None,  # Added additional parameter
    verbose: str = None   # Added verbose parameter
) -> dict:
    """
    Updates the focus file with new focus information.

    Args:
        new_focus (str): The new focus text to be added to the focus file.
        category (str, optional): The category of the focus (e.g., "Research", "Task", "Goal"). Defaults to None.
        frustration_level (int, optional): A level indicating the current frustration level (0-10). Defaults to None.
        focus_strength (int, optional): A level indicating the strength of the focus (0-10). Defaults to None.
        defocus_threshold (int, optional): A level indicating the threshold at which the focus should be considered defocused (0-10). Defaults to None.
        importance (float, optional): Importance of the focus (0-1). Defaults to None.
        progress (float, optional): Progress on the focus (0-1). Defaults to None.
        additional (str, optional): Additional information about the focus like important  data .
        verbose (str, optional): Verbosity level of the focus (e.g., "normal", "detailed"). Defaults to None.


    Returns:
        dict: A dictionary containing the status of the operation, a message, and the updated focus text.
    """

    focus_file_path = "focus/focus.json" # Hardcode the relative path to the focus file

    try:
        # Read the existing focus from the file
        with open(focus_file_path, "r") as f:
            focus_data = json.load(f)

        # Update the focus data with new values
        focus_data["current_focus"] = new_focus
        if frustration_level is not None:
            focus_data["frustration"] = frustration_level / 10.0  # Convert to 0-1 scale
        if focus_strength is not None:
            focus_data["focus_strength"] = focus_strength / 10.0  # Convert to 0-1 scale
        if importance is not None:
            focus_data["importance"] = importance
        if progress is not None:
            focus_data["progress"] = progress
        if additional is not None:
            focus_data["additional"] = additional
        if verbose is not None:
            focus_data["verbose"] = verbose

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
        new_focus="Write a blog post",
        importance=0.8,
        progress=0.3
    )
    print(result)