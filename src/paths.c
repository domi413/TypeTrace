/// Implementation of path resolution functions

#include "paths.h"
#include "common.h"

#include <errno.h>
#include <libgen.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

// ============================================================================
// Static Functions
// ============================================================================

/// Validate and copy a path to a buffer
static int validate_and_copy_path(const char *path, char *buffer, size_t buffer_size)
{
    if (path == nullptr) {
        return -1;
    }

    size_t path_len = strnlen(path, MAX_PATH_LENGTH);
    if (path_len >= MAX_PATH_LENGTH || path_len >= buffer_size) {
        DEBUG_PRINT("Path too long: %s\n", path);
        return -1;
    }

    // Safe copy using snprintf with guaranteed null termination
    (void)snprintf(buffer, buffer_size, "%s", path);
    return OK;
}

/// Safe snprintf for home path construction
static int safe_home_path(char *buffer, size_t size, const char *home)
{
    int result = snprintf(buffer, size, "%s/.local/share", home);
    if (result < 0 || (size_t)result >= size) {
        return -1;
    }
    return OK;
}

/// Safe snprintf for database path construction
static int safe_db_path(char *buffer,
                        size_t size,
                        const char *data_dir,
                        const char *project_dir,
                        const char *db_file)
{
    int result = snprintf(buffer, size, "%s/%s/%s", data_dir, project_dir, db_file);
    if (result < 0 || (size_t)result >= size) {
        return -1;
    }
    return OK;
}

/// Get the data directory path (XDG or ~/.local/share fallback)
static int get_data_directory(char *data_path, size_t size)
{
    const char *data_dir = getenv("XDG_DATA_HOME");

    if (data_dir != nullptr && data_dir[0] != '\0') {
        return validate_and_copy_path(data_dir, data_path, size);
    }

    const char *home = getenv("HOME");
    if (home == nullptr || home[0] == '\0') {
        (void)fprintf(stderr, "HOME environment variable not set\n");
        return -1;
    }

    return safe_home_path(data_path, size, home);
}

/// Create a single directory with error handling
static int create_single_directory(const char *path)
{
    if (mkdir(path, S_IRWXU) != 0 && errno != EEXIST) {
        DEBUG_PRINT("Failed to create directory: %s (%s)\n", path, strerror(errno));
        return -1;
    }
    return OK;
}

/// Create a directory recursively (like mkdir -p)
static int create_directory_recursive(const char *path)
{
    char path_copy[MAX_PATH_LENGTH];
    size_t len = 0;

    if (validate_and_copy_path(path, path_copy, sizeof(path_copy)) != OK) {
        return -1;
    }

    len = strnlen(path_copy, MAX_PATH_LENGTH);
    if (len > 0 && path_copy[len - 1] == '/') {
        path_copy[len - 1] = '\0';
    }

    for (char *current_path = path_copy + 1; *current_path; current_path++) {
        if (*current_path == '/') {
            *current_path = '\0';

            if (create_single_directory(path_copy) != OK) {
                return -1;
            }

            *current_path = '/';
        }
    }

    // Create the final directory
    if (create_single_directory(path_copy) != OK) {
        return -1;
    }

    return OK;
}

// ============================================================================
// Public Functions
// ============================================================================

/// Creates all directories needed for the database path
int paths_ensure_db_directories(const char *path)
{
    char path_copy[MAX_PATH_LENGTH];
    const char *dir = nullptr;

    if (validate_and_copy_path(path, path_copy, sizeof(path_copy)) != OK) {
        return -1;
    }

    dir = dirname(path_copy);

    DEBUG_PRINT("Creating directory path: %s\n", dir);
    const int result = create_directory_recursive(dir);

    if (result != 0) {
        DEBUG_PRINT("Failed to create directory for %s\n", path);
        return -1;
    }

    return OK;
}

/// Resolves the path to the database file following XDG Base Directory spec
int paths_resolve_db_path(char *buffer, const size_t size)
{
    char data_path[MAX_PATH_LENGTH];

    if (get_data_directory(data_path, sizeof(data_path)) != OK) {
        return -1;
    }

    if (safe_db_path(buffer, size, data_path, PROJECT_DIR_NAME, DB_FILE_NAME) != OK) {
        (void)fprintf(stderr, "Path buffer too small\n");
        return -1;
    }

    DEBUG_PRINT("Database path: %s (using data_dir: %s)\n", buffer, data_path);
    return OK;
}
