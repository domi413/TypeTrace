#ifndef TYPETRACE_DATABASE_HPP
#define TYPETRACE_DATABASE_HPP

#include "types.hpp"

#include <SQLiteCpp/Database.h>
#include <filesystem>
#include <memory>
#include <vector>

namespace typetrace {

class DatabaseManager
{
  public:
    /// Constructs a database manager and initializes the database connection
    explicit DatabaseManager(const std::filesystem::path &db_dir);

    /// Writes a buffer of keystroke events to the database
    auto writeToDatabase(const std::vector<KeystrokeEvent> &buffer) -> void;

  private:
    /// Creates necessary database tables if they don't exist
    auto createTables() -> void;

    std::filesystem::path db_file;
    std::unique_ptr<SQLite::Database> db;
};

} // namespace typetrace

#endif
