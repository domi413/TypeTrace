/**
 * @file permission_check.c
 * @brief Implementation for permission checking functions
 *
 * This file implements functions for checking if the current user has the
 * necessary permissions to access input devices, specifically checking
 * membership in the 'input' group and verifying device accessibility.
 */

#include "permission_check.h"
#include "common.h"

#include <grp.h>
#include <libinput.h>
#include <pwd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>

// ============================================================================
// Public Functions
// ============================================================================

/**
 * @brief Check device accessibility
 *
 * Attempts to enumerate input devices to verify they are accessible.
 * This confirms that sufficient permissions exist to read from devices.
 *
 * @param li Initialized libinput context to use for checking devices
 * @return OK on success (devices can be accessed), NO_DEVICES_ERROR if no devices
 *         are available, PERMISSION_ERROR if devices exist but can't be accessed
 */
int perm_check_device_accessibility(struct libinput *li)
{
    if (!li) {
        (void)fprintf(stderr, "Invalid libinput context provided\n");
        return LIBINPUT_FAILED;
    }

    // Force dispatch to enumerate devices
    if (libinput_dispatch(li) < 0) {
        (void)fprintf(stderr, "Failed to dispatch libinput events\n");
        return LIBINPUT_FAILED;
    }

    // Check if at least one keyboard device was found
    bool has_devices = false;
    bool has_keyboard = false;
    struct libinput_device *device = nullptr;

    struct libinput_event *event = nullptr;

    // Process events and check for devices
    while ((event = libinput_get_event(li)) != nullptr) {
        if (libinput_event_get_type(event) == LIBINPUT_EVENT_DEVICE_ADDED) {
            has_devices = true;
            device = libinput_event_get_device(event);
            const char *name = libinput_device_get_name(device);

            // Check if this is a keyboard device
            if (libinput_device_has_capability(device, LIBINPUT_DEVICE_CAP_KEYBOARD)) {
                DEBUG_PRINT("Found keyboard device: %s\n", name);
                has_keyboard = true;
            } else {
                DEBUG_PRINT("Found non-keyboard device: %s\n", name);
            }
        }
        libinput_event_destroy(event);
    }

    if (!has_devices) {
        (void)fprintf(stderr, "No input devices found\n");
        return NO_DEVICES_ERROR;
    }

    if (!has_keyboard) {
        (void)fprintf(stderr, "No keyboard devices found\n");
        return NO_DEVICES_ERROR;
    }

    DEBUG_PRINT("Input devices accessible\n");
    return OK;
}

/**
 * @brief Check if the current user is in the 'input' group
 *
 * Verifies if the user running the program is a member of the 'input' group,
 * which is required for accessing input devices on Linux systems.
 *
 * @return OK on success (user is in the group), PERMISSION_ERROR otherwise
 */
int perm_check_input_group_membership(void)
{
    char *username = nullptr;
    struct passwd pwd;
    struct passwd *pw_result = nullptr;

    username = secure_getenv("USER");
    if (!username) {
        username = secure_getenv("USERNAME");
    }

    if (!username) {
        char pwd_buffer[MAX_PATH_LENGTH];
        if (getpwuid_r(geteuid(), &pwd, pwd_buffer, sizeof(pwd_buffer), &pw_result) ==
              0 &&
            pw_result != NULL) {
            username = pwd.pw_name;
        }
    }

    if (!username) {
        (void)fprintf(stderr, "Could not determine username\n");
        return PERMISSION_ERROR;
    }

    DEBUG_PRINT("Username: %s\n", username);

    struct group grp;
    struct group *grp_result = nullptr;
    char grp_buffer[MAX_PATH_LENGTH];

    if (getgrnam_r("input", &grp, grp_buffer, sizeof(grp_buffer), &grp_result) != 0 ||
        grp_result == nullptr) {
        (void)fprintf(stderr, "The 'input' group does not exist on this system\n");
        return PERMISSION_ERROR;
    }

    // Check if the user is in the input group
    char **members = grp.gr_mem;
    while (*members) {
        if (strcmp(*members, username) == 0) {
            DEBUG_PRINT("User %s is in the 'input' group\n", username);
            return OK;
        }
        members++;
    }

    struct passwd user_pwd;
    struct passwd *user_result = nullptr;
    char user_buffer[MAX_PATH_LENGTH];

    if (getpwnam_r(username, &user_pwd, user_buffer, sizeof(user_buffer), &user_result) ==
          0 &&
        user_result != nullptr) {
        if (user_pwd.pw_gid == grp.gr_gid) {
            DEBUG_PRINT("User %s has 'input' as primary group\n", username);
            return OK;
        }
    }

    (void)fprintf(stderr, "User %s is not in the 'input' group\n", username);
    return PERMISSION_ERROR;
}

/**
 * @brief Print a message explaining permission problems and how to solve them
 *
 * Provides user-friendly guidance on how to fix permission issues, e.g.,
 * by adding the user to the 'input' group.
 */
void perm_print_permission_help(void)
{
    (void)fprintf(stderr, "\n======= Permission Error =======\n");
    (void)fprintf(stderr, "TypeTrace requires access to input devices to function.\n\n");
    (void)fprintf(stderr, "To grant access, add your user to the 'input' group:\n");
    (void)fprintf(stderr, "    sudo usermod -a -G input $USER\n\n");
    (void)fprintf(stderr,
                  "Then log out and log back in for the changes to take effect.\n");
    (void)fprintf(stderr, "=============================\n\n");
}
