.PHONY: all clean run lint

all: build

build:
	@rm -rf build/
	@mkdir build
	@cd build && cmake .. && make

clean:
	@rm -rf build/

run: all
	@./build/typetrace_backend -d

lint: build
	@echo "Running clang-tidy..."
	@clang-tidy $$(find src -name "*.c" -o -name "*.h") -- -std=c23 -D_GNU_SOURCE -Ibuild/generated
	@echo "Running cppcheck..."
	@cppcheck --enable=all --suppress=missingIncludeSystem --check-level=exhaustive --std=c23 --platform=unix64 -Isrc/ -Ibuild/generated/ --template=gcc $$(find src -name "*.c" -o -name "*.h")
