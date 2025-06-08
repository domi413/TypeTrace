/**
 * @file permission_check.h
 * @brief Functions for checking permissions and device accessibility
 *
 * This header file contains functions for checking if the current user
 * has proper permissions to access input devices, including checking
 * membership in the 'input' group.
 */

#ifndef PERMISSION_CHECK_H
#define PERMISSION_CHECK_H

#include <libinput.h>
#include <stdint.h>

/**
 * @brief Check device accessibility
 *
 * Attempts to list and open input devices to verify they are accessible.
 * This confirms that sufficient permissions exist to read from devices.
 *
 * @param li Initialized libinput context to use for checking devices
 * @return 0 on success (devices can be accessed), NO_DEVICES_ERROR if no devices
 *         are available, PERMISSION_ERROR if devices exist but can't be accessed
 */
int perm_check_device_accessibility(struct libinput *li);

/**
 * @brief Check if the current user is in the 'input' group
 *
 * Verifies if the user running the program is a member of the 'input' group,
 * which is required for accessing input devices on Linux systems.
 *
 * @return 0 on success (user is in the group), PERMISSION_ERROR otherwise
 */
int perm_check_input_group_membership(void);

/**
 * @brief Print a message explaining permission problems and how to solve them
 *
 * Provides user-friendly guidance on how to fix permission issues, e.g.,
 * by adding the user to the 'input' group.
 */
void perm_print_permission_help(void);

#endif /* PERMISSION_CHECK_H */
