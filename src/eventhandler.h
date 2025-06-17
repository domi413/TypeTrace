/// Event handling interface for keyboard input events

#ifndef EVENTHANDLER_H
#define EVENTHANDLER_H

struct libinput;

/// Process libinput events and handle keyboard events
int eh_handle_events(struct libinput *li);

#endif // EVENTHANDLER_H
