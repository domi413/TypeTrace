/// Implementation for permission checking functions

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

/// Structure to hold device detection status
typedef struct device_status
{
    bool has_devices;  ///< True if any input devices were found
    bool has_keyboard; ///< True if keyboard devices were found
} device_status_t;

// ============================================================================
// Static Functions
// ============================================================================

/// Get the current username
static int get_current_username(char *buffer, size_t size)
{
    const char *username = secure_getenv("USER");
    if (!username) {
        username = secure_getenv("USERNAME");
    }

    if (username) {
        if (strlen(username) >= size) {
            return -1;
        }
        buffer[size - 1] = '\0';
        strncpy(buffer, username, size);
        if (buffer[size - 1] != '\0') {
            (void)fprintf(stderr, "Username truncated during copy\n");
            return -1;
        }
        return OK;
    }

    struct passwd pwd;
    struct passwd *pw_result = nullptr;
    char pwd_buffer[MAX_PATH_LENGTH];

    if (getpwuid_r(geteuid(), &pwd, pwd_buffer, sizeof(pwd_buffer), &pw_result)
        == 0
        && pw_result
        != nullptr) {
        if (strlen(pwd.pw_name) >= size) {
            return -1;
        }
        buffer[size - 1] = '\0';
        strncpy(buffer, pwd.pw_name, size);
        if (buffer[size - 1] != '\0') {
            (void)fprintf(stderr, "Username truncated during copy\n");
            return -1;
        }
        return OK;
    }

    return -1;
}

/// Get group information by name
static int get_group_by_name(const char *group_name,
                             struct group *grp,
                             char *buffer,
                             size_t buffer_size,
                             struct group **result)
{
    if (getgrnam_r(group_name, grp, buffer, buffer_size, result)
        != 0
        || *result
        == nullptr) {
        (void)fprintf(
          stderr, "The '%s' group does not exist on this system\n", group_name);
        return -1;
    }
    return OK;
}

/// Get user information by name
static int get_user_by_name(const char *username,
                            struct passwd *pwd,
                            char *buffer,
                            size_t buffer_size,
                            struct passwd **result)
{
    return getpwnam_r(username, pwd, buffer, buffer_size, result)
            == 0
            && *result
            != nullptr
           ? OK
           : -1;
}

/// Check if user is member of a group
static int is_user_in_group(const char *username, const struct group *grp)
{
    // Check if user is in the group's member list
    char **members = grp->gr_mem;
    while (*members) {
        if (strcmp(*members, username) == 0) {
            DEBUG_PRINT("User %s is in the '%s' group\n", username, grp->gr_name);
            return OK;
        }
        members++;
    }

    // Check if user has this group as primary group
    struct passwd user_pwd;
    struct passwd *user_result = nullptr;
    char user_buffer[MAX_PATH_LENGTH];

    if (get_user_by_name(
          username, &user_pwd, user_buffer, sizeof(user_buffer), &user_result)
        == OK
        && user_pwd.pw_gid
        == grp->gr_gid) {
        DEBUG_PRINT("User %s has '%s' as primary group\n", username, grp->gr_name);
        return OK;
    }

    return -1;
}

/// Process a device added event
static void process_device_added_event(struct libinput_event *event,
                                       device_status_t *status)
{
    status->has_devices = true;
    struct libinput_device *device = libinput_event_get_device(event);
    const char *name = libinput_device_get_name(device);

    if (libinput_device_has_capability(device, LIBINPUT_DEVICE_CAP_KEYBOARD)) {
        DEBUG_PRINT("Found keyboard device: %s\n", name);
        status->has_keyboard = true;
    } else {
        DEBUG_PRINT("Found non-keyboard device: %s\n", name);
    }
}

/// Enumerate and check input devices
static int enumerate_devices(struct libinput *li, device_status_t *status)
{
    if (libinput_dispatch(li) < 0) {
        (void)fprintf(stderr, "Failed to dispatch libinput events\n");
        return LIBINPUT_FAILED;
    }

    status->has_devices = false;
    status->has_keyboard = false;

    struct libinput_event *event = nullptr;
    while ((event = libinput_get_event(li)) != nullptr) {
        if (libinput_event_get_type(event) == LIBINPUT_EVENT_DEVICE_ADDED) {
            process_device_added_event(event, status);
        }
        libinput_event_destroy(event);
    }

    return OK;
}

// ============================================================================
// Public Functions
// ============================================================================

/// Check device accessibility
int perm_check_device_accessibility(struct libinput *li)
{
    if (!li) {
        (void)fprintf(stderr, "Invalid libinput context provided\n");
        return LIBINPUT_FAILED;
    }

    device_status_t status = { false, false };

    int result = enumerate_devices(li, &status);
    if (result != OK) {
        return result;
    }

    if (!status.has_devices) {
        (void)fprintf(stderr, "No input devices found\n");
        return NO_DEVICES_ERROR;
    }

    if (!status.has_keyboard) {
        (void)fprintf(stderr, "No keyboard devices found\n");
        return NO_DEVICES_ERROR;
    }

    DEBUG_PRINT("Input devices accessible\n");
    return OK;
}

/// Check if the current user is in the 'input' group
int perm_check_input_group_membership(void)
{
    char username[USERNAME_MAX_LENGTH];
    if (get_current_username(username, sizeof(username)) != OK) {
        (void)fprintf(stderr, "Could not determine username\n");
        return PERMISSION_ERROR;
    }

    DEBUG_PRINT("Username: %s\n", username);

    struct group grp;
    struct group *grp_result = nullptr;
    char grp_buffer[MAX_PATH_LENGTH];

    if (get_group_by_name("input", &grp, grp_buffer, sizeof(grp_buffer), &grp_result)
        != OK) {
        return PERMISSION_ERROR;
    }

    if (is_user_in_group(username, &grp) == OK) {
        return OK;
    }

    (void)fprintf(stderr, "User %s is not in the 'input' group\n", username);
    return PERMISSION_ERROR;
}

/// Print a message explaining permission problems and how to solve them
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
