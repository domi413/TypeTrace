#include "cli.hpp"

#include "constants.hpp"
#include "database.hpp"
#include "eventhandler.hpp"
#include "exceptions.hpp"
#include "logger.hpp"
#include "types.hpp"
#include "version.hpp"

#include <cstdlib>
#include <filesystem>
#include <memory>
#include <print>
#include <span>
#include <string_view>
#include <vector>

namespace typetrace {

/// Constructs a CLI instance and parses command line arguments
Cli::Cli(std::span<char *> args)
{
    parseArguments(args);

    db_manager = std::make_unique<DatabaseManager>(getDatabaseDir());
    event_handler = std::make_unique<EventHandler>();

    // Set up callback for EventHandler to flush buffer to database
    event_handler->setBufferCallback(
      [this](const std::vector<KeystrokeEvent> &buffer) { db_manager->writeToDatabase(buffer); });
}

/// Runs the main event loop for keystroke tracing
auto Cli::run() -> void
{
    while (true) { // use eventhandler to quit
        event_handler->trace();
    }
};

/// Displays help information and usage instructions
auto Cli::showHelp(const char *program_name) -> void
{
    std::print(R"(
The backend of TypeTrace
Version: {}

Usage: {} [OPTION…]

Options:
 -h, --help      Display help then exit.
 -v, --version   Display version then exit.
 -d, --debug     Enable debug mode.

Warning: This is the backend and is not designed to run by users.
You should run the frontend of TypeTrace which will run this.
)",
               PROJECT_VERSION,
               program_name);
};

/// Displays the program version information
auto Cli::showVersion() -> void
{
    std::println(PROJECT_VERSION);
};

/// Gets the database directory path using XDG or fallback locations
auto Cli::getDatabaseDir() -> std::filesystem::path
{
    if (const char *xdg_path = std::getenv("XDG_DATA_HOME")) {
        getLogger()->debug("Found XDG data directory: {}", xdg_path);
        return std::filesystem::path{ xdg_path } / PROJECT_DIR_NAME;
    }

    const char *home = std::getenv("HOME");
    if (home == nullptr) {
        getLogger()->critical("HOME environment variable is not set");
        throw SystemError("HOME environment variable is not set");
    }

    getLogger()->debug("Using default home directory: {}", home);
    return std::filesystem::path{ home } / ".local" / "share" / PROJECT_DIR_NAME;
};

/// Parses and processes command line arguments
auto Cli::parseArguments(std::span<char *> args) -> void
{
    bool debug_mode{ false };

    for (std::size_t i = 1; i < args.size(); i++) {
        std::string_view arg{ args[i] };

        if (arg == "-h" || arg == "--help") {
            showHelp(args[0]);
            std::exit(0);
        } else if (arg == "-v" || arg == "--version") {
            showVersion();
            std::exit(0);
        } else if (arg == "-d" || arg == "--debug") {
            debug_mode = true;
        } else {
            std::println("Unknown option: {}", arg);
            showHelp(args[0]);
            std::exit(1);
        }
    }

    initLogger(debug_mode);
};

} // namespace typetrace
