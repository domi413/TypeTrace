/**
 * @file database.c
 * @brief Implementation of database operations for keystroke logging
 *
 * This file implements functions for storing keystroke data in an SQLite database,
 * with features for creating tables if they don't exist and updating
 * keystroke counts for existing entries. It also implements a buffer system
 * to batch write keystrokes for better performance.
 */

#include "database.h"
#include "common.h"
#include "sql.h"

#include <sqlite3.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

/* Static buffer for keystrokes */
static keystroke_event_t *keystroke_buffer = nullptr;
static int buffer_count = 0;
static struct timespec buffer_start_time;

/* Forward declaration for static function */
static void db_write_buffer_to_database(keystroke_event_t *events, int count);

// ============================================================================
// Static Functions
// ============================================================================

/**
 * @brief Begin an SQLite transaction
 *
 * Helper function to start an SQLite transaction.
 *
 * @param db The database connection
 * @return SQLITE_OK on success, error code on failure
 */
static int db_begin_transaction(sqlite3 *db)
{
    char *err_msg = nullptr;
    const int rc = sqlite3_exec(db, "BEGIN TRANSACTION;", nullptr, nullptr, &err_msg);

    if (rc != SQLITE_OK) {
        (void)fprintf(stderr, "Failed to begin transaction: %s\n", err_msg);
        sqlite3_free(err_msg);
        DEBUG_PRINT("Closing database connection (transaction begin failure).\n");
    }

    return rc;
}

/**
 * @brief Commit an SQLite transaction
 *
 * Helper function to commit an SQLite transaction.
 *
 * @param db The database connection
 * @return SQLITE_OK on success, error code on failure
 */
static int db_commit_transaction(sqlite3 *db)
{
    char *err_msg = nullptr;
    const int rc = sqlite3_exec(db, "COMMIT;", nullptr, nullptr, &err_msg);

    if (rc != SQLITE_OK) {
        (void)fprintf(stderr, "Failed to commit transaction: %s\n", err_msg);
        sqlite3_free(err_msg);
        sqlite3_exec(db, "ROLLBACK;", nullptr, nullptr, nullptr);
    } else {
        DEBUG_PRINT("Transaction committed successfully.\n");
    }

    return rc;
}

/**
 * @brief Execute batch insert of keystroke events
 *
 * Helper function to insert multiple keystroke events using a prepared statement.
 *
 * @param db The database connection
 * @param stmt The prepared statement
 * @param events Array of keystroke events
 * @param count Number of events in the array
 * @return SQLITE_OK on success, error code on failure
 */
static int db_execute_batch_insert(sqlite3 *db,
                                   sqlite3_stmt *stmt,
                                   const keystroke_event_t *events,
                                   const int count)
{
    int rc = SQLITE_OK;

    // Process each event
    for (int i = 0; i < count; i++) {
        sqlite3_bind_int(stmt, 1, events[i].key_code);
        sqlite3_bind_text(stmt, 2, events[i].key_name, -1, SQLITE_STATIC);
        sqlite3_bind_text(stmt, 3, events[i].date, -1, SQLITE_STATIC);

        rc = sqlite3_step(stmt);
        if (rc != SQLITE_DONE) {
            (void)fprintf(
              stderr, "Execution failed for batch UPSERT: %s\n", sqlite3_errmsg(db));
        }

        // Reset statement for next row
        sqlite3_reset(stmt);
    }

    return rc;
}

/**
 * @brief Opens the database and ensures the keystrokes table exists
 *
 * Helper function to open the SQLite database connection and create
 * the keystrokes table if it doesn't exist.
 *
 * @param db Pointer to store the database connection
 * @return SQLITE_OK on success, error code on failure
 */
static int db_open_and_ensure_table(sqlite3 **db)
{
    char *err_msg = nullptr;

    int rc = sqlite3_open(db_file_path, db);
    if (rc != SQLITE_OK) {
        (void)fprintf(stderr, "Cannot open database: %s\n", sqlite3_errmsg(*db));
        return rc;
    }
    DEBUG_PRINT("Opened database successfully.\n");

    rc = sqlite3_exec(*db, CREATE_KEYSTROKES_TABLE_SQL, nullptr, nullptr, &err_msg);
    if (rc != SQLITE_OK) {
        (void)fprintf(stderr, "Failed to create table: %s\n", err_msg);
        sqlite3_free(err_msg);
        DEBUG_PRINT("Closing database connection (error path).\n");
        sqlite3_close(*db);
        return rc;
    }

    return SQLITE_OK;
}

/**
 * @brief Prepare an SQL statement for execution
 *
 * Helper function to prepare an SQLite statement.
 *
 * @param db The database connection
 * @param stmt Pointer to store the prepared statement
 * @return SQLITE_OK on success, error code on failure
 */
static int db_prepare_statement(sqlite3 *db, sqlite3_stmt **stmt)
{
    const int rc = sqlite3_prepare_v2(db, UPSERT_KEYSTROKE_SQL, -1, stmt, nullptr);

    if (rc != SQLITE_OK) {
        (void)fprintf(stderr, "Failed to prepare statement: %s\n", sqlite3_errmsg(db));
        DEBUG_PRINT("Closing database connection (prepare statement failure).\n");
        sqlite3_exec(db, "ROLLBACK;", nullptr, nullptr, nullptr);
    }

    return rc;
}

/**
 * @brief Writes multiple buffered keystroke events to the database
 *
 * This function takes an array of keystroke events and writes them all
 * to the database in a single transaction for better performance.
 *
 * @param events Array of keystroke events
 * @param count Number of events in the array
 */
