.PHONY: all clean run lint format check-format

all: clean build

build:
	@rm -rf build/
	@mkdir build
	@cd build && cmake .. && make

clean:
	@rm -rf build/

run: build
	@./build/typetrace_backend -d

check-format:
	@echo "Checking code formatting..."
	@if clang-format --dry-run --Werror $$(find src -name "*.cpp" -o -name "*.hpp") 2>&1; then \
		echo "✓ All files are properly formatted"; \
	else \
		exit 1; \
	fi

fmt:
	@echo "Formatting code..."
	@clang-format -i $$(find src -name "*.cpp" -o -name "*.hpp")
	@echo "✓ Code formatting complete"

CLANG_TIDY_FLAGS = --warnings-as-errors='*'
CLANG_TIDY_COMPILE_FLAGS = -- -std=c++23 -D_GNU_SOURCE -Ibuild/generated

lint: build check-format
	@echo "Running clang-tidy..."
	@clang-tidy $(CLANG_TIDY_FLAGS) $$(find src -name "*.cpp" -o -name "*.hpp") $(CLANG_TIDY_COMPILE_FLAGS)
