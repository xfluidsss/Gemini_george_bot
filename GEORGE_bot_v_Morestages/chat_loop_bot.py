import time
import google.generativeai as genai
import json
from typing import List, Dict, Optional
import logging
import os
from TOOL_MANAGER import  ToolManager
tool_manager=ToolManager()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Replace with your actual API key
from keys import googleKey

API_KEY = googleKey
genai.configure(api_key=API_KEY)

from google.generativeai.types import HarmCategory, HarmBlockThreshold

safety_settings = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
}

# Load prompts and system instructions from JSON files
with open('configs/prompts.json', 'r') as f:
    prompts = json.load(f)
with open('configs/system_instructions.json', 'r') as f:
    system_instructions = json.load(f)

# Initialize models with safety settings and system instructions
input_model_name = "gemini-1.5-flash-latest"
action_taker_model_name = "gemini-1.5-flash-latest"
evaluator_model_name = "gemini-1.5-flash-latest"
input_model = genai.GenerativeModel(
    model_name=input_model_name,
    safety_settings=safety_settings,
    system_instruction=system_instructions.get("input_model", "")
)

action_taker_model = genai.GenerativeModel(
    model_name=action_taker_model_name,
    safety_settings=safety_settings,
    system_instruction=system_instructions.get("action_taker_model", "")
)

evaluator_model = genai.GenerativeModel(
    model_name=evaluator_model_name,
    safety_settings=safety_settings,
    system_instruction=system_instructions.get("evaluator_model", "")
)

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

def check_for_finish_flag(response):
    """Checks for the finish flag in the model's response."""
    flag_to_detect = "***STOP!FINISHED***"
    return flag_to_detect in extract_text_from_response(response)

def process_turn(user_input: str) -> bool:
    """Handles a single turn in the conversation."""
    global conversation_history, current_turn, memory

    try:
        # Reset the current turn
        current_turn = []

        # Stage 1: Input/Reasoning Model
        conversation_history.append(f"User: {user_input}")
        time.sleep(1)

        # Build a combined prompt for the input model
        input_prompt = f"""
            Conversation:
            {'\n'.join(conversation_history)}
            Focus: {load_focus_data('focus/focus.json')} 
            {prompts.get('input_model_prompt', '')}

            Available Tools:
            {tool_manager.get_short_tool_descriptions()}
        """

        try:
            response_input = input_model.generate_content(input_prompt)
            print(f"Input/Reasoning Model Response: {response_input}")

            conversation_history.append(f"Input/Reasoning Model: {extract_text_from_response(response_input)}")
            tool_results = handle_tool_calls(response_input)
            print(f"Tool Results: {tool_results}")

            # Add tool results to conversation history
            for result in tool_results:
                conversation_history.append(f"Tool: {result}")

            current_turn.extend(tool_results)

            # Check for finish flag in Input Model's response
            if check_for_finish_flag(response_input):
                print_colored(Color.OKGREEN, "Input Model signaled task completion. Returning to user input.")
                return False  # Signal to break the main loop

        except Exception as E:
            print_colored(Color.FAIL, f"Error generating content from Input/Reasoning Model: {E}")

        # Stage 2: Action Taker
        time.sleep(1)
        try:
            action_prompt = f"""
                Conversation:
                {'\n'.join(conversation_history)}
                {prompts.get('action_taker_model_prompt', '')}
                take  next  step  accoording  to   logical execution of  steps 
            """

            response_action_taker = action_taker_model.generate_content(action_prompt)
            print(f"Action Taker Model Response: {response_action_taker}")

            conversation_history.append(f"Action Taker Model: {extract_text_from_response(response_action_taker)}")
            tool_results = handle_tool_calls(response_action_taker)
            print(f"Tool Results: {tool_results}")

            # Add tool results to conversation history
            for result in tool_results:
                conversation_history.append(f"Tool: {result}")

            current_turn.extend(tool_results)

            # Check for finish flag in Action Taker Model's response
            if check_for_finish_flag(response_action_taker):
                print_colored(Color.OKGREEN, "Action Taker Model signaled task completion. Returning to user input.")
                return False  # Signal to break the main loop

        except Exception as E:
            print_colored(Color.FAIL, f"Error generating content from Action Taker Model: {E}")

        # Stage 3: Evaluator Model
        time.sleep(3)
        try:
            evaluation_prompt = f"""
                Conversation:
                {'\n'.join(conversation_history)}
                {prompts.get('evaluator_model_prompt', '')}
                update  your  focus , you must  describe   what  has  been accomplished 
            """

            response_evaluator = evaluator_model.generate_content(evaluation_prompt)
            print(f"Evaluator Model Response: {response_evaluator}")

            conversation_history.append(f"Evaluator Model: {extract_text_from_response(response_evaluator)}")
            tool_results = handle_tool_calls(response_evaluator)
            print(f"Tool Results: {tool_results}")

            # Add tool results to conversation history
            for result in tool_results:
                conversation_history.append(f"Tool: {result}")

            # Check for finish flag in Evaluator Model's response
            if check_for_finish_flag(response_evaluator):
                print_colored(Color.OKGREEN, "Evaluator Model signaled task completion. Returning to user input.")
                return False  # Signal to break the main loop

            return True  # Continue processing

        except Exception as E:
            print_colored(Color.FAIL, f"Error generating content from Evaluator Model: {E}")
            return True

    except Exception as e:
        print(e)
        for entry in conversation_history:
            print(entry)
        time.sleep(5)
        return True


# Initialize conversation history and current turn
conversation_history = []
current_turn = []
memory = {}

if __name__ == "__main__":
    print_colored(Color.OKGREEN, "Welcome to GEORGE, your AI assistant!")
    print("Type 'quit' to exit.")
    while True:
        user_input = input(f"{Color.OKCYAN}You: {Color.ENDC}")
        if user_input.lower() == "quit":
            break
        process_turn(user_input)