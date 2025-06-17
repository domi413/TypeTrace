/// Implementation of database operations for keystroke logging

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

// ============================================================================
// Static Functions
// ============================================================================

/// Begin an SQLite transaction
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

/// Commit an SQLite transaction
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

/// Execute batch insert of keystroke events
static int db_execute_batch_insert(sqlite3 *db,
                                   sqlite3_stmt *stmt,
                                   const keystroke_event_t *events,
                                   const int count)
{
    int rc = SQLITE_OK;

    // Process each event
    for (int i = 0; i < count; i++) {
        sqlite3_bind_int(stmt, 1, (int)events[i].key_code);
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

/// Opens the database and ensures the keystrokes table exists
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

/// Prepare an SQL statement for execution
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

/// Writes multiple buffered keystroke events to the database
static void db_write_buffer_to_database(const keystroke_event_t *events, const int count)
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

/// Get current time information
static int get_current_time_info(struct tm *tm_info)
{
    const time_t t = time(nullptr);
    if (t == (time_t)-1) {
        (void)fprintf(stderr, "Failed to get current time.\n");
        return BUFFER_ERROR;
    }

    if (localtime_r(&t, tm_info) == nullptr) {
        (void)fprintf(stderr, "Failed to get local time.\n");
        return BUFFER_ERROR;
    }

    return OK;
}

/// Set date string for keystroke event
static void set_event_date(keystroke_event_t *event, const struct tm *tm_info)
{
    if (strftime(event->date, sizeof(event->date), "%Y-%m-%d", tm_info) == 0) {
        // Use snprintf for safe string handling with guaranteed null termination
        int result = snprintf(event->date, sizeof(event->date), "UNKNOWN");
        if (result >= (int)sizeof(event->date)) {
            // Fallback if even "UNKNOWN" doesn't fit
            (void)snprintf(event->date, sizeof(event->date), "ERR");
        }
    }
}

/// Add keystroke to buffer
static int add_keystroke_to_buffer(uint32_t key_code,
                                   const char *key_name,
                                   const struct tm *tm_info)
{
    keystroke_event_t *event = &keystroke_buffer[buffer_count];
    event->key_code = key_code;

    if (snprintf(event->key_name, sizeof(event->key_name), "%s", key_name)
        >= (int)sizeof(event->key_name)) {
        DEBUG_PRINT("Key name truncated: %s\n", key_name);
    }

    set_event_date(event, tm_info);
    buffer_count++;

    DEBUG_PRINT("Added keystroke [%d/%u] to buffer: %s (code %u)\n",
                buffer_count,
                BUFFER_SIZE,
                key_name,
                key_code);

    return OK;
}

// ============================================================================
// Public Functions
// ============================================================================

/// Add a keystroke event to the buffer
int db_add_to_buffer(const uint32_t key_code, const char *key_name)
{
    if (keystroke_buffer == nullptr && !db_init_buffer()) {
        return BUFFER_ERROR;
    }

    struct tm tm_info;
    int result = get_current_time_info(&tm_info);
    if (result != OK) {
        return result;
    }

    if (buffer_count < BUFFER_SIZE) {
        add_keystroke_to_buffer(key_code, key_name, &tm_info);
    } else {
        // Buffer is full, flush it
        return db_check_and_flush_buffer(true);
    }

    // Check if we should flush due to timeout
    return db_check_and_flush_buffer(false);
}

/// Check if buffer should be flushed and flush if needed
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
    const double elapsed = (double)(current_time.tv_sec - buffer_start_time.tv_sec)
                         + ((double)(current_time.tv_nsec - buffer_start_time.tv_nsec)
                            / NANOSECONDS_PER_SECOND);

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

/// Flush and free the keystroke buffer
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

/// Initialize the keystroke buffer
bool db_init_buffer(void)
{
    if (keystroke_buffer == nullptr) {
        keystroke_buffer
          = (keystroke_event_t *)calloc(BUFFER_SIZE, sizeof(keystroke_event_t));

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
