/// Functions for resolving file paths in the application

#ifndef PATHS_H
#define PATHS_H

#include <stddef.h>

/// Creates all directories needed for the database path
int paths_ensure_db_directories(const char *path);

/// Resolves the path to the database file following XDG Base Directory spec
int paths_resolve_db_path(char *buffer, size_t size);

#endif /* PATHS_H */
