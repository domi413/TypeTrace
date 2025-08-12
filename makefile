.PHONY: all clean run lint format check-format fix

all: clean build

build:
	@cmake --preset=default
	@cmake --build build

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

CLANG_TIDY_FLAGS = --warnings-as-errors=\'*\' --header-filter='^\$' --exclude-header-filter=\'.*\'
CLANG_TIDY_COMPILE_FLAGS = -- -std=c++23 -Ibuild/generated -Ibuild/vcpkg_installed/x64-linux/include -I/usr/include/libevdev-1.0 -Isrc

lint: build check-format
	@echo "Running clang-tidy..."
	@clang-tidy $(CLANG_TIDY_FLAGS) $$(find src -name "*.cpp" -o -name "*.hpp") $(CLANG_TIDY_COMPILE_FLAGS)
	@echo "✓ Linting complete"

fix: build
	@echo "Auto-fixing clang-tidy issues..."
	@clang-tidy --fix $(CLANG_TIDY_FLAGS) $$(find src -name "*.cpp" -o -name "*.hpp") $(CLANG_TIDY_COMPILE_FLAGS)
	@echo "✓ Auto-fixes applied"
