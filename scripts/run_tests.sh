#!/bin/bash

# Change to the TypeTrace main directory
cd "$(dirname "$0")/.." || exit 1

# Install all Python dependencies from the requirements file
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Install optional dev tools if needed (ruff wird vorausgesetzt, ist aber in requirements.txt)
if ! command -v ruff &> /dev/null; then
    echo " 'ruff' is being installed..."
    pip install ruff
fi

# Format code with ruff (line length 79, gesamter typetrace-Ordner)
echo " Formatting with ruff..."
ruff format ./typetrace/ --line-length 79

# Run ruff check with auto-fix (nach Formatierung, um restliche Fixes zu machen)
echo " Running ruff check with auto-fix..."
ruff check ./typetrace/ --fix

# Run code quality checks with pylint & flake8
echo " Running pylint..."
pylint ./typetrace/ --exit-zero
echo " Running flake8..."
flake8 ./typetrace/

# Check if cloc is installed, then generate code statistics
if command -v cloc >/dev/null 2>&1; then
    echo " Generating code statistics with cloc..."
    cloc ./typetrace/
else
    echo " Warning: cloc is not installed. Install via 'sudo apt install cloc'"
fi

# Run all tests with pytest and generate a coverage report
echo " Running tests with pytest..."
pytest --cov=typetrace ./typetrace/tests/

# Optional: Run NFR verification script (falls gewünscht)
echo " Running NFR verification..."
ruff format "$HOME/TypeTrace/typetrace" && python3 /home/mustafa/TypeTrace/scripts/nfr-verification-script.py --nfr=all --source-dir="$HOME/TypeTrace/typetrace" --db-path="$HOME/.local/share/typetrace/TypeTrace.db"

