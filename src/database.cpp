#include "database.hpp"

#include "constants.hpp"
#include "exceptions.hpp"
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

DatabaseManager::DatabaseManager(const std::filesystem::path &db_dir) :
  db_file(db_dir / DB_FILE_NAME)
{
    const auto parent_dir = db_dir.parent_path();
    if (!parent_dir.empty() && !std::filesystem::exists(parent_dir)) {
        std::filesystem::create_directories(parent_dir);
    }

    try {
        db = std::make_unique<SQLite::Database>(db_file.string(),
                                                static_cast<unsigned int>(SQLite::OPEN_READWRITE)
                                                  | static_cast<unsigned int>(SQLite::OPEN_CREATE));
        // WAL mode
        // db->exec(OPTIMIZE_DATABASE_SQL);

        createTables();
    } catch (const SQLite::Exception &e) {
        throw DatabaseError(std::format(
          "Failed to open database '{}': {}", (db_file / DB_FILE_NAME).string(), e.what()));
    }
}

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

    } catch (const SQLite::Exception &e) {
        throw DatabaseError(std::format("Failed to write to database: {}", e.what()));
    }
}

// Error: unable to open database file
auto DatabaseManager::createTables() -> void
{
    try {
        db->exec(CREATE_KEYSTROKES_TABLE_SQL);
    } catch (const SQLite::Exception &e) {
        throw DatabaseError(std::format("Failed to create tables: {}", e.what()));
    }
}

} // namespace typetrace
