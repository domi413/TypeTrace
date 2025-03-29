#!/bin/bash

# Wechsel ins Hauptverzeichnis von TypeTrace
cd "$(dirname "$0")/.." || exit 1

# Installiere alle Python-Abhängigkeiten
pip install -r requirements.txt

# Code formatieren mit ruff (falls COM812 Fehler, deaktivieren)
ruff format ./typetrace/

# Code-Qualitätsprüfung mit pylint & flake8
pylint ./typetrace/ --exit-zero
flake8 ./typetrace/

# Code-Statistiken mit cloc
cloc ./typetrace/

# Tests mit pytest + coverage-Report
pytest --cov=typetrace ./typetrace/tests/

# to run ./scripts/run_tests.sh
