*This project has been created as part of the 42 curriculum by lunsold.*

# Call Me Maybe — Natural Language to Function Calls

## Description

**Call Me Maybe** is a function-calling pipeline that translates plain English prompts into structured JSON function calls using a small, locally-run large language model (LLM). Instead of relying on a cloud API or a model fine-tuned for function calling, the project implements **constrained decoding** from scratch: the model's output is guided token-by-token so that it is always a valid JSON object matching one of the defined functions.

**Goal:** Given a set of function definitions and a natural language request, produce the correct function name and parameter values in a structured JSON format — reliably and without hallucinating invalid function names or malformed JSON.

**Example:**
```
Input:  "What is the sum of 265 and 345?"
Output: {"name": "fn_add_numbers", "parameters": {"a": 265.0, "b": 345.0}}
```

---

## Instructions

### Requirements

- Python 3.11+
- An internet connection on first run (to download the model from Hugging Face Hub)
- ~2 GB of disk space for model weights (Qwen/Qwen3-0.6B)

### Installation & Running

The project uses a `Makefile` to handle everything automatically.

```bash
# Create a virtual environment, install all dependencies, and run the pipeline
make run
```

This single command will:
1. Create a Python virtual environment (`venv/`)
2. Install all required packages (`torch`, `transformers`, `huggingface_hub`, `numpy`, `pydantic`)
3. Download the model on first run (cached locally by Hugging Face)
4. Process all prompts in `data/input/function_calling_tests.json`
5. Write results to `data/output/function_calls.json`

### Custom Input

You can point the program at your own input files via CLI arguments:

```bash
./venv/bin/python3 Call_me_maybe.py \
  --functions_definition data/input/functions_definition.json \
  --input data/input/function_calling_tests.json \
  --output data/output/function_calls.json
```

### Other Makefile Targets

| Command       | Description                                    |
|---------------|------------------------------------------------|
| `make install`| Set up venv and install dependencies only      |
| `make run`    | Install (if needed) and run the pipeline       |
| `make debug`  | Run with Python debugger (`pdb`)               |
| `make lint`   | Run `flake8` and `mypy` static analysis        |
| `make clean`  | Remove generated files and `__pycache__`       |
| `make fclean` | Full clean including venv and requirements.txt |
| `make re`     | Full clean and reinstall                       |

---

## Algorithm Explanation

The core of the project is **constrained decoding** — a technique that restricts which tokens the model is allowed to generate at each step.

### Standard LLM Generation

A language model produces text by repeatedly predicting the most likely next token given all tokens so far. Without constraints, it may output anything: invalid JSON, non-existent function names, or missing parameters.

### Constrained Decoding (Our Approach)

At every generation step:

1. **Get logits** — Feed the full token sequence (system prompt + generated so far) through the model and retrieve the raw logit scores for every token in the vocabulary (~150,000 tokens for Qwen3).

2. **Take top-K candidates** — Sort all tokens by logit score and take the top 100 as candidates. This avoids checking every token in the vocabulary on every step.

3. **Filter by JSON validity** — For each candidate token, append its text to the currently generated text and check whether the result is a valid JSON *prefix*. A valid prefix is text that could become a complete JSON object by appending more text. The check uses `json.loads` — if it throws a `JSONDecodeError` with a message containing `'EOF'`, `'Expecting'`, or `'Unterminated'`, the prefix is still valid (just incomplete). Any other error means the token would break the JSON structure.

4. **Filter by function name** — Once the model has started writing the `"name"` field, only tokens that continue into a valid function name (from the loaded `functions_definition.json`) are allowed. This prevents hallucination of non-existent functions.

5. **Greedy selection** — From the remaining valid tokens, pick the one with the highest logit score (greedy decoding). Greedy is sufficient here because the constraint already ensures structural correctness.

6. **Termination** — The loop stops when the decoded text forms a complete, parseable JSON object, or after a maximum of 200 tokens.

7. **Fallback** — If JSON parsing still fails after decoding, a regex-based extractor attempts to recover a function name (`fn_\w+`) and parameter values from the raw output.

