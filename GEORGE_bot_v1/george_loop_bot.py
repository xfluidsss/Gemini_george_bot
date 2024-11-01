import time
import google.generativeai as genai
import json
from typing import List, Dict, Optional
import logging
import os
from TOOL_MANAGER import ToolManager  # Assuming you have a TOOL_MANAGER.py file

# Color class (enhanced for more colors and easier use)
class Color:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    YELLOW = '\033[33m' # Added yellow
    PURPLE = '\033[35m' # Added purple

    def __init__(self, text, color):
        self.text = text
        self.color = color

    def __str__(self):
        return self.color + self.text + Color.ENDC

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Replace with your actual API key
from keys import googleKey  # Assuming you have a separate file for your API key

API_KEY = googleKey
genai.configure(api_key=API_KEY)

from google.generativeai.types import HarmCategory, HarmBlockThreshold

safety_settings = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
}


tool_manager = ToolManager("tools")

def print_colored(color: str, text: str):
    print(color + str(text) + Color.ENDC)


def load_focus_data(focus_file_path: str) -> str:
    """Loads focus data as a string from the specified file."""
    try:
        with open(focus_file_path, "r") as f:
            focus_data = f.read()
        return focus_data
    except FileNotFoundError:
        print_colored(Color.WARNING, f"Focus file not found: {focus_file_path}")
        return ""
    except Exception as e:
        print_colored(Color.FAIL, f"Error loading focus file: {e}")
        return ""


def extract_text_from_response(response) -> str:
    """Extracts text content from model response with error handling."""
    try:
        extracted_text = ""
        if response.candidates:
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    extracted_text += part.text
        return extracted_text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from response: {e}")
        return "Error processing response"


def handle_tool_calls(response):
    """Interprets and executes function calls from model response with enhanced error handling."""
    results = []
    try:
        if response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    for part in candidate.content.parts:
                        function_call = getattr(part, 'function_call', None)
                        if function_call:
                            print_colored(Color.OKBLUE, "---------------TOOL EXECUTION-------------------")
                            tool_name = function_call.name
                            tool_function = tool_manager.get_tool_function(tool_name)

                            if tool_function:
                                function_args = {
                                    arg_name: arg_value
                                    for arg_name, arg_value in function_call.args.items()
                                }

                                print(f"Executing: {Color.OKGREEN}{tool_name}{Color.ENDC}")
                                print("Arguments:")
                                for key, value in function_args.items():
                                    print(f"        {Color.OKCYAN}{key}{Color.ENDC}: {value}")

                                try:
                                    result = tool_function(**function_args)
                                    result_str = f"Tool {Color.OKGREEN}{tool_name}{Color.ENDC} executed successfully:\n{result}"
                                    results.append(result_str)
                                    print_colored(Color.OKGREEN, result_str)
                                except Exception as e:
                                    error_msg = f"Error executing {tool_name}: {str(e)}"
                                    logger.error(error_msg)
                                    results.append(error_msg)
                                    print_colored(Color.FAIL, error_msg)
                            else:
                                error_msg = f"Tool '{tool_name}' not found in available tools"
                                logger.warning(error_msg)
                                results.append(error_msg)
    except Exception as e:
        error_msg = f"Error interpreting tool calls: {str(e)}"
        logger.error(error_msg)
        results.append(error_msg)
    return results


