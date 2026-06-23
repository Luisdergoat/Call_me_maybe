"""Process a natural language prompt into a structured function call."""
import json
import re
from typing import Any, Dict, List, Optional

import numpy as np

from src.token_validator import get_valid_tokens_for_json


def is_json_complete(text: str) -> bool:
    """Return True if text is a complete, parseable JSON object."""
    text = text.strip()
    if not text.startswith('{') or not text.endswith('}'):
        return False
    try:
        json.loads(text)
        return True
    except json.JSONDecodeError:
        return False


def extract_json(text: str) -> Optional[str]:
    """Extract the first complete JSON object from text."""
    start = text.find('{')
    if start == -1:
        return None
    depth = 0
    in_string = False
    escape_next = False
    for i, ch in enumerate(text[start:], start):
        if escape_next:
            escape_next = False
            continue
        if ch == '\\' and in_string:
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
        if not in_string:
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
    return None


def _build_system_prompt(prompt: str, functions_def: List[dict]) -> str:
    """Build a structured prompt for function calling."""
    functions_text = json.dumps(functions_def, indent=2)
    examples: List[str] = []
    for func in functions_def:
        ex_params: Dict[str, Any] = {}
        for pname, pinfo in func['parameters'].items():
            ptype = pinfo.get('type', 'string')
            if ptype == 'number':
                ex_params[pname] = 1.0
            elif ptype == 'boolean':
                ex_params[pname] = True
            else:
                ex_params[pname] = "example"
        examples.append(json.dumps(
            {"name": func['name'], "parameters": ex_params}
            ))
    examples_text = "\n".join(examples)
    return (
        "You are a function calling system."
        "Extract the function name and parameter "
        "values directly from the user request."
        "Output ONLY raw JSON, no markdown, "
        "no explanation.\n\n"
        f"Available functions:\n{functions_text}\n\n"
        "Rules:\n"
        "- 'name': exact function name from the list above\n"
        "- 'parameters': values extracted from the user request\n"
        "- For string params: copy the EXACT text from the request\n"
        "- For file paths: copy the COMPLETE path including all "
        "slashes and filename (e.g. /home/user/data.json)\n"
        "- For template strings: copy the ENTIRE template verbatim; "
        "escape any embedded double quotes as \\\\\"\n"
        "- For number params: use the exact number from the request\n"
        "- For regex params: "
        "write a valid regex pattern that matches the description\n\n"
        f"Example format:\n{examples_text}\n\n"
        f"User request: {prompt}\n"
        "JSON:"
    )


_NUMERIC_TYPES = {'number', 'integer', 'float', 'int'}


def _coerce_types(
    parameters: Dict[str, Any],
    func_def: Dict[str, Any]
) -> Dict[str, Any]:

    result: Dict[str, Any] = {}
    for pname, pinfo in func_def['parameters'].items():
        ptype = pinfo.get('type', 'string')
        val = parameters.get(pname)
        if val is None:
            result[pname] = 0.0 if ptype in _NUMERIC_TYPES else ""
        elif ptype in _NUMERIC_TYPES:
            try:
                result[pname] = float(val)
            except (TypeError, ValueError):
                result[pname] = 0.0
        elif ptype == 'boolean':
            result[pname] = bool(val)
        else:
            result[pname] = str(val)
    return result


def _looks_like_path(val: str) -> bool:
    return bool(val) and (val.startswith('/') or (len(val) > 1 and val[1] == ':'))


def _fix_string_params(
    prompt: str,
    parameters: Dict[str, Any],
    func_def: Dict[str, Any]
) -> Dict[str, Any]:
    """Patch parameters that the LLM extracted incorrectly from the prompt."""
    result = dict(parameters)
    for pname, pinfo in func_def['parameters'].items():
        if pinfo.get('type', 'string') != 'string':
            continue
        val = str(result.get(pname, ''))

        if 'path' in pname.lower() or 'file' in pname.lower():
            if not _looks_like_path(val):
                m = re.search(r'([A-Za-z]:\\[^\s,]+|/[^\s,]+)', prompt)
                if m:
                    result[pname] = m.group(0)

        if 'template' in pname.lower():
            m = re.search(
                r'[Tt]emplate\s*:\s*(.+)$', prompt, re.DOTALL
            )
            if m:
                extracted = m.group(1).strip()
                if len(extracted) > len(val):
                    result[pname] = extracted

    return result


def _fallback_extraction(
    prompt: str,
    text: str,
    functions_def: List[dict]
) -> Optional[Dict[str, Any]]:

    name_match = re.search(r'fn_\w+', text)
    if not name_match:
        return None
    name = name_match.group(0)
    func_def = next((f for f in functions_def if f['name'] == name), None)
    if not func_def:
        return None
    numbers = re.findall(r'-?\d+\.?\d*', text)
    strings = re.findall(r"['\"]([^'\"]{1,500})['\"]", text)
    parameters: Dict[str, Any] = {}
    num_idx = str_idx = 0
    for pname, pinfo in func_def['parameters'].items():
        ptype = pinfo.get('type', 'string')
        if ptype in _NUMERIC_TYPES and num_idx < len(numbers):
            parameters[pname] = float(numbers[num_idx])
            num_idx += 1
        elif ptype == 'string' and str_idx < len(strings):
            parameters[pname] = strings[str_idx]
            str_idx += 1
        else:
            parameters[pname] = 0.0 if ptype in _NUMERIC_TYPES else ""
    return {"prompt": prompt, "name": name, "parameters": parameters}


def process_prompt(
    prompt: str,
    functions_def: List[dict],
    llm_model,
    id_to_token: dict
) -> Optional[Dict[str, Any]]:
    """Translate a natural language prompt into a structured function call.

    Uses constrained decoding to guarantee valid JSON output matching the
    available function definitions.
    """
    system_prompt = _build_system_prompt(prompt, functions_def)
    encoded = llm_model.encode(system_prompt)
    input_ids: List[int] = encoded[0].tolist()

    generated_tokens: List[int] = []
    max_tokens = 200

    for _ in range(max_tokens):
        current_ids = input_ids + generated_tokens
        logits = llm_model.get_logits_from_input_ids(current_ids)

        valid_tokens = get_valid_tokens_for_json(
            functions_def, generated_tokens, id_to_token, llm_model, logits
        )

        logits_arr = np.array(logits)
        mask = np.full(len(logits), -np.inf)
        for tid in valid_tokens:
            mask[tid] = logits_arr[tid]

        next_token = int(np.argmax(mask))
        generated_tokens.append(next_token)

        if is_json_complete(llm_model.decode(generated_tokens)):
            break

    raw_text = llm_model.decode(generated_tokens)

    json_str = extract_json(raw_text)
    if json_str:
        try:
            result = json.loads(json_str)
            name = result.get("name", "")
            func_def = next(
                (f for f in functions_def if f['name'] == name), None
                )
            if func_def:
                coerced = _coerce_types(
                    result.get("parameters", {}), func_def
                )
                return {
                    "prompt": prompt,
                    "name": name,
                    "parameters": _fix_string_params(
                        prompt, coerced, func_def
                    )
                }
        except (json.JSONDecodeError, KeyError):
            pass

    print("JSON parse failed, trying regex fallback...")
    fallback = _fallback_extraction(prompt, raw_text, functions_def)
    if fallback:
        func_def = next(
            (f for f in functions_def if f['name'] == fallback['name']), None
        )
        if func_def:
            fallback['parameters'] = _fix_string_params(
                prompt, fallback['parameters'], func_def
            )
    return fallback
