"""Input/output utilities for reading function definitions and test prompts."""
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from pydantic import BaseModel, ValidationError


class PromptEntry(BaseModel):
    """A single natural language prompt to process."""

    prompt: str


class ParameterDef(BaseModel):
    """Type definition for a function parameter."""

    type: str


class FunctionDef(BaseModel):
    """Definition of a callable function."""

    name: str
    description: str
    parameters: Dict[str, ParameterDef]
    returns: ParameterDef


class Input_reader:
    """Read and validate input files for the function calling pipeline."""

    def __init__(self) -> None:
        """Initialize with empty data."""
        self.data: List[Dict[str, Any]] = []
        self.available_functions: List[Dict[str, Any]] = []

    def read_input(self, file_path: str) -> None:
        """Read prompt test cases from a JSON file."""
        try:
            with open(file_path, 'r') as f:
                raw = json.load(f)
            validated = [PromptEntry(**entry).model_dump() for entry in raw]
            self.data = validated
        except FileNotFoundError:
            print(f"Error: Input file not found: {file_path}", file=sys.stderr)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in input file: {e}", file=sys.stderr)
        except ValidationError as e:
            print(f"Error: Input file schema invalid: {e}", file=sys.stderr)

    def read_functions(self, file_path: str) -> None:
        """Read function definitions from a JSON file."""
        try:
            with open(file_path, 'r') as f:
                raw = json.load(f)
            validated = [FunctionDef(**entry).model_dump() for entry in raw]
            self.available_functions = validated
        except FileNotFoundError:
            print(f"Error: Functions file not found: {file_path}", file=sys.stderr)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in functions file: {e}", file=sys.stderr)
        except ValidationError as e:
            print(f"Error: Functions file schema invalid: {e}", file=sys.stderr)

    def read_input_out(self) -> None:
        """Read prompts from the default input path."""
        default = Path(__file__).parent / "../data/input/function_calling_tests.json"
        self.read_input(str(default))

    def check_available_functions(self) -> None:
        """Read function definitions from the default path."""
        default = Path(__file__).parent / "../data/input/functions_definition.json"
        self.read_functions(str(default))
