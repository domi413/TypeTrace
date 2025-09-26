# Frontend executable for TypeTrace

# Find required dependencies
find_package(PkgConfig REQUIRED)
pkg_check_modules(GTKMM REQUIRED gtkmm-4.0)

# Source files
set(FRONTEND_SOURCES application.cpp main.cpp)

# Create executable
add_executable(typetrace_frontend ${FRONTEND_SOURCES})

# Link libraries
target_link_libraries(
    typetrace_frontend
    PRIVATE typetrace_common ${GTKMM_LIBRARIES}
)

# Include directories
target_include_directories(typetrace_frontend
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}
)

# System include directories (suppresses warnings)
target_include_directories(typetrace_frontend
    SYSTEM PRIVATE
        ${GTKMM_INCLUDE_DIRS}
)

# Link directories
target_link_directories(typetrace_frontend PRIVATE ${GTKMM_LIBRARY_DIRS})
