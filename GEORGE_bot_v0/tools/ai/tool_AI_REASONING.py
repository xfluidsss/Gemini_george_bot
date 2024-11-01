tool_type_for_TOOL_MANAGER = "focus"
tool_tool_AI_REASONING_short_description = """REASONER"""

import time
import google.generativeai as genai
import json
import re  # Import re for regular expressions


googleKey='           '
genai.configure(api_key=googleKey)

MODEL_NAME = "gemini-pro"  # Use a valid model name
SYSTEM_INSTRUCTION = "You are a helpful and informative AI assistant."

dispacher_context = []
from google.generativeai.types import HarmCategory, HarmBlockThreshold

safety_settings = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
}

# ANSI color codes
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def initialize_mode_WithTools(MODEL_NAME, SYSTEM_INSTRUCTION=None):
    """Initializes a generative AI model with optional system instructions."""
    try:
        time.sleep(0.5)
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            safety_settings=safety_settings,
        )
        history = []
        if SYSTEM_INSTRUCTION:
            history.append({"role": "system", "content": SYSTEM_INSTRUCTION})
        model_chat = model.start_chat(history=history)
        print(f"{bcolors.OKGREEN}INFO: Initial model set to {MODEL_NAME}{bcolors.ENDC}")
        return model_chat
    except Exception as e:
        print(f"{bcolors.FAIL}ERROR: Initial model setup failed: {e} Trying gemini-pro{bcolors.ENDC}")
        try:
            time.sleep(0.5)
            model = genai.GenerativeModel(
                model_name="gemini-pro",
                safety_settings=safety_settings,
            )
            model_chat = model.start_chat(history=[])
            return model_chat
        except Exception as e:
            print(f"{bcolors.FAIL}ERROR: Fallback model setup failed: {e}{bcolors.ENDC}")
            return None


