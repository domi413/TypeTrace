#ifndef TYPETRACE_TYPES_HPP
#define TYPETRACE_TYPES_HPP

#include "constants.hpp"

#include <array>
#include <cstdlib>

namespace typetrace {

// ============================================================================
// Structures
// ============================================================================

/// Structure representing a keystroke event
struct KeystrokeEvent
{
    /// Code of the pressed key
    std::size_t key_code{};

    /// Human-readable name of the key
    std::array<char, KEY_NAME_MAX_LENGTH> key_name{};

    /// Date in YYYY-MM-DD format
    std::array<char, DATE_STRING_LENGTH> date{};
};

} // namespace typetrace

#endif // TYPETRACE_TYPES_HPP
