/**
 * @file input_utils.c
 * @brief Implementation of utilities for handling libinput device access
 *
 * This file implements the libinput interface for opening and closing
 * input devices, handling file descriptors properly.
 */

#include "input_utils.h"
#include "common.h"

#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

/**
 * @brief Open an input device with restricted access
 *
 * Opens the specified device path with the given flags. This function is
 * called by libinput when it needs to access an input device.
 *
 * @param path Path to the device file
 * @param flags Open flags (e.g., O_RDONLY, O_RDWR)
 * @param user_data User data pointer (unused)
 * @return File descriptor on success, negative errno on failure
 */
static int open_restricted_impl(const char *path,
                                const int flags,
                                const void *user_data __attribute__((unused)))
{
    const int fd = open(path, flags);
    if (fd < 0) {
        (void)fprintf(
          stderr, "Failed to open %s (flags %x): %s\n", path, flags, strerror(errno));
        return -errno;
    }
    DEBUG_PRINT("Opened device: %s (fd: %d)\n", path, fd);
    return fd;
}

/**
 * @brief Close a previously opened input device
 *
 * Closes the file descriptor for an input device that was previously opened
 * by open_restricted_impl. This function is called by libinput when it's
 * done with a device.
 *
 * @param fd File descriptor to close
 * @param user_data User data pointer (unused)
 */
static void close_restricted_impl(const int fd,
                                  const void *user_data __attribute__((unused)))
{
    close(fd);
    DEBUG_PRINT("Closed device (fd: %d)\n", fd);
}

/**
 * @brief libinput interface implementation
 *
 * Structure containing function pointers for device access used by libinput.
 */
const struct libinput_interface INPUT_UTILS_LIBINPUT_INTERFACE = {
    .open_restricted = (int (*)(const char *, int, void *))open_restricted_impl,
    .close_restricted = (void (*)(int, void *))close_restricted_impl,
};
