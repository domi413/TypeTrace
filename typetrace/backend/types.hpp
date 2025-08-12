#ifndef TYPETRACE_TYPES_HPP
#define TYPETRACE_TYPES_HPP

#include "constants.hpp"

#include <array>
#include <cstdlib>

namespace typetrace {

// ============================================================================
// Structures
// ============================================================================

// TODO(domi): Make benchmark to check if we can replace std::array with std::string.
//             This would simplify the code and improve readability.

/// Structure representing a keystroke event
struct KeystrokeEvent
{
    std::size_t key_code{};                           ///< Code of the pressed key
    std::array<char, KEY_NAME_MAX_LENGTH> key_name{}; ///< Human-readable name of the key
    std::array<char, DATE_STRING_LENGTH> date{};      ///< Date in YYYY-MM-DD format
};

} // namespace typetrace

#endif // TYPETRACE_TYPES_HPP
