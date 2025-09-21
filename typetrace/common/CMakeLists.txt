add_library(typetrace_common STATIC src/logger.cpp)

target_include_directories(
    typetrace_common
    PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
)

target_link_libraries(typetrace_common PUBLIC spdlog::spdlog)

target_compile_options(
    typetrace_common
    PRIVATE
        -O3
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

target_link_options(typetrace_common PRIVATE -flto -Wl,--gc-sections)