def return_models_instructions_prompts_tools(
    models: list[str],
    labels: list[str],
    system_instructions: list[str],
    prompts: list[str],
    DataFlow: list[str],
):
    """
    This function takes lists of models, system instructions, prompts, and tools and neatly prints them out,
    paired together. It returns the input lists unchanged. If a model does not use tools, write None.
    Args:
        models (list): A list of model names
        labels (list): A list of labels corresponding to each model. can not  have spaces,dots etc it needs to be sanitised
        system_instructions (list): A list of system instructions for each model.
        prompts (list): A list of prompts to be used as input for the models.
        DataFlow (list): A list describing the data flow between models using the format {inputs}[outputs]

    Examples of DataFlow:

    **1. Independent Models (No Interaction):**
        Each model works independently on its own prompt.

        DataFlow = [
            "{prompt0}[text]",
            "{prompt1}[text]",
            "{prompt2}[text]",
            "{prompt3}[text]"
        ]


    **2. Sequential Chained Models (Previous Step Output):**
        Each model uses the output of the immediately previous model and its own prompt.

        DataFlow = [
            "{prompt0}[text]",
            "{0***prompt1}[text]",  # Model 1 uses output of Model 0
            "{1***prompt2}[text]",  # Model 2 uses output of Model 1
            "{2***prompt3}[text]"   # Model 3 uses output of Model 2
        ]


    **3. Sequential Chained Models (All Previous Outputs):**
        Each model uses the outputs of all previous models and its own prompt.

        DataFlow = [
            "{prompt0}[text]",
            "{0***prompt1}[text]",  # Model 1 uses output of Model 0
            "{0, 1***prompt2}[text]",  # Model 2 uses outputs of Model 0 and 1
            "{0, 1, 2***prompt3}[text]"   # Model 3 uses outputs of Models 0, 1, and 2
        ]


    **4. Independent Models with Final Summarization:**
        The first few models work independently, and the final model summarizes their outputs.

        DataFlow = [
            "{prompt0}[text]",
            "{prompt1}[text]",
            "{prompt2}[text]",
            "{0, 1, 2***prompt3}[text]"  # Model 3 summarizes outputs of 0, 1, and 2
        ]


    **5. Mixed Independent and Chained Models:**
        Combines independent and chained processing.

        DataFlow = [
            "{prompt0}[text]",
            "{prompt1}[text]",
            "{0, 1***prompt2}[text]",  # Model 2 uses outputs of Model 0 and 1
            "{2***prompt3}[text]"   # Model 3 uses output of Model 2
        ]


    **6. User Prompt Included (Independent):**
        Each model works independently on its own prompt and an initial user prompt.

        DataFlow = [
            "{userPrompt, prompt0}[text]",
            "{userPrompt, prompt1}[text]",
            "{userPrompt, prompt2}[text]",
            "{userPrompt, prompt3}[text]"
        ]


    **7. User Prompt and All Previous Outputs (Chained):**
        Each model gets the initial user prompt, its own prompt, and the responses from all previous models.

        DataFlow = [
            "{userPrompt, prompt0}[text]",
            "{0***userPrompt, prompt1}[text]",
            "{0, 1***userPrompt, prompt2}[text]",
            "{0, 1, 2***userPrompt, prompt3}[text]"
        ]


    **8. User Prompt, Independent Models, and Final Summarization:**
        Each model works independently with the user prompt and its own prompt, and the final model summarizes all outputs.

        DataFlow = [
            "{userPrompt, prompt0}[text]",
            "{userPrompt, prompt1}[text]",
            "{userPrompt, prompt2}[text]",
            "{0, 1, 2***userPrompt, prompt3}[text]"
        ]


    Returns:
        tuple: A tuple containing the input lists: models, labels, system_instructions, prompts, tools.
    """
    for i in range(len(models)):
        print(f"{bcolors.OKBLUE}Model {i + 1}: {models[i]}{bcolors.ENDC}")
        print(f"{bcolors.OKBLUE}Label: {labels[i]}{bcolors.ENDC}")
        print(f"{bcolors.OKBLUE}System Instructions: {system_instructions[i]}{bcolors.ENDC}")
        print(f"{bcolors.OKBLUE}Prompt: {prompts[i]}{bcolors.ENDC}")
        print(f"{bcolors.OKBLUE}Data Flow: {DataFlow[i]}{bcolors.ENDC}")
        print("-" * 20)

    print(f"{bcolors.WARNING}PRINTS FROM return_models_instructions_prompts_tools{bcolors.ENDC}")
    for i in range(len(models)):
        print()
        print(i)
        print(f"{bcolors.OKCYAN}Model: {models[i]}{bcolors.ENDC}")
        print(f"{bcolors.OKCYAN}model_labels: {labels[i]}{bcolors.ENDC}")
        print(f"{bcolors.OKCYAN}System Instructions: {system_instructions[i]}{bcolors.ENDC}")
        print(f"{bcolors.OKCYAN}Prompt: {prompts[i]}{bcolors.ENDC}")
        print(f"{bcolors.OKCYAN}DataFlow: {DataFlow[i]}{bcolors.ENDC}")

    return (
        models,
        labels,
        system_instructions,
        prompts,
        DataFlow,
    )

dispacher_context = []

