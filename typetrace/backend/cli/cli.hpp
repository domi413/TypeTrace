#ifndef TYPETRACE_CLI_HPP
#define TYPETRACE_CLI_HPP

#include "database_manager.hpp"
#include "event_handler.hpp"

#include <filesystem>
#include <memory>
#include <span>

namespace typetrace {

class Cli
{
  public:
    /// Constructs a CLI instance and parses command line arguments
    explicit Cli(std::span<char *> args);

    /// Runs the main event loop for keystroke tracing
    auto run() -> void;

  private:
    /// Parses and processes command line arguments
    static auto parseArguments(std::span<char *> args) -> void;

    /// Displays help information and usage instructions
    static auto showHelp(const char *program_name) -> void;

    /// Displays the program version information
    static auto showVersion() -> void;

    /// Gets the database directory path using XDG or fallback locations
    [[nodiscard]] static auto getDatabaseDir() -> std::filesystem::path;

    std::unique_ptr<EventHandler> event_handler;
    std::unique_ptr<DatabaseManager> db_manager;
};

} // namespace typetrace

#endif
