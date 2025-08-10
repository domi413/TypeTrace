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
    explicit DatabaseManager(const std::filesystem::path &db_path);

    auto writeToDatabase(const std::vector<KeystrokeEvent> &buffer) -> void;

  private:
    auto createTables() -> void;

    std::filesystem::path db_file;
    std::unique_ptr<SQLite::Database> db;
};

} // namespace typetrace

#endif
