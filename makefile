.PHONY: all clean run debug lint format check-format fix

SOURCES_CPP = $(shell find typetrace/ tests/ -name "*.cpp" -o -name "*.hpp")
SOURCES_CMake = $(shell find typetrace/ tests/ -name "*CMakeLists.txt")

all: clean build

build:
	@echo "Configuring and building with Ninja..."
	@cmake --preset=default -GNinja
	@cmake --build build

clean:
	@echo "Removing build directory..."
	@rm -rf build/

run: build
	@echo "Running the typetrace backend..."
	@./build/typetrace/backend/typetrace_backend

debug: build
	@echo "Running the typetrace backend in debug mode..."
	@./build/typetrace/backend/typetrace_backend -d

check-format:
	@echo "Checking code formatting..."
	@if clang-format --dry-run --Werror $(SOURCES_CPP) && gersemi --check $(SOURCES_CMake); then \
		echo "✓ All files are properly formatted"; \
	else \
		exit 1; \
	fi

format:
	@echo "Formatting code..."
	@clang-format -i $(SOURCES_CPP)
	@gersemi -i $(SOURCES_CMake)
	@echo "✓ Code formatting complete"

# Flags for clang-tidy
LINT_COMMON_FLAGS = -p build/
LINT_TIDY_FLAGS = --warnings-as-errors='*'

lint: build
	@echo "Running clang-tidy..."
	@clang-tidy $(LINT_COMMON_FLAGS) $(LINT_TIDY_FLAGS) $(SOURCES_CPP)
	@echo "✓ Linting complete"

fix: build
	@echo "Auto-fixing clang-tidy issues..."
	@clang-tidy --fix $(LINT_COMMON_FLAGS) $(SOURCES_CPP)
	@echo "✓ Auto-fixes applied"

sort-dictionary:
	@echo "Sorting latexindent dictionary..."
	tr '[:upper:]' '[:lower:]' < .cspell_ignored.txt | sort -f -u -o .cspell_ignored.txt
	@echo "✓ Sorted and converted .cspell_ignored.txt to lowercase with unique entries"

cleanup-dictionary:
	@echo "Cleaning up unused words from .cspell_ignored.txt..."
	@.github/scripts/cleanup-cspell-ignored.sh

check-cspell-ignored:
	@echo "Checking for unused words in .cspell_ignored.txt..."
	@.github/scripts/check-cspell-ignored.sh
	@echo "✓ Cspell ignored file check complete"