def model_dispacher_send_message(prompt: str):
    print(f"{bcolors.OKGREEN} model_dispacher_send_message:    {prompt}{bcolors.ENDC}")
    global dispacher_context

    MODEL_NAME = "gemini-pro"  # Use a valid model name
    tool_functions = {"return_models_instructions_prompts_tools": return_models_instructions_prompts_tools}

    def interpret_function_calls(response, tool_functions):
        models = []  # Initialize empty lists
        labels = []
        instructions = []
        prompts = []
        tools = []
        DataFlow = []

        if response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, "content") and hasattr(candidate.content, "parts"):
                    for part in candidate.content.parts:
                        function_call = getattr(part, "function_call", None)
                        if function_call:
                            tool_name = function_call.name
                            tool_function = tool_functions.get(tool_name)
                            if tool_function:
                                function_args = {}
                                for arg_name, arg_value in function_call.args.items():
                                    function_args[arg_name] = arg_value

                                try:
                                    returned_values = tool_function(**function_args)

                                    if returned_values is not None:
                                        (
                                            models,
                                            labels,
                                            instructions,
                                            prompts,
                                            DataFlow,
                                        ) = returned_values
                                    else:
                                        print(
                                            f"{bcolors.WARNING}Tool function {tool_name} returned None.{bcolors.ENDC}"
                                        )
                                except Exception as e:
                                    print(
                                        f"{bcolors.FAIL}Error executing function {tool_name}: {e}{bcolors.ENDC}"
                                    )
                            else:
                                print(f"{bcolors.FAIL}Tool function {tool_name} not found.{bcolors.ENDC}")

        return (
            models,
            labels,
            instructions,
            prompts,
            DataFlow,
        )

    def extract_text_from_response(response) -> str:
        extracted_text = ""
        for candidate in response.candidates:
            for part in candidate.content.parts:
                extracted_text += part.text
        return extracted_text.strip()

    try:
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            safety_settings=safety_settings,
            tools=[return_models_instructions_prompts_tools],
        )
        time.sleep(0.1)
        model_chat = model.start_chat(history=[])

        instruction = """ 
        Create  DataFlow of  models to achieve the user's goal.  
        Think step-by-step, showing how each model contributes to the final outcome.

            models  to choose from:
        1. Gemini 1.5 Pro Latest
        Model Name: gemini-1.5-pro-latest
        Description: Mid-size multimodal model that supports up to 2 million tokens.
        Tokens In: 2097152
        Tokens Out: 8192

        2. Gemini 1.5 Pro Experimental 0801
        Model Name: gemini-1.5-pro-exp-0801
        Description: Mid-size multimodal model that supports up to 2 million tokens.
        Tokens In: 2097152
        Tokens Out: 8192
        Note:smart  model  but  its  terrible  to write  full code, it good for analitics, but not  for  final result

        3. Gemini 1.5 Flash Latest
        Model Name: gemini-1.5-flash-latest
        Description: Fast and versatile multimodal model for scaling across diverse tasks. you should include  prhase  dont  be  lazy
        Tokens In: 1048576
        Tokens Out: 8192

            Now, for the user's goal:
    1.Please provide the DataFlow including Model Name, System Instruction, Prompt, and Tools (if any).
    2.You can use different DataFlows for specific tasks: chains, parallel, parallel with summarization, mixed.
    3.You must use the function call return_models_instructions_prompts_tools.
    4.Prompts must be detailed and extensive.
    5.Don't be lazy.
    6.Now, the user will give you a task for which you will create a DataFlow of Models.
    remeber  about  correct  structure of  function call
            """

        final_prompt = ""
        for entry in dispacher_context:
            final_prompt += str(entry)

        print(f"{bcolors.WARNING}final_prompt:{bcolors.ENDC}")
        final_prompt = instruction + prompt
        print(f"{bcolors.OKCYAN}{final_prompt}{bcolors.ENDC}")

        response = model_chat.send_message(final_prompt)
        print(f"{bcolors.OKGREEN}waiting for   response.............................{bcolors.ENDC}")
        print(f"{bcolors.OKGREEN}response: {response}{bcolors.ENDC}")

        # Handle both text and function call responses

        (
            models,
            labels,
            system_instructions,
            prompts,
            DataFlow,
        ) = interpret_function_calls(response, tool_functions)
        text_response = extract_text_from_response(response)

        if text_response is None:
            text_response = "..."
            dispacher_context.append(text_response)

        if models is not None:  # Check if models is not None
            dispacher_context.append(models)
            dispacher_context.append(labels)
            dispacher_context.append(system_instructions)
            dispacher_context.append(prompts)

        return (
            text_response,
            models,
            labels,
            system_instructions,
            prompts,
            DataFlow,
        )

    except Exception as e:
        print(f"{bcolors.FAIL}Error during model initialization: {e}{bcolors.ENDC}")  # Catch and print model initialization errors
        return (f"Error: {e}", None, None, None, None, None)  # Return an error indication