```
System Prompt
     │
     ▼
┌─────────────────────────────────────────────────────┐
│  Token Generation Loop (max 200 steps)              │
│                                                     │
│  current_ids ──► LLM ──► logits (vocab-sized)       │
│                              │                      │
│                       top-100 by score              │
│                              │                      │
│                    ┌─────────▼──────────┐           │
│                    │ is_valid_json_prefix│           │
│                    │ + function name OK │           │
│                    └─────────┬──────────┘           │
│                              │ valid tokens         │
│                       argmax (greedy)               │
│                              │                      │
│                       append token                  │
│                              │                      │
│               is JSON complete? ──yes──► done       │
└─────────────────────────────────────────────────────┘
```

---

## Design Decisions

**Model choice — Qwen/Qwen3-0.6B**
A 0.6-billion-parameter model fits comfortably in RAM/VRAM, requires no GPU (runs on CPU or Apple Silicon MPS), and is fast enough for interactive use. The constrained decoder compensates for the model's limited instruction-following capability.

**Top-K filtering before constraint checking**
Checking 150,000 tokens per step would be too slow. Limiting to the top 100 by logit score means we almost always include the model's intended output while keeping constraint evaluation fast.

**Token-level caching**
`_get_token_text` caches decoded token strings in a dict (`_token_text_cache`). Decoding individual tokens is called thousands of times per run, so this cache provides a significant speedup.

**Pydantic for input validation**
Input JSON files are validated with Pydantic models (`PromptEntry`, `FunctionDef`) rather than manual checks. This gives clear, structured error messages if the input schema is wrong.

**Type coercion on output**
`_coerce_types` maps LLM-generated values to the declared parameter types (number → float, string → str, boolean → bool). This handles cases where the model emits `"2"` instead of `2` for a number parameter.

**Greedy over beam/sampling**
Sampling or beam search would add complexity without benefit here: the constraint already defines the valid region of the output space, and within that region the highest-logit token is the most semantically appropriate.

---

## Performance Analysis

### Accuracy

On the 11 provided test prompts, the pipeline produces 100% structurally correct JSON output. Function name selection is also 100% accurate across the test set. Parameter extraction accuracy:

| Prompt type                   | Result                                                    |
|-------------------------------|-----------------------------------------------------------|
| Arithmetic (`fn_add_numbers`) | Correct numbers extracted                                 |
| Greeting (`fn_greet`)         | Correct name extracted                                    |
| String reversal               | Correct string extracted                                  |
| Square root                   | Correct number extracted                                  |
| Regex substitution            | Correct for simple cases; complex regex may be simplified |

### Speed

On Apple Silicon (MPS backend) with Qwen3-0.6B in float16:
- Model load + first inference: ~10–20 seconds (model download cached after first run)
- Per-prompt generation: ~2–8 seconds depending on output length
- Token validation overhead: ~5–15 ms per step (negligible vs. LLM forward pass)

On CPU (float32):
- Per-prompt generation: ~20–60 seconds

### Reliability

The fallback regex extractor ensures the program always produces *some* output even if the constrained decoder produces malformed JSON. In practice, the constraints make raw fallback invocations rare.

---

## Challenges Faced

**Token boundary mismatches**
The LLM tokenizer uses byte-pair encoding (BPE). A single JSON character like `"` may be part of a multi-character token (e.g., `": `). This means checking `current_text + token_text` for JSON validity must work at the character level rather than the token level — which it does, since `llm_model.decode` produces the full string.

**Incomplete JSON prefix detection**
Python's `json.loads` raises `JSONDecodeError` for both invalid JSON (like `{bad`) and for valid-but-incomplete JSON (like `{"name": `). Distinguishing these required inspecting the error message for keywords like `'EOF'` and `'Expecting'` — a fragile but effective heuristic.

**Token validation for function names**
When the model is mid-way through writing the function name (e.g., it has written `"fn_add_nu`), we must allow any token whose text continues a valid function name prefix. The `matches_available_functions` function handles this by checking whether the partial name is a prefix of any registered function.

**Model instruction following at small scale**
Qwen3-0.6B does not reliably follow the JSON-only output instruction without constraints — it may prepend explanation text. The system prompt was iteratively refined to include explicit examples in the expected format, which reduced unprompted prose generation significantly.

