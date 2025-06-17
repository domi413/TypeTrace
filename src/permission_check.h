/// Functions for checking permissions and device accessibility

#ifndef PERMISSION_CHECK_H
#define PERMISSION_CHECK_H

#include <libinput.h>
#include <stdint.h>

/// Check device accessibility
int perm_check_device_accessibility(struct libinput *li);

/// Check if the current user is in the 'input' group
int perm_check_input_group_membership(void);

/// Print a message explaining permission problems and how to solve them
void perm_print_permission_help(void);

#endif /* PERMISSION_CHECK_H */
