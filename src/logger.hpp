#ifndef TYPETRACE_LOGGER_HPP
#define TYPETRACE_LOGGER_HPP

#include "spdlog/logger.h"

#include <memory>

namespace typetrace {

/// Initializes the global logger with a console sink.
/// If `debug_mode` is true, sets the log level to `debug`, otherwise `info`.
void initLogger(bool debug_mode);

/// Get the global logger instance.
auto getLogger() -> std::shared_ptr<spdlog::logger>;

} // namespace typetrace

#endif
