/**
 * @file paths.h
 * @brief Functions for resolving file paths in the application
 *
 * This file provides functions for determining the correct paths
 * for application data files such as the database, following
 * the XDG Base Directory specification on Linux systems.
 */

#ifndef PATHS_H
#define PATHS_H

#include <stddef.h>

/**
 * @brief Creates all directories needed for the database path
 *
 * Ensures that all directories in the database path exist,
 * creating them if necessary.
 *
 * @param path Path for which to create directories
 * @return 0 on success, -1 on failure
 */
int paths_ensure_db_directories(const char *path);

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
int paths_resolve_db_path(char *buffer, size_t size);

#endif /* PATHS_H */
