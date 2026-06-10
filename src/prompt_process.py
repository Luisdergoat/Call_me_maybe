import json
import numpy as np

from src.token_validator import get_valid_tokens_for_json


def is_json_complete(text: str) -> bool:
    # checken ob alles in der JSON output ist
    try:
        json.loads(text)
        return True
    except Exception:
        return False


def process_prompt(prompt: str, functions_def: dict, llm_model) -> dict:

    # Wir erstellen ein System prompt
    functions_text = json.dumps(functions_def, indent=2)

    system_prompt = f"""You are a helpful function calling system.
Available functions:
{functions_text}

Given the user prompt, respond with ONLY a valid JSON object:
{{"name": "function_name", "parameters": {{...}}}}"""

    full_text = system_prompt + f"\n\nUser {prompt}\n\nResponse:"

    # Wir tokenisieren den Prompt
    encoded_input = llm_model.encode(full_text)
    token_ids = encoded_input[0].tolist()

    # Wir generieren Token-Für-Token
    generated_tokens = []
    max_tokens = 100

    # Laden des Vocabulars für die Token-Validierung
    vocab_path = llm_model.get_path_to_vocab_file()
    with open(vocab_path, 'r') as f:
        vocab = json.load(f)
    # Konvertieren zu {token_id: token_str} für schnelleren Zugriff
    id_to_token = {v: k for k, v in vocab.items()}

    for _ in range(max_tokens):
        # Logits holen
        current_ids = token_ids + generated_tokens
        logits = llm_model.get_logits_from_input_ids(current_ids)

        # Constraints anwenden
        # Nur gültige tokens nehmen
        valid_tokens = get_valid_tokens_for_json(functions_def, generated_tokens, id_to_token, llm_model)

        # Setye ungültige tokens auf -inf
        for token_id in range(len(logits)):
            if token_id not in valid_tokens:
                logits[token_id] = -float('inf')

        # Beste token auswählen
        next_token = int(np.argmax(logits))
        generated_tokens.append(next_token)

    # JSON Parsen
    json_text = llm_model.decode(generated_tokens)
    result = json.loads(json_text)

    return {
        "prompt": prompt,
        "name": result["name"],
        "parameters": result["parameters"]
    }
