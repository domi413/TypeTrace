#include "database.hpp"

#include "constants.hpp"
#include "exceptions.hpp"
#include "logger.hpp"
#include "spdlog/common.h"
#include "sql.hpp"
#include "types.hpp"

#include <SQLiteCpp/Database.h>
#include <SQLiteCpp/Exception.h>
#include <SQLiteCpp/Statement.h>
#include <SQLiteCpp/Transaction.h>
#include <filesystem>
#include <format>
#include <memory>
#include <vector>

namespace typetrace {

/// Constructs a database manager and initializes the database connection
DatabaseManager::DatabaseManager(const std::filesystem::path &db_dir) :
  db_file(db_dir / DB_FILE_NAME)
{
    getLogger()->info("Initializing database at: {}", db_file.string());

    if (!db_dir.empty() && !std::filesystem::exists(db_dir)) {
        getLogger()->debug("Creating parent directories for database path: {}", db_dir.string());
        std::filesystem::create_directories(db_dir);
    }

    try {
        db = std::make_unique<SQLite::Database>(db_file.string(),
                                                static_cast<unsigned int>(SQLite::OPEN_READWRITE)
                                                  | static_cast<unsigned int>(SQLite::OPEN_CREATE));
        // WAL mode
        // db->exec(OPTIMIZE_DATABASE_SQL);

        createTables();
        getLogger()->info("Database tables created successfully");
    } catch (const SQLite::Exception &e) {
        getLogger()->critical("Failed to open database '{}': {}", db_file.string(), e.what());
        throw DatabaseError(
          std::format("Failed to open database '{}': {}", db_file.string(), e.what()));
    }
}

/// Writes a buffer of keystroke events to the database
auto DatabaseManager::writeToDatabase(const std::vector<KeystrokeEvent> &buffer) -> void
{
    if (buffer.empty()) {
        return;
    }

    try {
        const SQLite::Transaction transaction(*db);
        SQLite::Statement stmt(*db, UPSERT_KEYSTROKE_SQL);

        for (const auto &event : buffer) {
            stmt.bind(1, static_cast<int>(event.key_code));
            stmt.bind(2, event.key_name.data());
            stmt.bind(3, event.date.data());

            stmt.exec();
            stmt.reset();
        }

        getLogger()->debug(
          "Inserted {} keystrokes into the database: {}", buffer.size(), db_file.string());
    } catch (const SQLite::Exception &e) {
        getLogger()->error("Failed to write to database: {}", e.what());
        throw DatabaseError(std::format("Failed to write to database: {}", e.what()));
    }
}

/// Creates necessary database tables if they don't exist
auto DatabaseManager::createTables() -> void
{
    try {
        db->exec(CREATE_KEYSTROKES_TABLE_SQL);
    } catch (const SQLite::Exception &e) {
        getLogger()->error("Failed to create tables: {}", e.what());
        throw DatabaseError(std::format("Failed to create tables: {}", e.what()));
    }
}

} // namespace typetrace