static void db_write_buffer_to_database(keystroke_event_t *events, const int count)
{
    if (events == nullptr || count <= 0) {
        return;
    }

    sqlite3 *db = nullptr;
    sqlite3_stmt *stmt = nullptr;

    int rc = db_open_and_ensure_table(&db);
    if (rc != SQLITE_OK) {
        return;
    }

    rc = db_begin_transaction(db);
    if (rc != SQLITE_OK) {
        sqlite3_close(db);
        return;
    }

    rc = db_prepare_statement(db, &stmt);
    if (rc != SQLITE_OK) {
        sqlite3_close(db);
        return;
    }

    db_execute_batch_insert(db, stmt, events, count);

    // Cleanup statement
    sqlite3_finalize(stmt);

    rc = db_commit_transaction(db);
    if (rc == SQLITE_OK) {
        DEBUG_PRINT("Successfully wrote %d keystrokes to database in batch.\n", count);
    }

    DEBUG_PRINT("Closing database connection (normal completion).\n");
    sqlite3_close(db);
}

// ============================================================================
// Public Functions
// ============================================================================

/**
 * @brief Add a keystroke event to the buffer
 *
 * Adds a keystroke event to the buffer and checks if the buffer should be flushed.
 *
 * @param key_code The numeric code of the pressed key
 * @param key_name The human-readable name of the key
 * @return 0 on success, error code on failure
 */
int db_add_to_buffer(const uint32_t key_code, const char *key_name)
{
    if (keystroke_buffer == nullptr) {
        if (!db_init_buffer()) {
            return BUFFER_ERROR;
        }
    }

    // Get current date
    const time_t t = time(nullptr);
    if (t == (time_t)-1) {
        (void)fprintf(stderr, "Failed to get current time.\n");
        return BUFFER_ERROR;
    }

    struct tm tm_info;
    if (localtime_r(&t, &tm_info) == NULL) {
        (void)fprintf(stderr, "Failed to get local time.\n");
        return BUFFER_ERROR;
    }

    if (buffer_count < BUFFER_SIZE) {
        // Add keystroke to buffer
        keystroke_event_t *event = &keystroke_buffer[buffer_count];
        event->key_code = key_code;
        strncpy(event->key_name, key_name, sizeof(event->key_name) - 1);
        event->key_name[sizeof(event->key_name) - 1] = '\0';

        if (strftime(event->date, sizeof(event->date), "%Y-%m-%d", &tm_info) == 0) {
            strcpy(event->date, "UNKNOWN");
        }
        buffer_count++;

        DEBUG_PRINT("Added keystroke [%d/%u] to buffer: %s (code %u)\n",
                    buffer_count,
                    BUFFER_SIZE,
                    key_name,
                    key_code);
    } else {
        // Buffer is full, flush it
        return db_check_and_flush_buffer(true);
    }

    // Check if we should flush due to timeout
    return db_check_and_flush_buffer(false);
}

/**
 * @brief Check if buffer should be flushed and flush if needed
 *
 * Checks if the buffer should be flushed due to timeout or size,
 * and flushes it if necessary.
 *
 * @param force_flush If true, flush regardless of timeout or size
 * @return 0 on success, error code on failure
 */
int db_check_and_flush_buffer(const bool force_flush)
{
    // Early exit if buffer is empty
    if (keystroke_buffer == nullptr || buffer_count == 0) {
        return OK; // Nothing to flush
    }

    struct timespec current_time;

    if (clock_gettime(CLOCK_MONOTONIC, &current_time) != 0) {
        perror("clock_gettime failed");
    }
    const double elapsed =
      (current_time.tv_sec - buffer_start_time.tv_sec) +
      ((current_time.tv_nsec - buffer_start_time.tv_nsec) / NANOSECONDS_PER_SECOND);

    if (force_flush || buffer_count >= BUFFER_SIZE || elapsed >= BUFFER_TIMEOUT) {
        DEBUG_PRINT("Flushing buffer with %d keystrokes to %s (elapsed: %.2f seconds)\n",
                    buffer_count,
                    db_file_path,
                    elapsed);

        db_write_buffer_to_database(keystroke_buffer, buffer_count);

        buffer_count = 0;
        if (clock_gettime(CLOCK_MONOTONIC, &buffer_start_time) != 0) {
            perror("clock_gettime failed");
        }
    }

    return OK;
}

/**
 * @brief Flush and free the keystroke buffer
 *
 * Ensures all remaining keystrokes are written to the database
 * and frees the buffer memory.
 */
void db_cleanup_buffer(void)
{
    if (keystroke_buffer != nullptr) {
        // Flush any remaining keystrokes
        db_check_and_flush_buffer(true);

        // Free buffer memory
        free(keystroke_buffer);
        keystroke_buffer = nullptr;
        buffer_count = 0;
        DEBUG_PRINT("Keystroke buffer cleaned up\n");
    }
}

/**
 * @brief Initialize the keystroke buffer
 *
 * Allocates memory for the keystroke buffer and initializes the start time.
 *
 * @return true on success, false on failure
 */
bool db_init_buffer(void)
{
    if (keystroke_buffer == nullptr) {
        keystroke_buffer =
          (keystroke_event_t *)calloc(BUFFER_SIZE, sizeof(keystroke_event_t));

        if (keystroke_buffer == nullptr) {
            (void)fprintf(stderr, "Failed to allocate keystroke buffer\n");
            return false;
        }
        if (clock_gettime(CLOCK_MONOTONIC, &buffer_start_time) != 0) {
            perror("clock_gettime failed");
        }

        buffer_count = 0;

        DEBUG_PRINT("Keystroke buffer initialized with size %u\n", BUFFER_SIZE);
    }
    return true;
}
