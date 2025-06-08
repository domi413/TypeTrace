/**
 * @file database.h
 * @brief Database interface for storing and retrieving keyboard input data
 *
 * This file contains functions for interacting with the SQLite database
 * that stores keystroke data, including inserting new records and
 * updating existing ones.
 */
#ifndef DATABASE_H
#define DATABASE_H

#include <stdint.h>

/**
 * @brief Add a keystroke event to the buffer
 *
 * This function adds a keystroke event to the buffer. If the buffer is full
 * or the timeout has been reached, it flushes the buffer to the database.
 *
 * @param key_code The key code from the input event
 * @param key_name The human-readable name of the key
 * @return 0 on success, error code on failure
 */
int db_add_to_buffer(uint32_t key_code, const char *key_name);

/**
 * @brief Check if buffer should be flushed and flush if needed
 *
 * This function checks if the buffer should be flushed (due to timeout or size)
 * and flushes it to the database if needed.
 *
 * @param force_flush If true, flush the buffer regardless of timeout or size
 * @return 0 on success, error code on failure
 */
int db_check_and_flush_buffer(bool force_flush);

/**
 * @brief Flush and free the keystroke buffer
 *
 * Ensures all remaining keystrokes are written to the database
 * and frees the buffer memory.
 */
void db_cleanup_buffer(void);

/**
 * @brief Initialize the keystroke buffer
 *
 * Allocates and initializes the buffer for storing keystroke events
 * before writing them to the database.
 *
 * @return true on success, false on failure
 */
bool db_init_buffer(void);

#endif // DATABASE_H
