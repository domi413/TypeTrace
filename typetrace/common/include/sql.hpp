#ifndef TYPETRACE_SQL_HPP
#define TYPETRACE_SQL_HPP

namespace typetrace {

// ============================================================================
// INSERT Queries
// ============================================================================

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

/// SQL query to clear all entries from the keystrokes table
constexpr const char *CLEAR_KEYSTROKES_TABLE_SQL = "DELETE FROM keystrokes;";

// ============================================================================
// READ Queries
// ============================================================================

/// SQL query to get the total count for each key
///
/// Example output:
///
/// scan_code  total_presses
/// ---------  -------------
/// 1          10
/// 3          19
/// 11         12
constexpr const char *GET_TOTAL_KEY_COUNTS_SQL = {
    R"(SELECT scan_code, SUM(count) AS total_presses
       FROM keystrokes
       GROUP BY scan_code
       ORDER BY scan_code ASC;)"
};

/// SQL query to get the daily amount of key presses over the last X days
///
/// Example output:
///
/// date        daily_total
/// ----------  -----------
/// 2025-09-20  28
/// 2025-09-19  43
/// 2025-09-18  58
constexpr const char *GET_DAILY_COUNTS_SQL = {
    R"(SELECT date, SUM(count) AS daily_total
       FROM keystrokes
       WHERE date BETWEEN date('now', '-' || ? || ' days') AND date('now', 'localtime')
       GROUP BY date
       ORDER BY date DESC;)"
};

/// SQL query to get the top N most pressed keys in last X days
///
/// Example output:
///
/// scan_code  total_presses
/// ---------  -------------
/// 48         97
/// 75         87
/// 27         85
constexpr const char *GET_TOP_KEYS_SQL = {
    R"(SELECT scan_code, SUM(count) AS total_presses
       FROM keystrokes
       WHERE date >= date('now', 'localtime', '-' || ? || ' days')
       GROUP BY scan_code
       ORDER BY total_presses DESC
       LIMIT ?;)"
};

} // namespace typetrace

#endif // SQL_H
