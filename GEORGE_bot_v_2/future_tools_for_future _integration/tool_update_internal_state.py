tool_type_for_TOOL_MANAGER = "focus"
tool_tool_update_internal_state_description = """ Updates the focus file with new focus information."""

import json
import os
import logging
from typing import Dict, List, Any, Optional
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
logger = logging.getLogger(__name__)

DEFAULT_INTERNAL_STATE = {
    "emotions": "",
    "progress": 0.0,
    "frustration_level": 0.0,
    "task_cost": 0.0,
    "predictions": {},
    "optimization_goal": "",
    "tasks_finished": [],
    "additional": {},
    "version": 1
}

def tool_update_internal_state(
    internal_state_file_path: str,
    emotions: Optional[str] = None,
    progress: Optional[float] = None,
    frustration_level: Optional[float] = None,
    task_cost: Optional[float] = None,
    predictions: Optional[Dict[str, Any]] = None,
    optimization_goal: Optional[str] = None,
    tasks_finished: Optional[List[str]] = None,
    additional: Optional[Dict[str, Any]] = None,
    version: Optional[int] = None
):
    """Updates the internal state file with enhanced parameters and robust error handling.

    Args:
        internal_state_file_path (str): The full path to the internal state JSON file.
        emotions (Optional[str]): A string describing the agent's emotional state.
        progress (Optional[float]): A float between 0 and 1 representing the overall progress of the current task or goal.
        frustration_level (Optional[float]): A float between 0 and 1 indicating the agent's frustration level with the current task. Higher values suggest more frustration.
        task_cost (Optional[float]): A float representing the computational cost or resource consumption of the current task. Must be non-negative.
        predictions (Optional[Dict[str, Any]]): A dictionary containing any predictions made by the agent. The structure of this dictionary is flexible but should be consistent.
        optimization_goal (Optional[str]): A string describing the current optimization goal    minimize cost ,  maximize accuracy"  "minimize time
        tasks_finished (Optional[List[str]]): A list of strings representing the names or IDs of tasks that have been completed.
        additional (Optional[Dict[str, Any]]): A dictionary for storing any additional relevant information. The structure is flexible.
        version (Optional[int]): An integer representing the version number of the internal state data. Useful for tracking changes and potential rollbacks.

    Returns:
        dict: A dictionary containing the status "success" or "failure", a message, and if successful the updated internal state data.
    """
    max_retries = 3
    retry_delay = 2

    for attempt in range(1, max_retries + 1):
        try:
            # Try to load existing internal state
            try:
                with open(internal_state_file_path, "r") as f:
                    internal_state_data = json.load(f)
            except FileNotFoundError:
                # File not found, create a new one with default state
                logger.warning(f"Internal state file not found. Creating a new one: {internal_state_file_path}")
                internal_state_data = DEFAULT_INTERNAL_STATE.copy()

            # Input validation
            if progress is not None and not 0 <= progress <= 1:
                raise ValueError("Progress must be between 0 and 1.")
            if frustration_level is not None and not 0 <= frustration_level <= 1:
                raise ValueError("Frustration level must be between 0 and 1.")
            if task_cost is not None and task_cost < 0:
                raise ValueError("Task cost cannot be negative.")

            # Update data (including new parameters)
            if emotions is not None:
                internal_state_data["emotions"] = emotions
            if progress is not None:
                internal_state_data["progress"] = progress
            if frustration_level is not None:
                internal_state_data["frustration_level"] = frustration_level
            if task_cost is not None:
                internal_state_data["task_cost"] = task_cost
            if predictions is not None:
                internal_state_data["predictions"] = predictions
            if optimization_goal is not None:
                internal_state_data["optimization_goal"] = optimization_goal
            if tasks_finished is not None:
                internal_state_data["tasks_finished"] = tasks_finished
            if additional is not None:
                internal_state_data["additional"] = additional
            if version is not None:
                internal_state_data["version"] = version

            # Write updated data back to the file
            with open(internal_state_file_path, "w") as f:
                json.dump(internal_state_data, f, indent=4)

            logger.info(f"Internal state updated successfully: {internal_state_data}")
            return {
                "status": "success",
                "message": f"Internal state updated successfully.",
                "updated_internal_state": internal_state_data,
            }

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in file: {internal_state_file_path}, error: {e}")
            return {"status": "failure", "message": f"Invalid JSON in file: {internal_state_file_path}"}
        except (IOError, OSError, PermissionError) as e:
            if attempt < max_retries:
                logger.warning(f"Error updating internal state (attempt {attempt}/{max_retries}): {e}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                logger.error(f"Error updating internal state (after {max_retries} retries): {e}")
                return {"status": "failure", "message": f"Error updating internal state: {e}"}
        except ValueError as e:
            logger.error(f"Invalid input data: {e}")
            return {"status": "failure", "message": f"Invalid input data: {e}"}
        except Exception as e:
            logger.exception(f"An unexpected error occurred: {e}")
            return {"status": "failure", "message": f"An unexpected error occurred: {e}"}