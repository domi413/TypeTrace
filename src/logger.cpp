#include "logger.hpp"

#include "spdlog/common.h"
#include "spdlog/logger.h"
#include "spdlog/sinks/stdout_color_sinks.h" // NOLINT

#include <memory>

namespace typetrace {

// Sets the log level of the global logger based on the debug mode
auto initLogger(bool debug_mode) -> void
{

    if (debug_mode) {
        getLogger()->set_level(spdlog::level::debug);
    } else {
        getLogger()->set_level(spdlog::level::info);
    }
}

// Create a console logger with color output
auto getLogger() -> std::shared_ptr<spdlog::logger>
{
    return spdlog::stdout_color_mt("typetrace", spdlog::color_mode::automatic); // NOLINT
}

} // namespace typetrace
