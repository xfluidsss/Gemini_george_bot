tool_type_for_TOOL_MANAGER = "script_execution"
tool_execute_script_short_description = "Executes Python code snippets safely with advanced options."
import io
import sys
import traceback
import psutil
import subprocess
from typing import Dict, Any, Optional

def tool_execute_script(
    path: str,  # Path to the Python script file
    timeout: Optional[float] = None,  # Maximum execution time in seconds
    max_memory: Optional[int] = None,  # Maximum memory usage in MB
    return_type: str = "output",  # Type of result to return (output, error, both)

) -> Dict[str, Any]:
    """
    Safely executes a Python script file using subprocess and returns the results with advanced options.

    Args:
        path (str): The path to the Python script file.
        timeout (float, optional): Maximum execution time in seconds.  If None, no timeout is enforced.
        max_memory (int, optional): Maximum memory usage in MB. If None, no memory limit is enforced.
        return_type (str): Type of result to return:
            - "output": Only return the output of the executed code.
            - "error": Only return the error message (if any).
            - "both": Return both output and error information.

    Returns:
        dict: A dictionary containing:
            - status: "success" or "failure"
            - message: A status message.
            - output: The output of the executed code (if successful and requested).
            - error: The error message (if an exception occurred and requested).
    """
    try:
        # Create a subprocess with appropriate arguments and environment
        process = subprocess.run(
            [sys.executable, path],
            capture_output=True,
            timeout=timeout,
            check=True,
            env={'PYTHONIOENCODING': 'utf-8'}  # Ensure consistent encoding
        )

        # Check for memory limits
        if max_memory is not None:
            if process.memory_info().rss / 1024 / 1024 > max_memory:
                raise MemoryError(f"Memory limit of {max_memory} MB exceeded.")

        # Construct the response based on return_type
        response = {
            "status": "success",
            "message": "Script executed successfully.",
        }
        if return_type in ("output", "both"):
            response["output"] = process.stdout.decode('utf-8').strip()
        if return_type in ("error", "both"):
            response["error"] = process.stderr.decode('utf-8').strip()

        return response

    except subprocess.TimeoutExpired as e:
        # Handle timeout errors
        return {
            "status": "failure",
            "message": f"Script execution timed out after {timeout} seconds.",
            "output": None,
            "error": str(e)
        }
    except subprocess.CalledProcessError as e:
        # Handle script execution errors
        return {
            "status": "failure",
            "message": f"Script execution failed with error code {e.returncode}.",
            "output": e.stdout.decode('utf-8').strip() if e.stdout else None,
            "error": e.stderr.decode('utf-8').strip() if e.stderr else None
        }
    except MemoryError as e:
        # Handle memory limit errors
        return {
            "status": "failure",
            "message": str(e),
            "output": None,
            "error": None
        }
    except Exception as e:
        # Handle other unexpected errors
        return {
            "status": "failure",
            "message": f"An error occurred during script execution: {str(e)}",
            "output": None,
            "error": traceback.format_exc()
        }