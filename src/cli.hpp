#ifndef TYPETRACE_CLI_HPP
#define TYPETRACE_CLI_HPP

#include "database.hpp"
#include "eventhandler.hpp"

#include <filesystem>
#include <span>

namespace typetrace {

class Cli
{
  public:
    explicit Cli(std::span<char *> args);

    auto run() -> void;

  private:
    static auto showHelp(const char *program_name) -> void;
    static auto showVersion() -> void;
    [[nodiscard]] static auto getDatabasePath() -> std::filesystem::path;

    auto parseArguments(std::span<char *> args) -> void;

    bool debug_mode{ false };

    DatabaseManager db_manager;
    EventHandler event_handler;
};

} // namespace typetrace

#endif
