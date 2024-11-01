import google.generativeai as genai
import json
from typing import List, Dict, Optional
import logging
import os
from TOOL_MANAGER import ToolManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
from keys import googleKey

google_key = os.environ.get('googleKEY')

genai.configure(api_key=google_key)
from google.generativeai.types import HarmCategory, HarmBlockThreshold




safety_settings={
HarmCategory.HARM_CATEGORY_HATE_SPEECH:HarmBlockThreshold.BLOCK_NONE,
HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT:HarmBlockThreshold.BLOCK_NONE,
HarmCategory.HARM_CATEGORY_HARASSMENT:HarmBlockThreshold.BLOCK_NONE,
HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT:HarmBlockThreshold.BLOCK_NONE,
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


class ConversationManager:
    def __init__(self, max_history: int = 10):
        self.history = []
        self.max_history = max_history

    def add_message(self, role: str, content: str):
        """Add a message to the conversation history with role tracking."""
        message = {"role": role, "content": content}
        self.history.append(message)

        # Trim history if it exceeds max length while preserving context
        if len(self.history) > self.max_history:
            # Keep the first message (system prompt) and most recent messages
            self.history = [self.history[0]] + self.history[-(self.max_history - 1):]

    def get_formatted_history(self) -> str:
        """Format conversation history for model input."""
        formatted_history = []
        for msg in self.history:
            role_prefix = "User: " if msg["role"] == "user" else "Assistant: "
            formatted_history.append(f"{role_prefix}{msg['content']}")
        return "\n".join(formatted_history)

    def clear_history(self):
        """Clear conversation history except for the system prompt."""
        if self.history:
            self.history = [self.history[0]]


def print_colored(color: str, text: str):
    print(color + str(text) + Color.ENDC)


class AIAssistant:
    def __init__(self, tools_folder: str = "tools"):
        self.tool_manager = ToolManager(tools_folder)
        self.conversation = ConversationManager()

        # Enhanced system prompts
        planner_prompt = """You are a highly capable AI assistant focused on planning and executing tasks. Your role is to:
1. Carefully analyze user requests and break them down into actionable steps
2. Use available tools appropriately and strategically
3. Maintain context across the conversation
4. Be explicit about your reasoning and planning process

When using tools:
- Only call tools when necessary and relevant
- Validate inputs before making tool calls
- Handle potential errors gracefully
- Explain your tool selection process

Remember: Quality over quantity in tool usage. Don't use tools unless they directly help accomplish the user's goal."""

        executor_prompt = """You are an analytical AI assistant that evaluates results and provides insights.
"""

        self.input_model = genai.GenerativeModel(
            model_name='gemini-1.5-flash-latest',
            safety_settings=safety_settings,
            system_instruction=planner_prompt,
            tools=self.tool_manager.load_tools_of_type("all")
        )

        self.executor_model = genai.GenerativeModel(
            model_name='gemini-1.5-flash-latest',
            safety_settings=safety_settings,
            system_instruction=executor_prompt
        )

        # Add system prompts to conversation history
        self.conversation.add_message("system", planner_prompt)

    def extract_text_from_response(self, response) -> str:
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

    def interpret_tool_calls(self, response) -> List[str]:
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
                                tool_function = self.tool_manager.get_tool_function(tool_name)

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

    def process_user_input(self, user_input: str) -> None:
        """Process user input and generate responses with full conversation context."""
        try:
            # Add user input to conversation history
            self.conversation.add_message("user", user_input)

            # Planning Stage
            print_colored(Color.OKBLUE, "\n--- Planning Stage ---")
            input_response = self.input_model.generate_content(self.conversation.get_formatted_history())
            input_response_text = self.extract_text_from_response(input_response)

            if input_response_text:
                print_colored(Color.OKGREEN, input_response_text)
                self.conversation.add_message("assistant", input_response_text)

            # Tool Execution Stage
            results = self.interpret_tool_calls(input_response)
            if results:
                # Add tool results to conversation history
                tool_results_text = "\n".join(results)
                self.conversation.add_message("system", f"Tool Results:\n{tool_results_text}")

                # Evaluation Stage
                print_colored(Color.OKBLUE, "\n--- Evaluation Stage ---")
                executor_response = self.executor_model.generate_content(self.conversation.get_formatted_history())
                executor_text = self.extract_text_from_response(executor_response)

                if executor_text:
                    print_colored(Color.OKGREEN, executor_text)
                    self.conversation.add_message("assistant", executor_text)

        except Exception as e:
            error_msg = f"Error processing user input: {str(e)}"
            logger.error(error_msg)
            print_colored(Color.FAIL, error_msg)


def main():
    assistant = AIAssistant()
    print_colored(Color.HEADER, "AI Assistant initialized. Type 'exit' to quit.")

    while True:
        try:
            user_input = input(Color.OKCYAN + "\nWhat would you like to do? " + Color.ENDC).strip()

            if user_input.lower() in ['exit', 'quit']:
                print_colored(Color.OKGREEN, "Goodbye! 👋")
                break

            if user_input.lower() == 'clear':
                assistant.conversation.clear_history()
                print_colored(Color.OKGREEN, "Conversation history cleared!")
                continue

            assistant.process_user_input(user_input)

        except KeyboardInterrupt:
            print_colored(Color.WARNING, "\nInterrupted by user. Type 'exit' to quit.")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            print_colored(Color.FAIL, f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()