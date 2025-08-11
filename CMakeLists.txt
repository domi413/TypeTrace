cmake_minimum_required(VERSION 3.16)

# ============================================================================
# Project Definition
# ============================================================================
project(TypeTrace
    VERSION 0.1.0
    DESCRIPTION "The backend for the TypeTrace project"
    LANGUAGES CXX
)

# ============================================================================
# Build Configuration
# ============================================================================
set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Generate compile_commands.json for clangd
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Default to Release build if not specified
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# Add GNU source feature test macro
add_compile_definitions(_GNU_SOURCE)

# ============================================================================
# Version Information
# ============================================================================
# Get git commit hash if available
find_package(Git QUIET)
if(GIT_FOUND)
    execute_process(
        COMMAND ${GIT_EXECUTABLE} rev-parse --short HEAD
        WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
        OUTPUT_VARIABLE GIT_COMMIT
        OUTPUT_STRIP_TRAILING_WHITESPACE
        ERROR_QUIET
    )

    # Check if working directory is dirty
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

# ============================================================================
# Dependencies
# ============================================================================
find_package(PkgConfig REQUIRED)

pkg_check_modules(LIBUDEV REQUIRED libudev)
pkg_check_modules(LIBINPUT REQUIRED libinput)
pkg_check_modules(LIBEVDEV REQUIRED libevdev)
pkg_check_modules(SQLITE3 REQUIRED sqlite3)

# Find SQLiteCpp
find_path(SQLITECPP_INCLUDE_DIR SQLiteCpp/SQLiteCpp.h
    PATHS /usr/include /usr/local/include
)
find_library(SQLITECPP_LIBRARY NAMES SQLiteCpp libSQLiteCpp
    PATHS /usr/lib /usr/local/lib /usr/lib/x86_64-linux-gnu
)

if(NOT SQLITECPP_INCLUDE_DIR OR NOT SQLITECPP_LIBRARY)
    message(FATAL_ERROR "SQLiteCpp not found. Please install libsqlitecpp-dev")
endif()

# ============================================================================
# Generated Files
# ============================================================================
configure_file(
    ${CMAKE_SOURCE_DIR}/src/version.hpp.in
    ${CMAKE_BINARY_DIR}/generated/version.hpp
    @ONLY
)

# ============================================================================
# Executable Target
# ============================================================================
add_executable(typetrace_backend
    src/main.cpp
    src/cli.cpp
    src/eventhandler.cpp
    src/database.cpp
)

# Include directories
target_include_directories(typetrace_backend PRIVATE
    src
    ${CMAKE_BINARY_DIR}/generated
    ${LIBUDEV_INCLUDE_DIRS}
    ${LIBINPUT_INCLUDE_DIRS}
    ${LIBEVDEV_INCLUDE_DIRS}
    ${SQLITE3_INCLUDE_DIRS}
    ${SQLITECPP_INCLUDE_DIR}
)

# Link libraries
target_link_libraries(typetrace_backend PRIVATE
    ${LIBUDEV_LIBRARIES}
    ${LIBINPUT_LIBRARIES}
    ${LIBEVDEV_LIBRARIES}
    ${SQLITE3_LIBRARIES}
    ${SQLITECPP_LIBRARY}
)

# Compiler flags
target_compile_options(typetrace_backend PRIVATE
    -Wall -Wextra
    -Wshadow
    -Wcast-align
    -Wconversion
    -Wdouble-promotion
    -Wduplicated-branches
    -Wduplicated-cond
    -Werror
    -Wformat=2
    -Wlogical-op
    -Wmisleading-indentation
    -Wnon-virtual-dtor
    -Wnull-dereference
    -Wold-style-cast
    -Woverloaded-virtual
    -Wpedantic
    -Wshadow
    -Wsign-conversion
    -Wunused
    -Wuseless-cast
    ${LIBEVDEV_CFLAGS_OTHER}
    ${LIBINPUT_CFLAGS_OTHER}
    ${LIBUDEV_CFLAGS_OTHER}
    ${SQLITE3_CFLAGS_OTHER}
)

# ============================================================================
# Installation
# ============================================================================
install(TARGETS typetrace_backend
    RUNTIME DESTINATION bin
)

# ============================================================================
# Build Information
# ============================================================================
message(STATUS "TypeTrace Backend Configuration:")
message(STATUS "  Version: ${PROJECT_VERSION}")
message(STATUS "  Git Commit: ${GIT_COMMIT}")
message(STATUS "  Build Type: ${CMAKE_BUILD_TYPE}")
message(STATUS "  CXX Standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "")
message(STATUS "Dependencies:")
message(STATUS "  libudev: ${LIBUDEV_VERSION}")
message(STATUS "  libinput: ${LIBINPUT_VERSION}")
message(STATUS "  libevdev: ${LIBEVDEV_VERSION}")
message(STATUS "  sqlite3: ${SQLITE3_VERSION}")
