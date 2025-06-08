/**
 * @file input_utils.h
 * @brief Utilities for handling libinput device access
 *
 * This file provides the interface structure for libinput to access
 * input devices with proper file descriptor management.
 */

#ifndef INPUT_UTILS_H
#define INPUT_UTILS_H

#include <libinput.h>

/**
 * @brief libinput interface for restricted device access
 *
 * This structure contains function pointers for opening and closing
 * input devices, which requires special privileges. These functions
 * are used by libinput to access input devices.
 */
extern const struct libinput_interface INPUT_UTILS_LIBINPUT_INTERFACE;

#endif // INPUT_UTILS_H
