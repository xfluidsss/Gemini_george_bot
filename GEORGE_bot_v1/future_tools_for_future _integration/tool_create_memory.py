tool_type_for_TOOL_MANAGER = "memory"
tool_create_memory_short_description = """Updates the focus file with new focus information."""

import time
import json
import os
import logging
import google.generativeai as genai
from typing import List, Dict, Any
from datetime import datetime
import re

# --- Color and Configuration Settings ---
BLACK = "\033[30m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"
RESET = "\033[0m"
BOLD = "\033[1m"
UNDERLINE = "\033[4m"
REVERSE = "\033[7m"

# --- Global Variables ---
MEMORY_FRAME_NUMBER = 1
EDIT_NUMBER = 0
TIMESTAMP_FORMAT = '%Y-%m-%d_%H-%M'
SESSION_INFO = "Conversation"  # Renamed for clarity

# --- API Key and Configuration ---
googleKey = 'AIzaSyChx1mgNxXW4RwrnEPr3DCWvU_sQIV_4WM'  # Moved for better structure
genai.configure(api_key=googleKey)

# --- Helper Functions ---

def sanitize_href(href: str, memories_folder_path: str) -> str:
    """Sanitizes a given href string by replacing spaces with %20."""
    href = href.replace(" ", "%20")
    return href


def get_memories_folder_path() -> str:
    """Returns the absolute path to the 'memory' folder."""
    current_dir = os.path.abspath(os.path.dirname(__file__))
    memories_path = os.path.join(current_dir, "memory")
    return memories_path


def process_user_input() -> str:
    """Gets user input from the console."""
    user_input = input(f"{GREEN}Enter input: {RESET}")
    print(f"{MAGENTA}User input received: {user_input}{RESET}")
    return user_input


def call_interaction_model(user_input: str, timestamp: str) -> genai.GenerateContentResponse:
    """Calls the interaction model with the provided user input and timestamp."""
    print(f"\n{CYAN}--- Calling Interaction Model ---{RESET}")
    try:
        interaction_model = genai.GenerativeModel(
            model_name='gemini-1.5-flash-latest',
            safety_settings={'HARASSMENT': 'block_none'},
            system_instruction='You follow orders and generate creative text interactions'
        )
        chat = interaction_model.start_chat(history=[])
        response = chat.send_message(f"currentTime: {timestamp} create {user_input}")
        print(f"AI Response: {response.text}")
        return response
    except Exception as e:
        print(f"Error in Interaction Model: {e}")
        return None


def call_memory_model(loop_conversation: str) -> genai.GenerateContentResponse:
    """Calls the memory model to analyze and summarize the provided conversation loop."""
    print(f"\n{CYAN}--- Calling Memory Model ---{RESET}")
    try:
        memory_model = genai.GenerativeModel(
            model_name='gemini-1.5-flash-latest',
            safety_settings={'HARASSMENT': 'block_none'},
            system_instruction="""You are a sophisticated AI assistant helping to organize memory. 
            Analyze and summarize the provided conversation, focusing on elements that would be most useful for storing and retrieving this memory later. Don't hallucinate. 
            Use the provided JSON schema for your response and fill in all fields with relevant information.
            You can omit entries if they don't seem appropriate for memory storage and would be empty.
            Never omit the "memory_folders_storage" entry.

            **JSON Schema:** 
            {
                "naming_suggestion": {
                    "memory_frame_name": "A descriptive name for the memory frame" 
                },
                "storage": {
                    "memory_folders_storage": [
                        {
                            "folder_path": "path/to/folder", 
                            "probability": 5 
                        }
                    ]
                },
                "interaction": {
                    "interaction_type": [], 
                    "people": [], 
                    "objects": [], 
                    "animals": [], 
                    "actions": [], 
                    "observed_interactions": [] 
                },
                "impact": {
                    "obtained_knowledge": "", 
                    "positive_impact": "", 
                    "negative_impact": "", 
                    "expectations": "", 
                    "strength_of_experience": "" 
                },
                "importance": {
                    "reason": "", 
                    "potential_uses": [], 
                    "importance_level": "0-100" 
                },
                "technical_details": {
                    "problem_solved": "", 
                    "concept_definition": "", 
                    "implementation_steps": [], 
                    "tools_and_technologies": [], 
                    "example_projects": [], 
                    "best_practices": [], 
                    "common_challenges": [], 
                    "debugging_tips": [], 
                    "related_concepts": [], 
                    "resources": [], 
                    "code_examples": [] 
                }
            }

            Here you have existing folder structure for memory_folders_storage:
            memory/NewGeneratedbyAI/

            **Memory Storage Suggestions:**
            Provide your suggestions for where this memory frame should be stored using the following format within the "memory_folders_storage" field:

            * **"folder_path":** The relative path for storing the memory frame (use '/' as the path separator).
            * **"probability":** The strength of probability (from 0 to 10) that the memory frame should be stored in the suggested folder. Use a scale from 0 (least likely) to 10 (most likely) to express your confidence. 
        """
        )
        chat = memory_model.start_chat(history=[])
        create_memory_prompt = f"Loop {loop_conversation}"
        response = chat.send_message(create_memory_prompt)
        print(f"Memory Model Response:\n{response.text}")
        return response
    except Exception as e:
        print(f"Error in Memory Model: {e}")
        return None


