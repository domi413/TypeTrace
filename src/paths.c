/**
 * @file paths.c
 * @brief Implementation of path resolution functions
 *
 * This file implements functions for resolving file paths in the application,
 * following the XDG Base Directory specification on Linux systems.
 */

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
// Public Functions
// ============================================================================

/**
 * @brief Creates all directories needed for the database path
 *
 * Uses the system command 'mkdir -p' to create all necessary parent directories.
 *
 * @param path Path for which to create directories
 * @return 0 on success, -1 on failure
 */
int paths_ensure_db_directories(const char *path)
{
    char path_copy[MAX_PATH_LENGTH];
    const char *dir = nullptr;

    strncpy(path_copy, path, MAX_PATH_LENGTH - 1);
    path_copy[MAX_PATH_LENGTH - 1] = '\0';

    dir = dirname(path_copy);

    char cmd[MAX_PATH_LENGTH];
    if (snprintf(cmd, sizeof(cmd), "mkdir -p \"%s\"", dir) < 0) {
        perror("snprintf failed");
        return -1;
    }

    DEBUG_PRINT("Executing command: %s\n", cmd);
    const int result = system(cmd);

    if (result != 0) {
        DEBUG_PRINT("Failed to create directory for %s (error: %d, errno: %s)\n",
                    path,
                    result,
                    strerror(errno));
        return -1;
    }

    return OK;
}

/**
 * @brief Resolves the path to the database file
 *
 * Determines the correct path to the database file according to
 * the XDG Base Directory Specification. On Linux, this is typically
 * ~/.local/share/typetrace/TypeTrace.db
 *
 * @param buffer Buffer to store the resolved path
 * @param size Size of the buffer
 * @return 0 on success, -1 on failure (e.g., buffer too small)
 */
int paths_resolve_db_path(char *buffer, const size_t size)
{
    char data_path[MAX_PATH_LENGTH];
    const char *data_dir = getenv("XDG_DATA_HOME");

    if (data_dir == nullptr || data_dir[0] == '\0') {
        const char *home = getenv("HOME");
        if (home == nullptr || home[0] == '\0') {
            (void)fprintf(stderr, "HOME environment variable not set\n");
            return -1;
        }

        // Construct the default XDG data path
        if (snprintf(data_path, sizeof(data_path), "%s/.local/share", home) < 0) {
            perror("snprintf failed");
            return -1;
        }
        data_dir = data_path;
    }

    const int path_length =
      snprintf(buffer, size, "%s/%s/%s", data_dir, PROJECT_DIR_NAME, DB_FILE_NAME);

    if (path_length < 0 || (size_t)path_length >= size) {
        (void)fprintf(stderr, "Path buffer too small\n");
        return -1;
    }

    DEBUG_PRINT("Database path: %s (using data_dir: %s)\n", buffer, data_dir);
    return OK;
}
