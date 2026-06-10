import json
import numpy as np


def load_vocab(llm_model):
    # wir laden das vobaluar aus der JSON Datei
    vocab_path = llm_model.get_path_to_vocab_file()

    with open(vocab_path, 'r') as f:
        vocab = json.load(f)

    # vocab ist ein Dict: "Token_string": token_id, ...
    # muss umgekehrt werden zu token_id: "Token_string"
    id_to_token = {v: k for k, v in vocab.items()}

    return id_to_token


def matches_available_functions(text, functions_def):
    # Check ob der Text zu einer Funktion passt
    try:
        # Suche nach namen
        if '"name"' in text:
            # Extrahiere was nach "name" kommt
            parts = text.split('"name"')
            if len(parts) > 1:
                after_name = parts[1]

                # Suche nach dem nächsten Anführungszeichen
                if '"' in after_name:
                    function_name_part = after_name.split('"')[1]

                    # Vergleiche mit verfügbaren Funktionen
                    available_names = [func['name'] for func in functions_def]
                    # Prefix check 
                    for name in available_names:
                        if name.startswith(function_name_part):
                            return True
                if function_name_part in available_names:
                    return True
    except Exception as e:
        print(f"Error checking function match: {e}")
        pass
    # Wenn wir nicht sicher sind lassen wir es weiter laufen
    return True


def is_valid_json_prefix(text):
    # Is der Text gültig für das JSOn format?

    # Wir entfernen alle Whitespaces am Ende
    text = text.strip()

    if not text:  # Leerer Text ist gültig
        return True

    # Wir zählen die Klammern
    open_braces = text.count("{")
    close_braces = text.count("}")
    open_brackets = text.count("[")
    close_brackets = text.count("]")
    open_quotes = text.count('"')

    # Alle schließenden Klammern müssen geöffnet sein
    if close_braces > open_braces or close_brackets > open_brackets:
        return False
    # Quotes müssen paarweise sein
    if open_quotes % 2 != 0:
        pass  # Es ist ok wenn wir noch im string sind

    # Versuche zu parsen, wenn es fehlt, ist es ein Prefix
    try:
        json.loads(text)
        return True  # Vollständig gültig
    except json.JSONDecodeError as e:
        # Es ist unvollständig, aber könnte ein gültiger Prefix sein
        if "Expecting" in str(e) or "EOF" in str(e):
            return True  # Gültiger Prefix
        return False  # Ungültig


def get_valid_tokens_for_json(
    functions_def, generated_tokens, id_to_token, llm_model
):
    # Wir müssen sicherstellen, das die Tokens erlaubt sind

    # Was haben wir bisher generiert?
    current_text = llm_model.decode(generated_tokens)
    valid_tokens = []

    # Wir gehen alle tokens im Vocabular durch
    for token_id, token_str in id_to_token.items():

        # Würde das Toknen in die JSON passen?
        candidate_text = current_text + token_str

        # Ist es noch Syntaktisch korrekt?
        if is_valid_json_prefix(candidate_text):
            # Stimmt es mit den verfügbaren Funktionen überein?
            if matches_available_functions(candidate_text, functions_def):
                valid_tokens.append(token_id)

    return valid_tokens