def process_turn(user_input: str) -> None:
    global conversation_history, current_turn, memory
    try:
        # Reset the current turn
        current_turn = []

        # --- Stage 0: Input ---
        print(Color("---- Stage 0: Input ----", Color.HEADER))  # Colorful header
        conversation_history.append(f"User: {user_input}")  # Store plain text
        time.sleep(1)

        # --- Stage 1: Reasoner/Planner ---
        print(Color("---- Stage 1: Reasoner/Planner ----", Color.YELLOW))
        try:
            reasoner_planner_prompt = f"User Input: {user_input}\nCurrent Focus: {load_focus_data('focus/focus.json')}"
            reasoner_planner_response = reasoner_planner_model.generate_content(reasoner_planner_prompt)
            plan = extract_text_from_response(reasoner_planner_response)
            conversation_history.append(f"Reasoner/Planner: {plan}  update  your  focus")  # Store plain text
            print(Color(f"Plan: {plan}", Color.YELLOW))  # Print the plan
        except Exception as E:
            print_colored(Color.FAIL, f"Error in Reasoner/Planner: {E}")

        # --- Stage 2: Action Taker ---
        print(Color("---- Stage 2: Action Taker ----", Color.OKGREEN))
        try:
            action_taker_prompt = f"{action_taking_system_instruction.replace('[Plan will be inserted here]', plan)}"
            response_action_taker = action_taker_model.generate_content(action_taker_prompt)

            conversation_history.append(f"Action Taker: {response_action_taker}")  # Store plain text
            text_extracted_response = extract_text_from_response(response_action_taker)
            print(Color(f"Extracted Text: {text_extracted_response}", Color.OKGREEN))
            tool_results = handle_tool_calls(response_action_taker)
            conversation_history.extend(tool_results)  # Store plain text
            current_turn.extend(tool_results)

        except Exception as E:
            print_colored(Color.FAIL, f"Error in Action Taker: {E}")

        # --- Stage 3: Evaluator ---
        print(Color("---- Stage 3: Evaluator ----", Color.PURPLE))
        try:
            conversation_history.append(
                "focus of evaluation of results and propose course of action, you must update your focus, you must described what has been accomplished"
            )
            response_evaluator = evaluator_model.generate_content(conversation_history)

            conversation_history.append(f"Evaluator: {response_evaluator}")  # Store plain text
            text_extracted_response = extract_text_from_response(response_evaluator)
            print(Color(f"Extracted Text: {text_extracted_response}", Color.PURPLE))

            tool_results = handle_tool_calls(response_evaluator)
            conversation_history.extend(tool_results)  # Store plain text

        except Exception as E:
            print_colored(Color.FAIL, f"Error in Evaluator: {E}")

    except Exception as e:
        print(e)
        for entry in conversation_history:
            print(entry)
        time.sleep(5)


# Initialize conversation history
conversation_history = []
current_turn = []
memory = {}
availbe_tools = tool_manager.get_short_tool_descriptions()
print("************************************************************************************")
print(availbe_tools)
# System instructions for each model
input_system_instruction = f"""
You are a helpful AI assistant with a focus on completing the current task. 
You can update your internal focus.
You have access to these tools: {availbe_tools}
"""
print()
action_taking_system_instruction = """
You are a tool execution expert. Do not hallucinate! 
Execute the following actions based on the identified focus and tool suggestions: [List the actions from the input model].

"""

evaluation_system_instruction = """
Summarize results, identify issues, and suggest improvements.
Explain your reasoning. Based on the results, update your focus  .
"""

# Initialize models
try:
    input_model = genai.GenerativeModel(
        model_name='gemini-1.5-flash-latest',
        safety_settings=safety_settings,
        system_instruction=input_system_instruction,
        tools=tool_manager.load_tools_of_type("all")
    )
except Exception as E:
    print_colored(Color.FAIL, f"Error initializing input_model: {E}")

try:
    action_taker_model = genai.GenerativeModel(
        model_name='gemini-1.5-flash-latest',
        safety_settings=safety_settings,
        system_instruction=action_taking_system_instruction,
        tools=tool_manager.load_tools_of_type("all")
    )
except Exception as E:
    print_colored(Color.FAIL, f"Error initializing action_taker_model: {E}")

try:
    evaluator_model = genai.GenerativeModel(
        model_name='gemini-1.5-flash-latest',
        safety_settings=safety_settings,
        system_instruction=evaluation_system_instruction,
        tools=tool_manager.load_tools_of_type("all")
    )
except Exception as E:
    print_colored(Color.FAIL, f"Error initializing evaluator_model: {E}")

reasoner_planner_system_instruction = """
You are a strategic planner. Based on the user input and the current focus, create a plan of action. DO NOT use tools.  Your output should be a concise plan.
"""
try:
    reasoner_planner_model = genai.GenerativeModel(
        model_name='gemini-1.5-flash-latest',
        safety_settings=safety_settings,
        system_instruction=reasoner_planner_system_instruction
        # Notice: No tools provided here
    )
except Exception as E:
    print_colored(Color.FAIL, f"Error initializing reasoner_planner_model: {E}")


# Main Loop:
# Initial user input
user_input = input("user_input: ")
process_turn(user_input)

while True:
    # Ask for user input after every 3 turns
    for _ in range(3):
        process_turn("")  # Process empty input for the next 3 turns

    user_input = input("user_input: ")  # Get user input after 3 turns
    process_turn(user_input)