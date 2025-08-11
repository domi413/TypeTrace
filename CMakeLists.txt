cmake_minimum_required(VERSION 3.16)

# ============================================================================
# Project Definition
# ============================================================================
set(CMAKE_CXX_COMPILER "clang++")
project(TypeTrace
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

add_compile_definitions(_GNU_SOURCE)

# ============================================================================
# Version Information
# ============================================================================
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

# ============================================================================
# Dependencies
# ============================================================================
find_package(PkgConfig REQUIRED)

pkg_check_modules(DEPS REQUIRED libudev libinput libevdev sqlite3)

find_path(SQLITECPP_INCLUDE_DIR SQLiteCpp/SQLiteCpp.h)
find_library(SQLITECPP_LIBRARY NAMES SQLiteCpp)

if(NOT SQLITECPP_INCLUDE_DIR OR NOT SQLITECPP_LIBRARY)
    message(FATAL_ERROR "SQLiteCpp not found. Please install libsqlitecpp-dev")
endif()

# ============================================================================
# Generated Files & Executable
# ============================================================================
configure_file(src/version.hpp.in ${CMAKE_BINARY_DIR}/generated/version.hpp @ONLY)

add_executable(typetrace_backend
    src/cli.cpp
    src/database.cpp
    src/eventhandler.cpp
    src/logger.cpp
    src/main.cpp
)

target_include_directories(typetrace_backend PRIVATE
    src
    ${CMAKE_BINARY_DIR}/generated
    ${DEPS_INCLUDE_DIRS}
    ${SQLITECPP_INCLUDE_DIR}
)

target_link_libraries(typetrace_backend PRIVATE
    ${DEPS_LIBRARIES}
    ${SQLITECPP_LIBRARY}
)

# ============================================================================
# Compiler Flags
# ============================================================================
target_compile_options(typetrace_backend PRIVATE
    # Optimization
    -O3

    # Warnings
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

    ${DEPS_CFLAGS_OTHER}
)

target_link_options(typetrace_backend PRIVATE
    -flto -Wl,--gc-sections
)

# ============================================================================
# Installation & Build Info
# ============================================================================
install(TARGETS typetrace_backend RUNTIME DESTINATION bin)

message(STATUS "TypeTrace Backend:")
message(STATUS "  Version: ${PROJECT_VERSION} (${GIT_COMMIT})")
message(STATUS "  Build: ${CMAKE_BUILD_TYPE}")
message(STATUS "  Compiler: ${CMAKE_CXX_COMPILER_ID} ${CMAKE_CXX_COMPILER_VERSION}")
message(STATUS "  Standard: C++${CMAKE_CXX_STANDARD}")
