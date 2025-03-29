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

# Generate code statistics with cloc
cloc ./typetrace/

# Run tests with pytest and generate a coverage report
pytest --cov=typetrace ./typetrace/tests/

# to run ./scripts/run_tests.sh
