#include "database.hpp"

#include "sql.hpp"
#include "types.hpp"

#include <SQLiteCpp/Database.h>
#include <SQLiteCpp/Exception.h>
#include <SQLiteCpp/Statement.h>
#include <SQLiteCpp/Transaction.h>
#include <filesystem>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

namespace typetrace {

DatabaseManager::DatabaseManager(const std::filesystem::path &db_path) : db_file(db_path)
{
    auto parent_dir = db_path.parent_path();
    if (!parent_dir.empty() && !std::filesystem::exists(parent_dir)) {
        std::filesystem::create_directories(parent_dir);
    }

    db = std::make_unique<SQLite::Database>(db_path.string(),
                                            static_cast<unsigned int>(SQLite::OPEN_READWRITE)
                                              | static_cast<unsigned int>(SQLite::OPEN_CREATE));

    // WAL mode
    // db->exec(OPTIMIZE_DATABASE_SQL);

    createTables();
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
        throw std::runtime_error("Failed to write to database: " + std::string(e.what()));
    }
}

auto DatabaseManager::createTables() -> void
{
    try {
        db->exec(CREATE_KEYSTROKES_TABLE_SQL);
    } catch (const SQLite::Exception &e) {
        throw std::runtime_error("Failed to create tables: " + std::string(e.what()));
    }
}

} // namespace typetrace
