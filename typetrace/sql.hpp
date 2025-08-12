#ifndef TYPETRACE_SQL_HPP
#define TYPETRACE_SQL_HPP

namespace typetrace {

/// SQL query to create the keystrokes table if it doesn't exist
constexpr const char *CREATE_KEYSTROKES_TABLE_SQL = {
    R"(CREATE TABLE IF NOT EXISTS keystrokes (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           scan_code INTEGER NOT NULL,
           key_name TEXT NOT NULL,
           date DATE NOT NULL,
           count INTEGER DEFAULT 0,
           UNIQUE(scan_code, date)
       );)"
};

/// Database optimization pragmas
constexpr const char *OPTIMIZE_DATABASE_SQL =
  R"(PRAGMA journal_mode=WAL;
       PRAGMA synchronous=NORMAL;
       PRAGMA cache_size=10000;
       PRAGMA temp_store=memory;)";

/// SQL query for inserting or updating keystroke data (UPSERT)
constexpr const char *UPSERT_KEYSTROKE_SQL = {
    R"(INSERT INTO keystrokes (scan_code, key_name, date, count)
       VALUES (?, ?, ?, 1)
       ON CONFLICT(scan_code, date) DO UPDATE SET
           count = count + 1,
           key_name = excluded.key_name;)"
};

} // namespace typetrace

#endif // SQL_H
