#ifndef TYPETRACE_TYPES_HPP
#define TYPETRACE_TYPES_HPP

#include <cstddef>
#include <string>

namespace typetrace {

// ============================================================================
// Structures
// ============================================================================

/// Structure representing a keystroke event
struct KeystrokeEvent
{
    std::size_t key_code{}; ///< Code of the pressed key
    std::string key_name;   ///< Human-readable name of the key
    std::string date;       ///< Date in YYYY-MM-DD format
};

} // namespace typetrace

#endif // TYPETRACE_TYPES_HPP
