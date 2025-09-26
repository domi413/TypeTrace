# Backend executable for TypeTrace

# Find required dependencies
find_package(PkgConfig REQUIRED)
pkg_check_modules(LIBEVDEV REQUIRED libevdev)

# Source files
set(BACKEND_SOURCES
    cli/cli.cpp
    database_manager/database_manager.cpp
    dbus/dbus.cpp
    event_handler/event_handler.cpp
    main.cpp
)

# Create executable
add_executable(typetrace_backend ${BACKEND_SOURCES})

# Link libraries
target_link_libraries(
    typetrace_backend
    PRIVATE typetrace_common SQLiteCpp ${DEPS_LIBRARIES}
)

# Include directories
target_include_directories(
    typetrace_backend
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}
        ${CMAKE_BINARY_DIR}/generated
        ${DEPS_INCLUDE_DIRS}
        ${LIBEVDEV_INCLUDE_DIRS}
    PUBLIC cli database_manager dbus event_handler
)
