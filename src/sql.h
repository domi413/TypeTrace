/// SQL query definitions for the TypeTrace database

#ifndef SQL_H
#define SQL_H

/// SQL query to create the keystrokes table if it doesn't exist
static constexpr char CREATE_KEYSTROKES_TABLE_SQL[]
  = "CREATE TABLE IF NOT EXISTS keystrokes ("
    "    id INTEGER PRIMARY KEY AUTOINCREMENT,"
    "    scan_code INTEGER NOT NULL,"
    "    key_name TEXT NOT NULL,"
    "    date DATE NOT NULL,"
    "    count INTEGER DEFAULT 0,"
    "    UNIQUE(scan_code, date)"
    ");";

/// SQL query for inserting or updating keystroke data (UPSERT)
static constexpr char UPSERT_KEYSTROKE_SQL[]
  = "INSERT INTO keystrokes (scan_code, key_name, date, count) "
    "VALUES (?, ?, ?, 1) "
    "ON CONFLICT(scan_code, date) DO UPDATE SET "
    "    count = count + 1, "
    "    key_name = excluded.key_name;";

#endif // SQL_H
