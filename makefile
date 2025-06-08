.PHONY: all clean run lint format check-format

all: build

build:
	@rm -rf build/
	@mkdir build
	@cd build && cmake .. && make

clean:
	@rm -rf build/

run: all
	@./build/typetrace_backend -d

check-format:
	@echo "Checking code formatting..."
	@if clang-format --dry-run --Werror $$(find src -name "*.c" -o -name "*.h") 2>&1; then \
		echo "✓ All files are properly formatted"; \
	else \
		exit 1; \
	fi

format:
	@echo "Formatting code..."
	@clang-format -i $$(find src -name "*.c" -o -name "*.h")
	@echo "✓ Code formatting complete"

lint: build check-format
	@echo "Running clang-tidy..."
	@clang-tidy --warnings-as-errors='*' $$(find src -name "*.c" -o -name "*.h") -- -std=c23 -D_GNU_SOURCE -Ibuild/generated
	@echo "Running cppcheck..."
	@cppcheck --enable=all --suppress=missingIncludeSystem --suppress=unusedStructMember --check-level=exhaustive --std=c23 --platform=unix64 -Isrc/ -Ibuild/generated/ --template=gcc --error-exitcode=1 $$(find src -name "*.c" -o -name "*.h")
