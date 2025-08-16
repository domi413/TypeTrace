#ifndef TYPETRACE_CONSTANTS_HPP
#define TYPETRACE_CONSTANTS_HPP

#include <cstddef>
#include <string_view>

namespace typetrace {

// ============================================================================
// Buffering Constants
// ============================================================================

/// Maximum number of keystrokes to buffer before writing to the database
constexpr std::size_t BUFFER_SIZE = 50;

/// Maximum time (in seconds) to buffer keystrokes before writing to the database
constexpr std::size_t BUFFER_TIMEOUT = 100;

/// Polling timeout in milliseconds for libinput events
constexpr std::size_t POLL_TIMEOUT_MS = 100;

// ============================================================================
// File and Directory Constants
// ============================================================================

/// The directory name
constexpr std::string_view PROJECT_DIR_NAME = "typetrace";

/// SQLite database file name
constexpr std::string_view DB_FILE_NAME = "TypeTrace.db";

} // namespace typetrace

#endif
