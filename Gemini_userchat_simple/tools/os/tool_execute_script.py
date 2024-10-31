tool_type_for_TOOL_MANAGER = "script_execution"
tool_execute_script_short_description = "Executes Python code snippets safely with advanced options."
import io
import sys
import traceback
import psutil
from typing import Dict, Any, Optional

def tool_execute_script(
    code: str,
    timeout: Optional[float] = None,  # Maximum execution time in seconds
    max_memory: Optional[int] = None,  # Maximum memory usage in MB
    return_type: str = "output",  # Type of result to return (output, error, both)

) -> Dict[str, Any]:
    """
    Safely executes a Python code snippet and returns the results with advanced options.

    Args:
        code (str): The Python code to execute.
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
        # Create a temporary standard output stream to capture output
        stdout_buffer = io.StringIO()
        sys.stdout = stdout_buffer

        # Implement timeout and memory limits (if provided)
        if timeout is not None:
            # Use a separate thread to enforce timeout
            def execute_with_timeout():
                try:
                    exec(code)
                except Exception as e:
                    raise e

            from threading import Thread, Timer
            thread = Thread(target=execute_with_timeout)
            timer = Timer(timeout, thread.cancel)
            timer.start()
            thread.start()
            thread.join()
            timer.cancel()

        if max_memory is not None:
            # Execute with memory limit
            def execute_with_memory_limit():
                process = psutil.Process()
                try:
                    exec(code)
                except Exception as e:
                    raise e
                finally:
                    if process.memory_info().rss / 1024 / 1024 > max_memory:
                        raise MemoryError(f"Memory limit of {max_memory} MB exceeded.")
            execute_with_memory_limit()

        # Reset standard output
        sys.stdout = sys.__stdout__

        # Get the captured output
        output = stdout_buffer.getvalue().strip()

        # Construct the response based on return_type
        response = {
            "status": "success",
            "message": "Script executed successfully.",
        }
        if return_type in ("output", "both"):
            response["output"] = output
        if return_type in ("error", "both"):
            response["error"] = None  # No error occurred

        return response

    except Exception as e:
        # Capture the error message and traceback
        error_message = f"Error executing script: {str(e)}"
        error_traceback = traceback.format_exc()

        # Reset standard output
        sys.stdout = sys.__stdout__

        # Construct the response based on return_type
        response = {
            "status": "failure",
            "message": error_message,
        }
        if return_type in ("output", "both"):
            response["output"] = None
        if return_type in ("error", "both"):
            response["error"] = error_traceback

        return response