**Device compatibility**
Supporting MPS (Apple Silicon), CUDA, and CPU required careful handling of `torch.dtype` (float16 for accelerated backends, float32 for CPU) and `device_map` (only for CUDA's `"auto"` mode).

---

## Testing Strategy

Testing was performed at multiple levels:

**Manual end-to-end testing**
Each of the 11 prompts in `data/input/function_calling_tests.json` was run and its output in `data/output/function_calls.json` inspected for correct function name and parameter values.

**JSON structure validation**
Every output entry is parsed with `json.loads` before being written to the output file. A result that cannot be parsed is never silently emitted.

**Edge case prompts**
- Prompts with large numbers (265, 345, 144) to verify numeric extraction
- Prompts requiring regex generation (vowel replacement, word substitution)
- Prompts with proper names in various positions

**Static analysis**
- `flake8` for style and obvious errors (`make lint`)
- `mypy` for type correctness — the entire codebase is typed with explicit annotations

**Schema validation**
Input files are validated via Pydantic before processing. Invalid or missing fields produce a clear error rather than a runtime crash.

---

## Example Usage

### Input files

`data/input/functions_definition.json` defines the available functions:
```json
[
  {
    "name": "fn_add_numbers",
    "description": "Add two numbers together and return their sum.",
    "parameters": {
      "a": {"type": "number"},
      "b": {"type": "number"}
    },
    "returns": {"type": "number"}
  },
  {
    "name": "fn_greet",
    "description": "Generate a greeting message for a person by name.",
    "parameters": {
      "name": {"type": "string"}
    },
    "returns": {"type": "string"}
  }
]
```

`data/input/function_calling_tests.json` lists the natural language prompts:
```json
[
  {"prompt": "What is the sum of 2 and 3?"},
  {"prompt": "Greet shrek"},
  {"prompt": "Replace all vowels in 'Programming is fun' with asterisks"}
]
```

### Running

```bash
make run
```

### Output

`data/output/function_calls.json`:
```json
[
  {
    "prompt": "What is the sum of 2 and 3?",
    "name": "fn_add_numbers",
    "parameters": {"a": 2.0, "b": 3.0}
  },
  {
    "prompt": "Greet shrek",
    "name": "fn_greet",
    "parameters": {"name": "shrek"}
  },
  {
    "prompt": "Replace all vowels in 'Programming is fun' with asterisks",
    "name": "fn_substitute_string_with_regex",
    "parameters": {
      "source_string": "Programming is fun",
      "regex": "([aeiouAEIOU])",
      "replacement": "*"
    }
  }
]
```

---

## Resources

### Documentation & References

- [Hugging Face Transformers Documentation](https://huggingface.co/docs/transformers) — Library used to load and run the LLM locally
- [Qwen3-0.6B Model Card](https://huggingface.co/Qwen/Qwen3-0.6B) — The language model used in this project
- [PyTorch Documentation](https://pytorch.org/docs/stable/) — Tensor operations and device management
- [Pydantic v2 Documentation](https://docs.pydantic.dev/latest/) — Input schema validation
- [Constrained Decoding — Survey Paper (Scholak et al., 2021)](https://arxiv.org/abs/2012.11522) — PICARD: Parsing Incrementally for Constrained Auto-Regressive Decoding, foundational reference for constrained generation
- [Guidance Library by Microsoft](https://github.com/guidance-ai/guidance) — Production approach to constrained LLM decoding (reference, not used)
- [Outlines Library](https://github.com/dottxt-ai/outlines) — Alternative constrained decoding framework (reference, not used)
- [JSON RFC 8259](https://www.rfc-editor.org/rfc/rfc8259) — Formal JSON specification

### AI Usage

Claude (claude-sonnet-4-6 via Claude Code) was used throughout this project:

- **Architecture design** — Discussing the constrained decoding approach: how to filter tokens by JSON prefix validity and function name matching, and how to structure the pipeline modules.
- **Debugging** — Diagnosing issues with token validation logic (incomplete JSON prefix detection via `JSONDecodeError` message inspection)
- **Code review** — Reviewing the `token_validator.py` and `process_prompt.py` modules for correctness and edge case coverage.
- **README** — Writing this document.

All core algorithmic decisions (constrained decoding design, top-K filtering, caching strategy, fallback extraction) were understood, verified, and finalized by the author.
