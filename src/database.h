/// Database interface for storing and retrieving keyboard input data
#ifndef DATABASE_H
#define DATABASE_H

#include <stdint.h>

/// Add a keystroke event to the buffer
int db_add_to_buffer(uint32_t key_code, const char *key_name);

/// Check if buffer should be flushed and flush if needed
int db_check_and_flush_buffer(bool force_flush);

/// Flush and free the keystroke buffer
void db_cleanup_buffer(void);

/// Initialize the keystroke buffer
bool db_init_buffer(void);

#endif // DATABASE_H
