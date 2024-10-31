tool_type_for_TOOL_MANAGER = "focus"
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
SESSION_INFO = "Conversation"

googleKey='AIzaSyChx1mgNxXW4RwrnEPr3DCWvU_sQIV_4WM'

genai.configure(api_key=googleKey)


# --- Helper Functions ---

def sanitize_href(href: str, memories_folder_path: str) -> str:
    """Sanitizes a given href string by replacing spaces with %20."""
    href = href.replace(" ", "%20")
    return href


def Get_path_of_memories_folder() -> str:
    """Returns the absolute path to the 'memory' folder."""
    current = os.path.abspath(os.path.dirname(__file__))
    memories_path = os.path.join(current, "memory")
    return memories_path


def process_user_input() -> str:
    user_input = input(f"{GREEN}Enter input: {RESET}")
    print(f"{MAGENTA}User input received: {user_input}{RESET}")
    return user_input


def call_interaction_model(user_input: str, timestamp: str) -> genai.GenerateContentResponse:
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


def call_memory_model(user_input: str, response1_text: str) -> genai.GenerateContentResponse:
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
        create_memory_prompt = f"User: {user_input}\nAI: {response1_text}"
        response = chat.send_message(create_memory_prompt)
        print(f"Memory Model Response:\n{response.text}")
        return response
    except Exception as e:
        print(f"Error in Memory Model: {e}")
        return None


def extract_entries_smart(response_message: str) -> List[Dict[str, Any]]:
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
                entries.extend(response_data)  # Use extend to add all items from the list
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
    """Saves content to a file."""
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
    """Interprets function calls and executes them."""
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
                        logger = logging.getLogger(__name__)  # Get the logger for this module
                        logger.error(f"Error calling {tool_name}: {e}")
                        results.append({"status": "failure", "message": f"Error calling {tool_name}: {e}"})
                else:
                    results.append({"status": "failure", "message": f"Tool '{tool_name}' not found."})
            else:
                results.append({"status": "failure", "message": "No function call found."})
    return results


def store_memory_frame(memory_model_response_text: str,
                       memory_data: dict,
                       session_info: str):
    global MEMORY_FRAME_NUMBER, EDIT_NUMBER

    print(f"\n{YELLOW}--- Storing Memory Frame ---{RESET}")
    connection_map = {}
    memories_folder_path = Get_path_of_memories_folder()
    memory_frame_paths = []

    script_path = os.path.abspath(os.path.dirname(__file__))

    storage_folders = memory_data.get("storage", {}).get("memory_folders_storage", [])
    print(f"Suggested storage folders: {storage_folders}")

    timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
    proposed_name = memory_data.get("naming_suggestion", {}).get("memory_frame_name", "UnnamedMemory")
    importance_level = memory_data.get("importance", {}).get("importance_level", "UnknownImportance")

    # Check if there are any storage suggestions, and skip if empty
    if not storage_folders:
        print(f"{RED}Warning: No memory folders suggested. Skipping memory frame storage.{RESET}")
        return

    # Check if memory_data is not empty before storing it
    if not memory_data:
        print(f"{RED}Warning: Empty memory data received. Skipping memory frame storage.{RESET}")
        return

    for i, folder_info in enumerate(storage_folders):
        folder_path = folder_info.get("folder_path", "")
        probability = folder_info.get("probability", 0)
        print(f"Processing folder: {folder_path} (Probability: {probability})")

        if folder_path in connection_map:
            print(f"Folder '{folder_path}' found in connection map.")
            target_folder_path = connection_map[folder_path]
        else:
            print(f"Folder '{folder_path}' not in connection map. Creating in 'NewGeneratedbyAI'...")
            target_folder_path = os.path.join(script_path, "memory", "NewGeneratedbyAI", folder_path)
            os.makedirs(target_folder_path, exist_ok=True)

        # Construct the filename
        memory_frame_name = f"MemoryFrame_{MEMORY_FRAME_NUMBER:05d}_{SESSION_INFO}_{timestamp}_Probability_{probability}_Importance_{importance_level}_{proposed_name}.json"
        memory_frame_path = os.path.join(target_folder_path, memory_frame_name)
        print(f"Memory frame name: {memory_frame_name}")
        print(f"Memory frame path: {memory_frame_path}")

        # Only save the memory frame for the first iteration (i == 0)
        if i == 0:
            memory_frame_data = {
                "timestamp": timestamp,
                "edit_number": EDIT_NUMBER,
                "session_info": session_info,

            }

            try:
                with open(memory_frame_path, 'w') as file:
                    json.dump(memory_frame_data, file, indent=4)
                print(f"{YELLOW}Memory frame saved successfully at: {memory_frame_path}{RESET}")
                memory_frame_paths.append(memory_frame_path)
            except Exception as e:
                print(f"Error saving memory frame: {e}")
        else:
            print(f"Skipping save for folder suggestion at index {i}")


def tool_create_memory(user_input: str):
    timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)

    # Combine ALL responses for the Memory Model
    combined_conversation_summary = f"""

    """

    memory_response = call_memory_model(user_input, combined_conversation_summary)
    if memory_response is None:
        print("Error: Memory model call failed. Exiting.")
        return

    memory_entries = extract_entries_smart(memory_response.text)

    if not memory_entries:
        print(f"{RED}Warning: No memory entries returned by the memory model. Skipping memory frame storage.{RESET}")
        return

    available_tools = {"save_to_file": save_to_file}
    session_info="0000"
    for entry in memory_entries:
        # Construct memory_frame_data (this part remains largely the same)
        memory_frame_data = {
            "timestamp": timestamp,
            "edit_number": EDIT_NUMBER,
            "session_info": session_info,
            "naming_suggestion": entry.get("naming_suggestion", {}),  # Include naming_suggestion
            "storage": entry.get("storage", {}),  # Include storage
            "interaction": entry.get("interaction", {}),  # Include interaction
            "impact": entry.get("impact", {}),  # Include impact
            "importance": entry.get("importance", {}),  # Include importance
            "technical_details": entry.get("technical_details", {})  # Include technical_details
        }

        # Extract filename and path from the memory_data
        try:
            file_name = entry["naming_suggestion"]["memory_frame_name"].replace(" ", "_") + ".json"
            folder_path = entry["storage"]["memory_folders_storage"][0]["folder_path"]
            file_path = os.path.join(Get_path_of_memories_folder(), "NewGeneratedbyAI", folder_path)  # Adjust if needed

            # Prepare arguments for save_to_file
            save_args = {
                "content": json.dumps(memory_frame_data, indent=4),
                "file_name": file_name,
                "file_path": file_path,
                "create_folders": True
            }

            # Construct a Dummy Response to feed into the interpreter
            class DummyCandidate:
                def __init__(self, args):
                    self.function_call = DummyFunctionCall(args)

            class DummyFunctionCall:
                def __init__(self, args):
                    self.name = "save_to_file"
                    self.args = args

            dummy_response = genai.GenerateContentResponse()
            dummy_response.candidates = [DummyCandidate(save_args)]

            # Use the interpreter to handle the save_to_file call
            save_results = interpret_function_calls(dummy_response, available_tools)
            if save_results and save_results[0]['status'] == 'success':
                print(f"{GREEN}Memory frame saved successfully: {save_results[0]['message']}{RESET}")
            else:
                print(f"{RED}Error saving memory frame: {save_results[0]['message']}{RESET}")

        except (KeyError, IndexError, TypeError) as e:
            print(f"{RED}Error processing memory entry.  Check JSON structure: {e}{RESET}")
            continue  # Skip to the next entry if there's a problem with this one.

        MEMORY_FRAME_NUMBER += 1