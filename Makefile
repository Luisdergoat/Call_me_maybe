.PHONY: install run debug clean lint lint-strict

MAIN_MODULE ?= src
ARGS ?=

# install: Installiert Python-Abhängigkeiten mit uv über pyproject.toml oder requirements.txt.
install:
	@if [ -f pyproject.toml ]; then \
		uv sync; \
	elif [ -f requirements.txt ]; then \
		uv pip install -r requirements.txt; \
	else \
		echo "Fehler: Weder pyproject.toml noch requirements.txt gefunden." >&2; \
		exit 1; \
	fi

# run: Führt die Hauptapplikation aus dem src-Modul mit optionalen Parametern aus.
run:
	@if [ ! -d src ]; then \
		echo "Fehler: Das Verzeichnis 'src' wurde nicht gefunden." >&2; \
		exit 1; \
	fi
	uv run python -m $(MAIN_MODULE) $(ARGS)

# debug: Startet die Hauptapplikation im Debugmodus mit pdb.
debug:
	@if [ ! -d src ]; then \
		echo "Fehler: Das Verzeichnis 'src' wurde nicht gefunden." >&2; \
		exit 1; \
	fi
	uv run python -m pdb -m $(MAIN_MODULE) $(ARGS)

# clean: Entfernt Python-Caches und temporäre Dateien aus dem Projekt.
clean:
	find . -type d \( -name "__pycache__" -o -name ".mypy_cache" -o -name ".pytest_cache" \) -prune -exec rm -rf {} +
	find . -type f \( -name "*.pyc" -o -name "*.pyo" -o -name "*.pyd" \) -delete

# lint: Führt flake8 und mypy mit den geforderten Prüfoptionen aus.
lint:
	uv run flake8 .
	uv run mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

# lint-strict: Führt flake8 und mypy im strikten Modus aus.
lint-strict:
	uv run flake8 .
	uv run mypy . --strict
