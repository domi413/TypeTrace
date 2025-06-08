/**
 * @file eventhandler.h
 * @brief Event handling interface for keyboard input events
 *
 * This file defines the interface for processing libinput events,
 * specifically focusing on keyboard events that need to be tracked
 * and stored in the database.
 */

#ifndef EVENTHANDLER_H
#define EVENTHANDLER_H

struct libinput;

/**
 * @brief Process libinput events and handle keyboard events
 *
 * This function processes events from the libinput context, specifically
 * filtering for keyboard key press events, and logs them to the database.
 *
 * @param li Pointer to the initialized libinput context
 * @return Error code indicating success (NO_ERROR) or failure
 */
int eh_handle_events(struct libinput *li);

#endif // EVENTHANDLER_H
