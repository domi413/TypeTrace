#!/bin/bash

# Change to the TypeTrace main directory
cd "$(dirname "$0")/.." || exit 1

# Install all Python dependencies
pip install -r requirements.txt

# Format code with ruff (disable COM812 if necessary)
ruff format ./typetrace/

# Run code quality checks with pylint & flake8
pylint ./typetrace/ --exit-zero
flake8 ./typetrace/

# Check if cloc is installed, then generate code statistics
if command -v cloc >/dev/null 2>&1; then
    cloc ./typetrace/
else
    echo "Warning: cloc is not installed. Please install it separately (e.g., 'sudo apt install cloc' on Ubuntu)."
fi

# Run tests with pytest and generate a coverage report
pytest --cov=typetrace ./typetrace/tests/