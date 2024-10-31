import os
import importlib
from typing import Dict, Callable, List, Any
import logging
import inspect

# Set up logging (optional, but recommended)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Tool:
    """Represents a tool that can be used by the AI agent."""

    def __init__(self, name: str, function: Callable, description: str, arguments: Dict[str, str], tool_type: str):
        """
        Initializes a Tool object.

        Args:
            name: The name of the tool.
            function: The callable function that implements the tool.
            description: A brief description of the tool's functionality.
            arguments: A dictionary mapping argument names to their descriptions.
            tool_type: The type of the tool (e.g., 'os', 'web', 'focus').
        """
        self.name = name
        self.function = function
        self.description = description
        self.arguments = arguments
        self.tool_type = tool_type

    def __repr__(self):
        """Returns a string representation of the Tool object."""
        return f"Tool(name='{self.name}', function={self.function.__name__}, description='{self.description}', arguments={self.arguments}, tool_type='{self.tool_type}')"


class ToolManager:
    """Manages and provides access to tools."""

    def __init__(self, tools_folder: str):
        """
        Initializes the ToolManager with the path to the tools folder.

        Args:
            tools_folder: The path to the directory containing tool files.
        """
        self.tools_folder = tools_folder
        self.tools = {}  # Dictionary to store Tool objects
        self.load_tools()

    def load_tools(self):
        """Loads tools from files in the specified tools folder."""
        logger.info(f"Loading tools from: {self.tools_folder}")
        for root, _, files in os.walk(self.tools_folder):
            for file in files:
                if file.endswith(".py"):
                    # Extract tool name from file name
                    tool_name_from_file = file[:-3]  # Remove .py extension
                    module_path = os.path.join(root, file)

                    # Import the module
                    try:
                        spec = importlib.util.spec_from_file_location(tool_name_from_file, module_path)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                    except Exception as e:
                        logger.error(f"Error loading tool file '{file}': {e}")
                        continue

                    # Iterate through module attributes to find tool functions
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if callable(attr) and attr_name.startswith("tool_"):  # Check if it's a callable and starts with "tool_"

                            tool_name = attr_name  # Use the attribute name as the tool name
                            relative_path = os.path.relpath(module_path, self.tools_folder)  # Get the relative path to the tool file

                            # Get the short description for the tool from the module
                            tool_description = getattr(module, f"{tool_name}_short_description", f"Tool for {tool_name}")

                            # Get the tool arguments using inspect
                            tool_arguments = {}
                            sig = inspect.signature(attr)  # Get the function signature
                            for param_name, param in sig.parameters.items():
                                # Get the parameter type using annotation
                                tool_arguments[param_name] = param.annotation.__name__ if param.annotation != inspect._empty else "Any"

                            # Get the tool type from the module (optional, defaults to 'unknown')
                            tool_type = getattr(module, 'tool_type_for_TOOL_MANAGER', 'unknown')

                            # Create and store the Tool object
                            self.tools[tool_name] = Tool(tool_name, attr, tool_description, tool_arguments, tool_type)

                            # Log the discovered tool
                            logger.info(f"Discovered tool: {tool_name} (Type: {tool_type})")
                            print(f"  - {tool_name} - {tool_description}")  # Print the tool information
                            logger.debug(f"Tool description: {tool_description}")
                            logger.debug(f"Tool arguments: {tool_arguments}")  # Log the tool arguments

    def get_tool_function(self, function_name: str) -> Callable:
        """Returns the callable object for the given function name."""
        tool = self.tools.get(function_name)
        if tool:
            return tool.function
        else:
            return None

    def get_all_tools(self) -> List[Tool]:
        """Returns a list of all loaded tools."""
        return list(self.tools.values())

    def get_tools_by_type(self, tool_type: str) -> List[Tool]:
        """Returns a list of tools based on their type."""
        return [tool for tool in self.tools.values() if tool.tool_type == tool_type]

    def load_tools_of_type(self, tool_type: str = "all") -> List[Callable]:
        """Loads and returns a list of tool functions based on the specified type.

        Args:
            tool_type: The type of tools to load. 'all' for all tools, or a specific type like 'os', 'web', etc.

        Returns:
            A list of tool functions.
        """
        if tool_type == "all":
            return [tool.function for tool in self.tools.values()]
        else:
            return [tool.function for tool in self.tools.values() if tool.tool_type == tool_type]

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Calls the tool function with the provided arguments.

        Args:
            tool_name: The name of the tool to call.
            arguments: A dictionary of arguments to pass to the tool function.

        Returns:
            The result of the tool function call.

        Raises:
            KeyError: If the tool name is not found.
            TypeError: If the provided arguments are not valid for the tool.
        """
        tool = self.tools.get(tool_name)
        if tool is None:
            raise KeyError(f"Tool '{tool_name}' not found.")

        # Check if all required arguments are provided
        missing_args = set(tool.arguments.keys()) - set(arguments.keys())
        if missing_args:
            raise TypeError(f"Missing arguments for tool '{tool_name}': {', '.join(missing_args)}")

        # Call the tool function
        try:
            result = tool.function(**arguments)
            return result
        except Exception as e:
            raise RuntimeError(f"Error calling tool '{tool_name}': {e}")