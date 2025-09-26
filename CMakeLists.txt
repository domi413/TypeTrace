cmake_minimum_required(VERSION 4.1)

# ==================================================================
# Project Definition
# ==================================================================

set(CMAKE_CXX_COMPILER "clang++")
project(
    TypeTrace
    VERSION 0.1.0
    DESCRIPTION "The backend for the TypeTrace project"
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# ==================================================================
# Compiler Flags
# ==================================================================

# Global warning flags for all targets
add_compile_options(
    -Wall
    -Wcast-align
    -Wconversion
    -Wdouble-promotion
    -Werror
    -Wextra
    -Wformat=2
    -Wmisleading-indentation
    -Wnon-virtual-dtor
    -Wnull-dereference
    -Wold-style-cast
    -Woverloaded-virtual
    -Wpedantic
    -Wshadow
    -Wsign-conversion
    -Wunused
)

# Global link options
add_link_options(-flto -Wl,--gc-sections)

# ==================================================================
# Version Information
# ==================================================================

find_package(Git QUIET)
if(GIT_FOUND)
    execute_process(
        COMMAND ${GIT_EXECUTABLE} rev-parse --short HEAD
        WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
        OUTPUT_VARIABLE GIT_COMMIT
        OUTPUT_STRIP_TRAILING_WHITESPACE
        ERROR_QUIET
    )
    execute_process(
        COMMAND ${GIT_EXECUTABLE} diff --quiet
        WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
        RESULT_VARIABLE GIT_DIRTY
        ERROR_QUIET
    )
    if(NOT GIT_DIRTY EQUAL 0)
        set(GIT_COMMIT "${GIT_COMMIT}-dirty")
    endif()
else()
    set(GIT_COMMIT "unknown")
endif()

configure_file(
    typetrace/common/version/version.hpp.in
    ${CMAKE_BINARY_DIR}/generated/version.hpp
    @ONLY
)

# ==================================================================
# Dependencies
# ==================================================================

find_package(PkgConfig REQUIRED)
find_package(spdlog CONFIG REQUIRED)
find_package(SQLiteCpp CONFIG REQUIRED)

pkg_check_modules(DEPS REQUIRED libudev libinput libevdev)

# ==================================================================
# Subdirectories
# ==================================================================

add_subdirectory(typetrace/common)
add_subdirectory(typetrace/backend)
add_subdirectory(typetrace/frontend)
# add_subdirectory(tests)

# ==================================================================
# Installation & Build Info
# ==================================================================

install(TARGETS typetrace_backend RUNTIME DESTINATION bin)

message(STATUS "TypeTrace Backend:")
message(STATUS "  Version: ${PROJECT_VERSION} (${GIT_COMMIT})")
message(STATUS "  Build: ${CMAKE_BUILD_TYPE}")
message(
    STATUS
    "  Compiler: ${CMAKE_CXX_COMPILER_ID} ${CMAKE_CXX_COMPILER_VERSION}"
)
message(STATUS "  Standard: C++${CMAKE_CXX_STANDARD}")