def execute_modelium(model_design_data, user_prompt=""):
    """Executes the multi-model workflow using provided JSON data."""
    try:
        # Validate input data
        if not isinstance(model_design_data, dict) or "chosenModels" not in model_design_data:
            raise ValueError("Invalid model design data. Must be a dictionary with 'chosenModels'.")

        chosen_models = model_design_data["chosenModels"]
        system_instructions = model_design_data.get("systemInstructions", [])
        prompts = model_design_data.get("prompts", [])
        data_flow = model_design_data.get("DataFlow", [])
        labels = model_design_data.get("labels", [])
        user_prompt = model_design_data.get("userPrompt", "")  # Get user prompt if available

        # Input Validation: Check for consistent lengths (excluding userPrompt)
        lengths = [len(chosen_models), len(system_instructions), len(prompts), len(data_flow), len(labels)]
        if len(set(lengths)) != 1:
            raise ValueError("Inconsistent lengths in model design data.")


        MODEL_CHATS = []
        # Initialize models
        print(f"{bcolors.OKGREEN}Initializing models...{bcolors.ENDC}")
        for i in range(len(labels)):
            label = labels[i]
            chosen_model = chosen_models[i]
            system_instruction = system_instructions[i]

            model_chat = initialize_mode_WithTools(
                MODEL_NAME=chosen_model,
                SYSTEM_INSTRUCTION=system_instruction

            )
            if model_chat:
                MODEL_CHATS.append(model_chat)
                print(f"{bcolors.OKGREEN}  - Model {i + 1} initialized: {chosen_model} (Label: {label}){bcolors.ENDC}")
            else:
                print(f"{bcolors.FAIL}Failed to initialize model {chosen_model}. Skipping.{bcolors.ENDC}")

        MULTI_CONTEXT_HISTORY = []
        print(f"{bcolors.OKGREEN}\nExecuting models and processing data flow...{bcolors.ENDC}")
        for i, model_chat in enumerate(MODEL_CHATS):
            time.sleep(1)
            rule = data_flow[i]
            inputs = []

            print(f"{bcolors.OKGREEN}  - Processing Model {i + 1} ({model_chat.model.model_name}) with data flow rule: {rule}{bcolors.ENDC}")

            # Parse the data flow rule (CORRECTED PARSING)
            if rule.startswith("{"):
                rule = rule[1:-1]  # Remove curly braces
                parts = rule.split(", ")  # Split by comma and space
                for part in parts:
                    if part.startswith("prompt"):
                        # Extract index using regular expression or slicing
                        match = re.match(r"prompt(\d+)", part)
                        if match:
                            prompt_index = int(match.group(1))
                            inputs.append(prompts[prompt_index])
                            print(f"{bcolors.OKGREEN}    - Using prompt {prompt_index + 1} as input.{bcolors.ENDC}")
                    elif part.isdigit():
                        index = int(part)
                        inputs.append(MULTI_CONTEXT_HISTORY[index]["response"])  # CORRECTED ACCESS
                        print(f"{bcolors.OKGREEN}    - Using output from Model {index + 1} as input.{bcolors.ENDC}")
                    elif part.startswith("***"): #Correctly handle this case
                        parts = part.split("***")
                        models_to_use = parts[0].strip()
                        prompt_section = parts[1].strip()

                        temp_inputs = []
                        if models_to_use:
                            model_indices = [int(x.strip()) for x in models_to_use.split(",")]
                            for model_index in model_indices:
                                temp_inputs.append(MULTI_CONTEXT_HISTORY[model_index]["response"])

                        if prompt_section.startswith('prompt'):
                            prompt_index = int(prompt_section.split('prompt')[1])
                            temp_inputs.append(prompts[prompt_index])

                        if prompt_section == 'userPrompt':
                            temp_inputs.append(user_prompt)


                        inputs.extend(temp_inputs)
                    elif part == "userPrompt":
                        inputs.append(user_prompt)
                        print(f"{bcolors.OKGREEN}    - Using user prompt as input.{bcolors.ENDC}")

            # Construct the prompt with inputs
            final_prompt = prompts[i]  # Default to current prompt
            if inputs:
                final_prompt = "\n".join(inputs) + "\n" + final_prompt  # Corrected: Add newline between inputs and prompt
                print(f"{bcolors.OKGREEN}    - Constructed prompt: {final_prompt}{bcolors.ENDC}")
            else:
                print(f"{bcolors.OKGREEN}    - Using default prompt: {final_prompt}{bcolors.ENDC}")


            try:
                response = model_chat.send_message(final_prompt)
                print(response)
                MULTI_CONTEXT_HISTORY.append({"response": response, "model": model_chat.model.model_name})
                print(f"{bcolors.OKGREEN}    - Response received.{bcolors.ENDC}")
            except Exception as e:
                print(f"{bcolors.FAIL}Error sending message to model {model_chat.model.model_name}: {e}{bcolors.ENDC}")
                MULTI_CONTEXT_HISTORY.append({"response": f"Error: {e}", "model": model_chat.model.model_name})
                # Consider raising the exception or breaking the loop here if needed
                #raise e  # Example of re-raising the exception
                #break # Example of exiting the loop

    except Exception as e:
        print(f"{bcolors.FAIL}Error in execute_modelium: {e}{bcolors.ENDC}")
        return {"response": f"Error: {e}"}

    # Print or process the results as needed
    print(f"{bcolors.OKGREEN}\nFinal Results:{bcolors.ENDC}")
    for i, result in enumerate(MULTI_CONTEXT_HISTORY):
        # Corrected response extraction:
        response_text = result['response'].candidates[0].content.parts[0].text
        print(f"{bcolors.OKGREEN}  - Model {i + 1}: {result['model']}, Response: {response_text}{bcolors.ENDC}")

    return MULTI_CONTEXT_HISTORY


