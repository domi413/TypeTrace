/**
 * @file common.h
 * @brief Common definitions, constants, and macros used throughout the TypeTrace
 *        application.
 *
 * This header file contains shared definitions for error codes, debugging macros,
 * and global constants used by the TypeTrace keyboard input tracking application.
 */

#ifndef COMMON_H
#define COMMON_H

#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

// ============================================================================
// Macros
// ============================================================================

/**
 * @brief Debug print macro that only outputs if debug_mode is enabled
 *
 * @param ... Arguments passed directly to printf()
 */
#define DEBUG_PRINT(...)     \
    if (debug_mode) {        \
        printf(__VA_ARGS__); \
    }

// ============================================================================
// Constants
// ============================================================================

/**
 * @brief Constants for time conversions
 */
static constexpr double NANOSECONDS_PER_SECOND = 1E9;

/**
 * @brief Constant to define the polling timeout for libinput events
 */
static constexpr unsigned int POLL_TIMEOUT_MS = 100;

/**
 * @brief Error buffer size for storing error messages
 */
static constexpr size_t ERROR_BUFFER_SIZE = 256;

/**
 * @brief Maximum length for file paths. 4096 characters is the maximum path length on
 * Linux
 */
static constexpr size_t MAX_PATH_LENGTH = 4096;

/**
 * @brief Maximum length for key names
 *
 * This is the maximum length of a key name in the database.
 * It should be sufficient for most keys, including special keys.
 */
static constexpr size_t KEY_NAME_MAX_LENGTH = 32;

/**
 * @brief Length of the date string in YYYY-MM-DD format: "YYYY-MM-DD\0"
 */
static constexpr size_t DATE_STRING_LENGTH = 11;

/**
 * @brief The directory name
 */
static constexpr char PROJECT_DIR_NAME[] = "typetrace";

/**
 * @brief SQLite database file name
 */
static constexpr char DB_FILE_NAME[] = "TypeTrace.db";

/**
 * @brief Maximum number of keystrokes to buffer before writing to the database
 */
static constexpr unsigned int BUFFER_SIZE = 50;

/**
 * @brief Maximum time (in seconds) to buffer keystrokes before writing to the database
 */
static constexpr unsigned int BUFFER_TIMEOUT = 100;

// ============================================================================
// External Variables
// ============================================================================

/**
 * @brief Debug mode control variable
 *
 * Can be enabled at runtime with -d or --debug flag in the command line
 */
extern bool debug_mode;

/**
 * @brief The path to the database
 */
extern char db_file_path[MAX_PATH_LENGTH];

// ============================================================================
// Enumerations
// ============================================================================

/**
 * @brief Error codes returned by application functions
 */
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

/**
 * @brief Structure representing a keystroke event
 */
typedef struct keystroke_event
{
    uint32_t key_code;                  /**< Code of the pressed key */
    char key_name[KEY_NAME_MAX_LENGTH]; /**< Human-readable name of the key */
    char date[DATE_STRING_LENGTH];      /**< Date in YYYY-MM-DD format */
} keystroke_event_t;

#endif // COMMON_H
