# Backend executable for TypeTrace

# Find required dependencies
find_package(libevdev REQUIRED)
find_package(PkgConfig REQUIRED)
pkg_check_modules(LIBINPUT_VARS REQUIRED IMPORTED_TARGET libinput)
pkg_check_modules(UDEV_VARS REQUIRED IMPORTED_TARGET libudev)

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
    PRIVATE
        typetrace_common
        libevdev::libevdev
        ${LIBINPUT_VARS_LIBRARIES}
        ${UDEV_VARS_LIBRARIES}
)

# Include directories
target_include_directories(
    typetrace_backend
    PRIVATE ${CMAKE_CURRENT_SOURCE_DIR} ${CMAKE_BINARY_DIR}/generated
    PUBLIC cli database_manager dbus event_handler
    PRIVATE ${LIBINPUT_VARS_INCLUDE_DIRS} ${UDEV_VARS_INCLUDE_DIRS}
)
