add_executable(
    typetrace_backend
    src/cli.cpp
    src/database.cpp
    src/eventhandler.cpp
    src/main.cpp
)

target_link_libraries(
    typetrace_backend
    PRIVATE typetrace_common SQLiteCpp ${DEPS_LIBRARIES}
)

target_include_directories(
    typetrace_backend
    PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    PRIVATE ${CMAKE_BINARY_DIR}/generated ${DEPS_INCLUDE_DIRS}
)

target_compile_options(
    typetrace_backend
    PRIVATE
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

target_link_options(typetrace_backend PRIVATE -flto -Wl,--gc-sections)
