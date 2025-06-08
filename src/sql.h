/**
 * @file sql.h
 * @brief SQL query definitions for the TypeTrace database
 *
 * This file contains SQL query strings used for creating tables,
 * inserting data, and updating existing records in the SQLite database.
 */

#ifndef SQL_H
#define SQL_H

/**
 * @brief SQL query to create the keystrokes table if it doesn't exist
 *
 * Creates a table with columns for ID, scan code, key name, date, and count,
 * with a unique constraint on scan_code and date.
 */
static constexpr char CREATE_KEYSTROKES_TABLE_SQL[] =
  "CREATE TABLE IF NOT EXISTS keystrokes ("
  "    id INTEGER PRIMARY KEY AUTOINCREMENT,"
  "    scan_code INTEGER NOT NULL,"
  "    key_name TEXT NOT NULL,"
  "    date DATE NOT NULL,"
  "    count INTEGER DEFAULT 0,"
  "    UNIQUE(scan_code, date)"
  ");";

/**
 * @brief SQL query for inserting or updating keystroke data
 *
 * Uses SQLite's "INSERT OR ... ON CONFLICT" syntax to either insert a new
 * record or update an existing one by incrementing the count.
 */
static constexpr char UPSERT_KEYSTROKE_SQL[] =
  "INSERT INTO keystrokes (scan_code, key_name, date, count) "
  "VALUES (?, ?, ?, 1) "
  "ON CONFLICT(scan_code, date) DO UPDATE SET "
  "    count = count + 1, "
  "    key_name = excluded.key_name;";

#endif // SQL_H