def extract_entries_smart(response_message: str) -> List[Dict[str, Any]]:
    """Extracts structured JSON entries from the AI response message."""
    print("\n--- Extracting Structured Entries ---")
    entries = []
    json_match = re.search(r"```json\n(.*?)\n```", response_message, re.DOTALL)
    if json_match:
        print("Found JSON data in the response.")
        try:
            json_data = json_match.group(1)
            print("Parsing JSON data...")
            response_data = json.loads(json_data)
            print("JSON data parsed successfully.")

            if isinstance(response_data, list):
                entries.extend(response_data)
            elif isinstance(response_data, dict):
                entries.append(response_data)
            else:
                print(f"Warning: Unexpected data type: {type(response_data)}")
                print("Skipping data.")

        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in the AI response: {e}")
        except Exception as e:
            print(f"Error extracting entry: {e}")
    return entries


def save_to_file(content: str, file_name: str, file_path: str, encoding: str = 'utf-8', create_folders: bool = True) -> \
Dict[str, Any]:
    """Saves content to a file with error handling and folder creation."""
    logging.info("Entering: save_to_file")
    full_path = os.path.join(file_path, file_name)

    try:
        if create_folders:
            os.makedirs(file_path, exist_ok=True)
        with open(full_path, 'w', encoding=encoding) as f:
            f.write(content)
        success_message = f"File saved successfully at: {full_path}"
        logging.info(success_message)
        return {"status": "success", "message": success_message, "file_path": full_path}
    except IOError as e:
        error_message = f"IOError: Failed to save file: {str(e)}"
        logging.error(error_message)
        return {"status": "failure", "message": error_message}
    except Exception as e:
        error_message = f"Unexpected error: Failed to save file: {str(e)}"
        logging.error(error_message)
        return {"status": "failure", "message": error_message}
    finally:
        logging.info("Exiting: save_to_file")


def interpret_function_calls(response: genai.GenerateContentResponse, available_tools: Dict[str, Any]) -> List[
    Dict[str, Any]]:
    """Interprets function calls within the AI response and executes them."""
    results = []
    if response.candidates:
        for candidate in response.candidates:
            if hasattr(candidate, 'function_call'):
                function_call = candidate.function_call
                tool_name = function_call.name
                if tool_name in available_tools:
                    tool_function = available_tools[tool_name]
                    function_args = {}
                    for arg_name, arg_value in function_call.args.items():
                        function_args[arg_name] = arg_value
                    try:
                        print(f"Calling tool: {tool_name} with args: {function_args}")
                        result = tool_function(**function_args)
                        results.append(result)
                    except Exception as e:
                        logger = logging.getLogger(__name__)
                        logger.error(f"Error calling {tool_name}: {e}")
                        results.append({"status": "failure", "message": f"Error calling {tool_name}: {e}"})
                else:
                    results.append({"status": "failure", "message": f"Tool '{tool_name}' not found."})
            else:
                results.append({"status": "failure", "message": "No function call found."})
    return results


def tool_create_memory(loop_data: str):
    """
    Processes a conversation loop, extracts memory data, and stores it as a memory frame.

    Args:
        loop_data (str): The conversation loop data as a string. This data should be
                         in a format that the memory model can understand and process.

    Returns:
        None: This function does not return any values. It directly saves the memory frame
              to a file if successful.
    """
    timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
    memories_folder_path = get_memories_folder_path()  # Use the function to get the path

    memory_response = call_memory_model(loop_data)
    if memory_response is None:
        print("Error: Memory model call failed. Exiting.")
        return

    memory_entries = extract_entries_smart(memory_response.text)

    if not memory_entries:
        print(f"{RED}Warning: No memory entries returned by the memory model. Skipping memory frame storage.{RESET}")
        return

    available_tools = {"save_to_file": save_to_file}
    session_info = "0000"  # Assuming this is a placeholder, adjust as needed
    for entry in memory_entries:
        memory_frame_data = {
            "timestamp": timestamp,
            "edit_number": EDIT_NUMBER,
            "session_info": session_info,
            "naming_suggestion": entry.get("naming_suggestion", {}),
            "storage": entry.get("storage", {}),
            "interaction": entry.get("interaction", {}),
            "impact": entry.get("impact", {}),
            "importance": entry.get("importance", {}),
            "technical_details": entry.get("technical_details", {})
        }

        try:
            file_name = entry["naming_suggestion"]["memory_frame_name"].replace(" ", "_") + ".json"
            folder_path = entry["storage"]["memory_folders_storage"][0]["folder_path"]
            file_path = os.path.join(memories_folder_path, "NewGeneratedbyAI", folder_path)

            save_args = {
                "content": json.dumps(memory_frame_data, indent=4),
                "file_name": file_name,
                "file_path": file_path,
                "create_folders": True
            }

            class DummyCandidate:
                def __init__(self, args):
                    self.function_call = DummyFunctionCall(args)

            class DummyFunctionCall:
                def __init__(self, args):
                    self.name = "save_to_file"
                    self.args = args

            dummy_response = genai.GenerateContentResponse()
            dummy_response.candidates = [DummyCandidate(save_args)]

            save_results = interpret_function_calls(dummy_response, available_tools)
            if save_results and save_results[0]['status'] == 'success':
                print(f"{GREEN}Memory frame saved successfully: {save_results[0]['message']}{RESET}")
            else:
                print(f"{RED}Error saving memory frame: {save_results[0]['message']}{RESET}")

        except (KeyError, IndexError, TypeError) as e:
            print(f"{RED}Error processing memory entry. Check JSON structure: {e}{RESET}")
            continue

