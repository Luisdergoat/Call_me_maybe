import os
import sys
import json

from llm_sdk import Small_LLM_Model
from src.io_utils import Input_reader
from src.prompt_process import process_prompt


def main():
    try:
        
        input_reader = Input_reader()
        input_reader.read_input_out()
        input_reader.check_available_functions()
        os.system("clear")
        sys.stdout.flush()

        llm_model = Small_LLM_Model()
        results = []
        prompts = input_reader.data
        functions_def = input_reader.available_functions

        for prompt_dict in prompts:
            prompt = prompt_dict["prompt"]
            print(f"Processing: {prompt}")
            print("\n")
            try:
                result = process_prompt(prompt, functions_def, llm_model)
                results.append(result)
            except Exception as e:
                print(f"Error processing prompt: {e}")

        output_file = "data/output/output.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)

        output_printed = "data/output/output.json"
        with open(output_printed, "r") as f:
            output_data = json.load(f)
            print(json.dumps(output_data, indent=2))

        print(f"\n✓ Saved {len(results)} results to {output_file}")

    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Exiting gracefully.")


if __name__ == "__main__":
    main()
