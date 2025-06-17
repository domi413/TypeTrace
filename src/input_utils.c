/// Implementation of utilities for handling libinput device access

#include "input_utils.h"
#include "common.h"

#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

/// Open an input device with restricted access
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

/// Close a previously opened input device
static void close_restricted_impl(const int fd,
                                  const void *user_data __attribute__((unused)))
{
    close(fd);
    DEBUG_PRINT("Closed device (fd: %d)\n", fd);
}

/// libinput interface implementation
const struct libinput_interface INPUT_UTILS_LIBINPUT_INTERFACE = {
    .open_restricted = (int (*)(const char *, int, void *))open_restricted_impl,
    .close_restricted = (void (*)(int, void *))close_restricted_impl,
};
