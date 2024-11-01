import time
import google.generativeai as genai
import json
from typing import List, Dict, Optional
import logging
import os
from TOOL_MANAGER import ToolManager  # Assuming you have a TOOL_MANAGER.py file
import datetime

tool_manager = ToolManager("tools")

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


def stopFlagDetection(response):
    """Checks for the stop flag in the response."""
    StopFlag = "***STOP_FINISHED***"
    try:
        extracted_text = extract_text_from_response(response)
        return StopFlag in extracted_text
    except Exception as e:
        logger.error(f"Error in stop flag detection: {e}")
        return False


def process_turn(user_input: str) -> bool:
    """Handles a single turn in the conversation and returns True if stop flag is detected."""
    global conversation_history, current_turn, memory
    try:
        # Reset the current turn
        current_turn = []

        # Stage 1: Input/Reasoning Model
        conversation_history.append(f"User: {user_input}")
        time.sleep(1)
        combined_prompt = f"""

            Conversation:
            {conversation_history[-1]} 
            Focus: {load_focus_data('focus/focus.json')} What are the possible actions to take next? 
            Available Tools:
            {tool_manager.get_short_tool_descriptions()}
        """
        try:
            response_input = input_model.generate_content(combined_prompt)
            print(f"Input/Reasoning Model Response: {response_input}")

            conversation_history.append(f" {response_input}")
            text_extracted_response = extract_text_from_response(response_input)

            tool_results = handle_tool_calls(response_input)
            print(f"Extracted Text: {text_extracted_response}")
            print(f"Tool Results: {tool_results}")
            conversation_history.append(f"obtained tool Results in conversation context: {tool_results}")
            current_turn.extend(tool_results)
        except Exception as E:
            print_colored(Color.FAIL, f"Error generating content from Input/Reasoning Model: {E}")

        # Stage 2: Action Taker
        time.sleep(1)
        try:
            conversation_history.append("take  next  step  accoording  to   logical execution of  steps  ")
            response_action_taker = action_taker_model.generate_content(conversation_history)
            print(f"Action Taker Model Response: {response_action_taker}")

            conversation_history.append(f"Action Taker Model Response: {response_action_taker}")
            text_extracted_response = extract_text_from_response(response_action_taker)
            print(f"Extracted Text: {text_extracted_response}")

            tool_results = handle_tool_calls(response_action_taker)
            print(f"Tool Results: {tool_results}")
            conversation_history.append(f"Tool Results: {tool_results}")
            current_turn.extend(tool_results)
        except Exception as E:
            print_colored(Color.FAIL, f"Error generating content from Action Taker Model: {E}")

        # Stage 3: Evaluator Model
        time.sleep(3)
        try:
            conversation_history.append(" update  your  focus ,evaluate  resuls")
            conversation_history.append("when main gaol is  achived  use write  ***STOP_FINISHED*** ")
            response_evaluator = evaluator_model.generate_content(conversation_history)
            print(f"Evaluator Model Response: {response_evaluator}")
            conversation_history.append(f"Evaluator Model Response: {response_evaluator}")
            text_extracted_response = extract_text_from_response(response_evaluator)
            print(f"Extracted Text: {text_extracted_response}")

            tool_results = handle_tool_calls(response_evaluator)
            print(f"Tool Results: {tool_results}")
            conversation_history.extend(tool_results)
        except Exception as E:
            print_colored(Color.FAIL, f"Error generating content from Evaluator Model: {E}")

        # Check for stop flag after each model call
        if stopFlagDetection(response_input):
            return True
        if stopFlagDetection(response_action_taker):
            return True
        if stopFlagDetection(response_evaluator):
            return True

        return False  # No stop flag detected

    except Exception as e:
        print(e)
        for entry in conversation_history:
            print(entry)
        time.sleep(5)
        return False  # Don't stop on other errors


# Initialize conversation history
conversation_history = []
current_turn = []
memory = {}
availbe_tools = tool_manager.get_short_tool_descriptions()
print("************************************************************************************")
print(availbe_tools)
# System instructions for each model
input_system_instruction = f"""
Available Tools: {availbe_tools}

Output Requirements:
- Explicitly list potential action steps

You are an expert in understanding and reasoning about complex tasks. 
Your goal is to guide the action taker model through the execution of the plan.
- If you detect that the goal has been achieved, write:
    "***STOP_FINISHED***" 
"""
print()
action_taking_system_instruction = """
You are a precise, methodical tool execution specialist with these core responsibilities:

Execution Principles:
- Execute tools with absolute precision
- Strictly follow the plan developed by the Input/Reasoning Model
- If you detect that the goal has been achieved, write:
    "***STOP_FINISHED***"
"""

evaluation_system_instruction = """
You are a comprehensive assessment and optimization specialist 

- Evaluate the results of the executed tools.
- Update the focus file.
- If you detect that the goal has been achieved, write:
    "***STOP_FINISHED***"
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
        tools=tool_manager.load_tools_of_type("focus")
    )
except Exception as E:
    print_colored(Color.FAIL, f"Error initializing evaluator_model: {E}")

# Main Loop:
# Initial user input
user_input = input("user_input: ")
should_stop = process_turn(user_input)

# Create a directory for session logs
session_logs_dir = "session_logs"
os.makedirs(session_logs_dir, exist_ok=True)

# Get the current date and time for the session log file
log_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
session_log_file = os.path.join(session_logs_dir, f"session_log_{log_time}.txt")

# Open the session log file in append mode
with open(session_log_file, "a") as session_log:
    session_log.write(f"Session started at: {log_time}\n\n")

    loop_count = 0  # Initialize loop count
    while True:
        # Ask for user input after every 3 turns
        for _ in range(3):
            loop_count += 1  # Increment loop count
            should_stop = process_turn("")  # Process empty input for the next 3 turns
            if should_stop:
                print("Task completed.  Press Enter to continue the conversation.")
                input()  # Wait for user input (Enter key)
                should_stop = False  # Reset stop flag for new conversation
                break  # Exit inner loop

        if should_stop:
            break  # Exit outer loop if stop flag is found

        user_input = input("user_input: ")
        should_stop = process_turn(user_input)

        # Write the current loop to the session log with loop count
        session_log.write(f"Loop {loop_count}: \n")
        session_log.write(f"User: {user_input}\n")
        for entry in conversation_history:
            session_log.write(f"{entry}\n")
        session_log.write("\n")

    # Close the session log file
    session_log.write(f"Session ended at: {datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}\n\n")
    session_log.close()