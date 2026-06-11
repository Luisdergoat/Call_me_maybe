"""Main entry point for the function calling pipeline."""
import argparse
import json
import os
import sys

from llm_sdk import Small_LLM_Model
from src.io_utils import Input_reader
from src.process_prompt import process_prompt
from src.token_validator import load_vocab


def main() -> None:
    """Run the function calling pipeline."""
    os.system("clear")
    print("=== Call Me Maybe: Natural Language to Function Calls ===\n")
    print("Processing prompts and generating function calls...\n")
    parser = argparse.ArgumentParser(
        description="Translate natural language prompts into structured function calls."
    )
    parser.add_argument(
        "--functions_definition",
        default="data/input/functions_definition.json",
        help="Path to function definitions JSON file",
    )
    parser.add_argument(
        "--input",
        default="data/input/function_calling_tests.json",
        help="Path to input prompts JSON file",
    )
    parser.add_argument(
        "--output",
        default="data/output/function_calls.json",
        help="Path to output JSON file",
    )
    args = parser.parse_args()

    try:
        reader = Input_reader()
        reader.read_input(args.input)
        reader.read_functions(args.functions_definition)

        prompts = reader.data
        functions_def = reader.available_functions

        if not prompts:
            print("Error: No prompts loaded.", file=sys.stderr)
            sys.exit(1)
        if not functions_def:
            print("Error: No function definitions loaded.", file=sys.stderr)
            sys.exit(1)

        llm_model = Small_LLM_Model()
        id_to_token = load_vocab(llm_model)

        results = []
        for entry in prompts:
            print("loading...")
            prompt = entry.get("prompt", "")
            if not prompt:
                continue

            try:
                result = process_prompt(prompt, functions_def, llm_model, id_to_token)
                if result:
                    results.append(result)
            except Exception as e:
                print(f"Error processing prompt '{prompt}': {e}", file=sys.stderr)

        out_dir = os.path.dirname(args.output)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)

        print(json.dumps(results, indent=2))
        print(f"\nSaved {len(results)} results to {args.output}")

    except KeyboardInterrupt:
        print("\nInterrupted by user.")


if __name__ == "__main__":
    main()
