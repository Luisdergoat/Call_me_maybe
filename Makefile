# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    Makefile                                           :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: luisunsold <luisunsold@student.42.fr>      +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2026/02/10 00:00:00 by luunsold          #+#    #+#              #
#    Updated: 2026/06/12 09:50:46 by luisunsold       ###   ########.fr        #
#                                                                              #
# **************************************************************************** #

# ================================ COLORS ================================== #
RED		= \033[0;31m
GREEN	= \033[0;32m
YELLOW	= \033[0;33m
BLUE	= \033[0;34m
RESET	= \033[0m

# ================================ VARIABLES =============================== #
VENV		= venv
PYTHON		= $(VENV)/bin/python3
DEBUG_MODE	= $(VENV)/bin/python3 -m pdb
PIP			= $(VENV)/bin/pip
ACTIVATE	= source $(VENV)/bin/activate

lint1		= flake8 .
lint2		= mypy .
SRC_DIR		= src
OUTPUT		= output.json

# Python files
MAIN		= Call_me_maybe.py

# ================================ TARGETS ================================= #

all: install
# Need the config as arg as well
# Install dependencies in virtual environment
install: $(VENV)/bin/activate requirements.txt
	@echo "$(BLUE)📦 Installing dependencies...$(RESET)"
	@$(PIP) install --upgrade pip
	@$(PIP) install -r requirements.txt
	@echo "$(GREEN)✅ Dependencies installed successfully!$(RESET)"
	@echo "$(YELLOW)💡 Virtual environment created at: $(VENV)$(RESET)"
	@echo "$(BLUE)📝 Start the programm with make run"

# Create virtual environment
$(VENV)/bin/activate:
	@echo "$(BLUE)🔧 Creating virtual environment...$(RESET)"
	@python3 -m venv $(VENV)
	@echo "$(GREEN)✅ Virtual environment created!$(RESET)"

# Create requirements.txt if it doesn't exist
requirements.txt:
	@echo "$(BLUE)📝 Creating requirements.txt...$(RESET)"
	@echo "numpy>=2.2.6\npydantic>=2.10.0\ntorch>=2.0.0\ntransformers>=4.30.0\nhuggingface_hub>=0.19.0\nflake8>=4.0.0\nmypy>=0.900" > requirements.txt
	@echo "$(GREEN)✅ requirements.txt created!$(RESET)"
	@echo "$(GREEN)✅ Dependencies installed successfully!$(RESET)"

# Run maze generation
run: install
	@echo "$(BLUE)🎮 Running llm ...$(RESET)"
	@PYTHONPATH=$(SRC_DIR) $(PYTHON) $(MAIN)

debug: install
	@echo "$(BLUE)🐞 Running in debug mode...$(RESET)"
	$(DEBUG_MODE) $(MAIN) $(ARGS)
	@echo "$(GREEN)✅ Debugging session ended!$(RESET)"

# Clean generated files
clean:
	@echo "$(YELLOW)🧹 Cleaning generated files...$(RESET)"
	@rm -f $(OUTPUT)
	@rm -rf __pycache__
	@rm -rf $(SRC_DIR)/__pycache__
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@echo "$(GREEN)✅ Cleaned!$(RESET)"

# Clean everything including venv
fclean: clean
	@echo "$(RED)🗑️  Removing virtual environment...$(RESET)"
	@rm -rf $(VENV)
	@rm -f requirements.txt
	@echo "$(GREEN)✅ Full clean complete!$(RESET)"
 
# Reinstall everything
re: fclean all

# check the code with flake8 and mypy
lint: fclean
	@echo "$(BLUE)🔍 Running linters...$(RESET)"
	@$(lint1)
	@$(lint2)
	@echo "$(GREEN)✅ Linting complete!$(RESET)"

# Show help
help:
	@echo "$(BLUE)╔══════════════════════════════════════════════════════════╗$(RESET)"
	@echo "$(BLUE)║               Call_me_maybe  -  Makefile Commands        ║$(RESET)"
	@echo "$(BLUE)╚══════════════════════════════════════════════════════════╝$(RESET)"
	@echo ""
	@echo "$(GREEN)Installation:$(RESET)"
	@echo "  make install    - Create venv and install dependencies"
	@echo ""
	@echo "$(GREEN)Running:$(RESET)"
	@echo "  make run        - let the llm work"
	@echo ""
	@echo "$(GREEN)Cleaning:$(RESET)"
	@echo "  make clean      - Remove generated files"
	@echo "  make fclean     - Remove venv and all generated files"
	@echo "  make re         - Full reinstall"
	@echo ""

%:
	@true

.PHONY: all install run clean fclean re help activate
