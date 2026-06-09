import json
import llm_sdk

model = llm_sdk.Small_LLM_Model()

prompt = "What is 2 + 3?"
token_ids = model.encode(prompt)
logits = model.get_logits_from_input_ids(token_ids)

with open(model.get_path_to_vocabulary_json()) as f:
    vocabulary = json.load(f)

# Nächsten Token wählen
next_token_id = logits.index(max(logits))
next_token = vocabulary[str(next_token_id)]
print(f"Nächster Token: {next_token}")

# Mit Constraint
logits_copy = list(logits)
for token_id in [0, 1, 2]:
    logits_copy[token_id] = -float('inf')

next_token_id = logits_copy.index(max(logits_copy))
print(f"Mit Constraint: {vocabulary[str(next_token_id)]}")
