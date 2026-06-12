"""Constrained decoding utilities for JSON function call generation."""
import json
from typing import Dict, List

import numpy as np

_token_text_cache: Dict[int, str] = {}


def _get_token_text(token_id: int, llm_model) -> str:
    """Decode a single token to its string representation, with caching."""
    if token_id not in _token_text_cache:
        _token_text_cache[token_id] = llm_model.decode([token_id])
    return _token_text_cache[token_id]


def is_valid_json_prefix(text: str) -> bool:
    """Return True if text could be a valid prefix of a JSON object."""
    text = text.strip()
    if not text:
        return True
    if not text.startswith('{'):
        return False
    if text.count('}') > text.count('{'):
        return False
    try:
        json.loads(text)
        return True
    except json.JSONDecodeError as e:
        msg = str(e)
        if 'EOF' in msg or 'Expecting' in msg or 'Unterminated' in msg:
            return True
        return False


def matches_available_functions(text: str, functions_def: List[dict]) -> bool:

    if '"name"' not in text:
        return True
    available_names = [f['name'] for f in functions_def]
    try:
        idx = text.find('"name"')
        after = text[idx + 6:].lstrip(' \t\n:')
        if not after or after[0] != '"':
            return True
        after = after[1:]
        if not after:
            return True
        if '"' in after:
            name_val = after[:after.index('"')]
            return name_val in available_names
        for name in available_names:
            if name.startswith(after):
                return True
        return False
    except Exception:
        return True


def get_valid_tokens_for_json(
    functions_def: List[dict],
    generated_tokens: List[int],
    id_to_token: dict,
    llm_model,
    logits: List[float],
    top_k: int = 100
) -> List[int]:

    current_text = llm_model.decode(
        generated_tokens
        ) if generated_tokens else ""
    logits_arr = np.array(logits)
    top_k_ids = np.argsort(logits_arr)[-top_k:].tolist()

    valid_tokens: List[int] = []
    for token_id in top_k_ids:
        token_id = int(token_id)
        token_text = _get_token_text(token_id, llm_model)
        if not token_text:
            continue
        candidate_text = current_text + token_text
        if (is_valid_json_prefix(candidate_text)
                and matches_available_functions(
                    candidate_text, functions_def
                    )):
            valid_tokens.append(token_id)

    return valid_tokens if valid_tokens else [int(top_k_ids[-1])]


def load_vocab(llm_model) -> Dict[int, str]:
    """Load vocabulary from model and return id→token mapping."""
    vocab_path = llm_model.get_path_to_vocab_file()
    with open(vocab_path, 'r') as f:
        vocab = json.load(f)
    return {v: k for k, v in vocab.items()}
