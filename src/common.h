/// Common definitions, constants, and macros used throughout TypeTrace

#ifndef COMMON_H
#define COMMON_H

#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

// ============================================================================
// Macros
// ============================================================================

/// Debug print macro that only outputs if debug_mode is enabled
#define DEBUG_PRINT(...)         \
    do {                         \
        if (debug_mode) {        \
            printf(__VA_ARGS__); \
        }                        \
    } while (0)

// ============================================================================
// Constants
// ============================================================================

/// Constants for time conversions
static constexpr double NANOSECONDS_PER_SECOND = 1E9;

/// Constant to define the polling timeout for libinput events
static constexpr unsigned int POLL_TIMEOUT_MS = 100;

/// Error buffer size for storing error messages
static constexpr size_t ERROR_BUFFER_SIZE = 256;

/// Maximum length for file paths (4096 is Linux max)
static constexpr size_t MAX_PATH_LENGTH = 4096;

/// Maximum length for key names in the database
static constexpr size_t KEY_NAME_MAX_LENGTH = 32;

/// Length of the date string in YYYY-MM-DD format
static constexpr size_t DATE_STRING_LENGTH = 11;

/// The directory name
static constexpr char PROJECT_DIR_NAME[] = "typetrace";

/// SQLite database file name
static constexpr char DB_FILE_NAME[] = "TypeTrace.db";

/// Maximum number of keystrokes to buffer before writing to the database
static constexpr unsigned int BUFFER_SIZE = 50;

/// Maximum time (in seconds) to buffer keystrokes before writing to the database
static constexpr unsigned int BUFFER_TIMEOUT = 100;

/// Maximum length for usernames (for permission checking)
static constexpr size_t USERNAME_MAX_LENGTH = 256;

// ============================================================================
// External Variables
// ============================================================================

/// Debug mode control variable (enabled with -d or --debug)
extern bool debug_mode;

/// The path to the database
extern char db_file_path[MAX_PATH_LENGTH];

// ============================================================================
// Enumerations
// ============================================================================

/// Error codes returned by application functions
enum error_code
{
    OK,               /**< Operation completed successfully */
    WRONG_ARGUMENT,   /**< Invalid command-line argument provided */
    UDEV_FAILED,      /**< Failed to initialize or use udev */
    LIBINPUT_FAILED,  /**< Failed to initialize or use libinput */
    SEAT_FAILED,      /**< Failed to assign a seat to libinput */
    BUFFER_ERROR,     /**< Buffer operation failed */
    PERMISSION_ERROR, /**< Permission denied, user not in input group */
    NO_DEVICES_ERROR, /**< No input devices available or accessible */
    INFORMATION_EXIT, /**< Information exit code */
};

/// Structure representing a keystroke event
typedef struct keystroke_event
{
    uint32_t key_code;                  /**< Code of the pressed key */
    char key_name[KEY_NAME_MAX_LENGTH]; /**< Human-readable name of the key */
    char date[DATE_STRING_LENGTH];      /**< Date in YYYY-MM-DD format */
} keystroke_event_t;

#endif // COMMON_H
