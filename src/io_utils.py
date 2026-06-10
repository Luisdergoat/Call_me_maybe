from pathlib import Path
import json


class Input_reader:
    def __init__(self):
        pass

    def read_input_out(self):

        file_path = Path(__file__).parent / "../data/input/function_calling_tests.json"
        try:
            with open(file_path, 'r') as calling_json:
                data = json.load(calling_json)
            print(data)
            self.data = data

        except FileNotFoundError:
            print("File not found")
        except json.JSONDecodeError:
            print("Invalid JSON format")

    def check_available_functions(self):

        file_path = Path(__file__).parent / "../data/input/functions_definition.json"
        try:
            with open(file_path, 'r') as calling_json:
                available_functions = json.load(calling_json)
            print(available_functions)
            self.available_functions = available_functions

        except FileNotFoundError:
            print("File not found")
        except json.JSONDecodeError:
            print("Invalid JSON format")