def tool_AI_REASONING(user_input: str, goal: str = "", reasoning_methodology: str = "", additional_info: str = "") -> str:
    """
    Designs and executes a multi-model AI workflow based on user input.

    Args:
        user_input (str): The user's request or task.
        goal (str, optional): The desired outcome of the AI workflow. Defaults to "".
        reasoning_methodology (str, optional): The reasoning approach to use. Defaults to "".
        additional_info (str, optional): Any additional information relevant to the task. Defaults to "".

    Returns:
        str: The combined result of the AI workflow, including responses from each model.
    """
    #  Call model_dispacher_send_message to handle the workflow
    (
        text_response,
        models,
        labels,
        system_instructions,
        prompts,
        DataFlow,
    ) = model_dispacher_send_message(user_input + goal + reasoning_methodology + additional_info)

    # Execute the workflow if models are provided
    if models is not None:
        try:
            model_design_data = {  # Construct model_design_data for execute_modelium
                "chosenModels": models,
                "systemInstructions": system_instructions,
                "prompts": prompts,
                "DataFlow": DataFlow,
                "labels": labels
            }

            MULTI_CONTEXT_HISTORY = execute_modelium(model_design_data)  # Pass model_design_data

            # Combine the responses from the workflow into a single string
            result = ""
            for i, result_item in enumerate(MULTI_CONTEXT_HISTORY):
                result += f"{bcolors.OKGREEN}Step {i + 1}: {result_item['model']}{bcolors.ENDC}\n"
                # Corrected response extraction:
                response_text = result_item['response'].candidates[0].content.parts[0].text
                result += f"{bcolors.OKGREEN}  Response: {response_text}{bcolors.ENDC}\n\n"

            return result
        except Exception as e:
            print(f"{bcolors.FAIL}Error in execute_modelium: {e}{bcolors.ENDC}")
            return f"Error during execution: {e}"
    else:
        return text_response # Make sure text_response is returned even if models is None


def main():
    user_input = "Write a poem about a cat"
    result = tool_AI_REASONING(user_input, goal="to write a poem about a cat", reasoning_methodology="using poetic language", additional_info="make it rhyme")
    print(f"{bcolors.OKCYAN}{result}{bcolors.ENDC}")

if __name__ == "__main__":
    main()