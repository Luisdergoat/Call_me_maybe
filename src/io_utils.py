from pathlib import Path
import numpy as np
import pydantic as pd
import sys
import os
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

        except FileNotFoundError:
            print("File not found")
        except json.JSONDecodeError:
            print("Invalid JSON format")


if __name__ == "__main__":
    input_reader = Input_reader()
    input_reader.read_input_out()
