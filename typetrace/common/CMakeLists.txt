# Common library for TypeTrace

# Find required dependencies
find_package(spdlog CONFIG REQUIRED)

# Source files
set(COMMON_SOURCES logger/logger.cpp)

# Create static library
add_library(typetrace_common STATIC ${COMMON_SOURCES})

# Link libraries
target_link_libraries(typetrace_common PUBLIC spdlog::spdlog)

# Include directories
target_include_directories(
    typetrace_common
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        constants
        exceptions
        logger
        sql
        types
        version
)
