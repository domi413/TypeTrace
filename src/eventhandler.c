/// Implementation of keyboard event handling functions
#include "eventhandler.h"
#include "common.h"
#include "database.h"

#include <libevdev-1.0/libevdev/libevdev.h>
#include <libinput.h>
#include <stdio.h>

// ============================================================================
// Static Functions
// ============================================================================

/// Process a keyboard key event
static int eh_process_key_event(struct libinput_event *event)
{
    struct libinput_event_keyboard *keyboard_event
      = libinput_event_get_keyboard_event(event);

    if (!keyboard_event) {
        (void)fprintf(stderr, " Failed to get keyboard event details.\n");
        return -1;
    }

    if (libinput_event_keyboard_get_key_state(keyboard_event)
        != LIBINPUT_KEY_STATE_PRESSED) {
        return OK;
    }

    const uint32_t key_code = libinput_event_keyboard_get_key(keyboard_event);
    const char *key_name = libevdev_event_code_get_name(EV_KEY, key_code);
    key_name = key_name ? key_name : "UNKNOWN";

    const int result = db_add_to_buffer(key_code, key_name);
    if (result != OK) {
        (void)fprintf(stderr, "Failed to add keystroke to buffer: %d\n", result);
        return -1;
    }

    DEBUG_PRINT("{\"key_name\": \"%s\", \"key_code\": %u, \"action\": "
                "\"added to buffer\"}\n",
                key_name,
                key_code);
    return OK;
}

// ============================================================================
// Public Functions
// ============================================================================

/// Handle all pending libinput events
int eh_handle_events(struct libinput *li)
{
    int result = OK;

    // Initialize the buffer on first run
    static bool buffer_initialized = false;
    if (!buffer_initialized) {
        if (!db_init_buffer()) {
            (void)fprintf(stderr, "Failed to initialize keystroke buffer.\n");
            return BUFFER_ERROR;
        }
        buffer_initialized = true;
    }

    if (libinput_dispatch(li) != 0) {
        (void)fprintf(stderr, "Failed to dispatch libinput events.\n");
        return LIBINPUT_FAILED;
    }

    struct libinput_event *event = nullptr;
    while ((event = libinput_get_event(li))) {
        enum libinput_event_type event_type = libinput_event_get_type(event);

        if (event_type == LIBINPUT_EVENT_KEYBOARD_KEY) {
            if (eh_process_key_event(event) < 0) {
                result = LIBINPUT_FAILED;
            }
        }
        libinput_event_destroy(event);
    }

    // Check if we need to flush the buffer due to timeout
    const int flush_result = db_check_and_flush_buffer(false);
    if (flush_result != OK) {
        (void)fprintf(stderr, "Error while checking buffer flush: %d\n", flush_result);
        if (result == OK) {
            result = flush_result;
        }
    }

    return result;
}
