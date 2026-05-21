VENV ?= .venv

.PHONY: install run debug clean lint

install:
	uv venv $(VENV)
	$(VENV)/bin/uv pip install -r requirements.txt || $(VENV)/bin/uv pip install .

run:
	$(VENV)/bin/uv run python3 -m src

debug:
	$(VENV)/bin/uv run python3 -m pdb -m src

clean:
	rm -rf __pycache__ .mypy_cache *.pyc

lint:
	$(VENV)/bin/uv run flake8
	$(VENV)/bin/uv run mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
