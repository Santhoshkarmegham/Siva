SHELL := /bin/sh

PYTHON ?= python3
VENV ?= .venv
VENV_PYTHON := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip
STREAMLIT := $(VENV)/bin/streamlit

PROJECT_DIRS := \
	data/raw \
	data/processed \
	src/brand_visibility \
	src/brand_visibility/analytics \
	src/brand_visibility/dashboard \
	src/brand_visibility/data \
	tests

.DEFAULT_GOAL := help

.PHONY: help scaffold venv install setup demo pipeline run check tree clean clean-data reset-data

help:
	@echo "Brand Visibility Intelligence - available commands"
	@echo ""
	@echo "  make scaffold              Create the complete folder/package scaffold"
	@echo "  make setup                 Create scaffold, virtual environment, and install"
	@echo "  make demo                  Generate demo CSV, SQLite DB, and EDA report"
	@echo "  make pipeline CSV=path     Process a real CSV dataset"
	@echo "  make run                   Launch the Streamlit dashboard"
	@echo "  make check                 Compile source and test the data pipeline"
	@echo "  make tree                  Display the project structure"
	@echo "  make clean                 Remove Python caches and build artifacts"
	@echo "  make clean-data            Remove generated processed data"

# mkdir -p and touch are idempotent: existing folders and files are preserved.
scaffold:
	@mkdir -p $(PROJECT_DIRS)
	@touch data/raw/.gitkeep
	@touch data/processed/.gitkeep
	@touch src/brand_visibility/__init__.py
	@touch src/brand_visibility/analytics/__init__.py
	@touch src/brand_visibility/dashboard/__init__.py
	@touch src/brand_visibility/data/__init__.py
	@touch tests/__init__.py
	@echo "Project scaffold is ready."

venv:
	@test -x "$(VENV_PYTHON)" || $(PYTHON) -m venv "$(VENV)"
	@echo "Virtual environment is ready at $(VENV)."

install: venv
	@$(VENV_PIP) install --upgrade pip
	@$(VENV_PIP) install -e .

setup: scaffold install
	@echo "Setup complete. Run 'make demo' and then 'make run'."

demo: scaffold
	@$(VENV_PYTHON) -m brand_visibility.pipeline --demo

pipeline: scaffold
	@test -n "$(CSV)" || (echo "Usage: make pipeline CSV=data/raw/brand_dataset.csv"; exit 2)
	@$(VENV_PYTHON) -m brand_visibility.pipeline --csv "$(CSV)"

run:
	@$(STREAMLIT) run app.py

check:
	@$(VENV_PYTHON) -m compileall -q src app.py
	@$(VENV_PYTHON) -m brand_visibility.pipeline --demo
	@$(VENV_PYTHON) -c "from brand_visibility.config import DATABASE; from brand_visibility.data.load import load_from_database; frame = load_from_database(DATABASE); assert len(frame) > 0; assert {'brand', 'visibility_score', 'price_range', 'discount_pct'} <= set(frame.columns); print('Checks passed:', len(frame), 'products')"

tree:
	@find . -maxdepth 4 \
		-not -path './.git*' \
		-not -path './.venv*' \
		-not -path '*/__pycache__*' \
		-print | sort

clean:
	@find . -type d -name __pycache__ -prune -exec rm -rf {} +
	@find . -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete
	@rm -rf build dist .pytest_cache *.egg-info src/*.egg-info
	@echo "Python build and cache files removed."

clean-data:
	@rm -f data/processed/brand_visibility_clean.csv
	@rm -f data/processed/brand_visibility.db
	@rm -f data/processed/eda_summary.json
	@echo "Generated data removed; .gitkeep was preserved."

reset-data: clean-data demo
