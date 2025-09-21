# TODO: Dependencies etc. are still missing

# Add sources from the various subdirectories
file(GLOB_RECURSE FRONTEND_SOURCES "src/*.cpp")

add_executable(typetrace_frontend ${FRONTEND_SOURCES})

target_link_libraries(typetrace_frontend PRIVATE typetrace_common)

target_include_directories(
    typetrace_frontend
    PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    PRIVATE ${CMAKE_BINARY_DIR}/generated
)

target_compile_options(
    typetrace_frontend
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
)

target_link_options(typetrace_frontend PRIVATE -flto -Wl,--gc-sections)

# If your .blp file needs to be processed, you would add a custom command here.
# For example, using glib-compile-resources if it's an XML file.
