from pydantic import BaseModel
from typing import List, Dict, Any
from io_utils import Input_reader

import json
import re
import os


class Prompt(BaseModel):
    prompt: str


class FunctionCall(BaseModel):
    function_name: str
    arguments: list[int]
    prompt: Prompt


def __check_for_function(prompt):
    print(f"Checking prompt: {prompt}")
    if "sum" in prompt:
        print("Function 'fn_add_numbers' found in the prompt.")
        return "fn_add_numbers"
    print("No function found in the prompt.")


def __make_prompt_to_string(prompt):
    prompt_string = ""
    for key, value in prompt.items():
        prompt_string = f"{prompt_string} {value}"
        print(f"Current prompt string: {prompt_string}")
    return prompt_string


def read_arguments_from_prompt(prompt):
    if __check_for_function(prompt) == "fn_add_numbers":
        numbers = re.findall(r'\d+', prompt)
        numbers = list(map(int, numbers))
        result = numbers
        return result
    print("No function found in the prompt.")



if __name__ == "__main__":

    input_reader = Input_reader()
    input_reader.read_input_out()
    os.system("clear")
    print(input_reader.data[0])
    input_reader.check_available_functions()
    print()
    print(input_reader.available_functions[0])
    print()
    prompt = input_reader.data[0]
    prompt = __make_prompt_to_string(prompt)
    try:
        call = FunctionCall(
            function_name=__check_for_function(prompt),
            arguments=read_arguments_from_prompt(prompt),
            prompt=Prompt(prompt=prompt)
        )
    except Exception as e:
        print(f"Error creating FunctionCall: {e}")
