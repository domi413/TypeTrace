add_executable(typetrace_backend
    cli.cpp
    database.cpp
    eventhandler.cpp
    main.cpp
    ${CMAKE_SOURCE_DIR}/typetrace/logger.cpp
)

target_include_directories(typetrace_backend PRIVATE
    ${CMAKE_SOURCE_DIR}/typetrace
    ${CMAKE_SOURCE_DIR}/typetrace/backend

    ${CMAKE_BINARY_DIR}/generated
    ${DEPS_INCLUDE_DIRS}
)

target_link_libraries(typetrace_backend PRIVATE
    ${DEPS_LIBRARIES}
    SQLiteCpp
    spdlog::spdlog
)

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
