#include "eventhandler.hpp"

#include "constants.hpp"
#include "exceptions.hpp"
#include "logger.hpp"
#include "spdlog/common.h"
#include "types.hpp"

#include <algorithm>
#include <cerrno>
#include <chrono>
#include <cstdlib>
#include <cstring>
#include <fcntl.h>
#include <format>
#include <functional>
#include <grp.h>
#include <libevdev-1.0/libevdev/libevdev.h>
#include <libinput.h>
#include <libudev.h>
#include <linux/input-event-codes.h>
#include <optional>
#include <poll.h>
#include <print>
#include <string_view>
#include <sys/poll.h>
#include <sys/types.h>
#include <system_error>
#include <unistd.h>
#include <utility>
#include <vector>

namespace typetrace {

/// Sets the callback function to be called when the buffer needs to be flushed
auto EventHandler::setBufferCallback(
  std::function<void(const std::vector<KeystrokeEvent> &)> callback) -> void
{
    buffer_callback = std::move(callback);
}

/// Traces keyboard events and processes them into keystroke events
auto EventHandler::trace() -> void
{
    struct pollfd pfd = { .fd = libinput_get_fd(li.get()), .events = POLLIN, .revents = 0 };

    const int result = poll(&pfd, 1, POLL_TIMEOUT_MS);

    if (result < 0) {
        getLogger()->error("Poll failed with error: {}",
                           std::error_code(errno, std::generic_category()));
        return;
    }

    if (result > 0 && POLLIN & pfd.revents) {
        libinput_dispatch(li.get());

        // Process all available events
        struct libinput_event *event = nullptr;
        while ((event = libinput_get_event(li.get())) != nullptr) {
            if (libinput_event_get_type(event) == LIBINPUT_EVENT_KEYBOARD_KEY) {
                if (const auto keystroke = processKeyboardEvent(event)) {
                    buffer.push_back(*keystroke);
                }
            }

            libinput_event_destroy(event);
        }
    }

    if (shouldFlush()) {
        flushBuffer();
    }
}

/// Checks if the current user is a member of the 'input' group
auto EventHandler::checkInputGroupMembership() -> void
{
    getLogger()->info("Checking for 'input' group membership...");

    struct group const *const input_group = getgrnam("input");
    if (input_group == nullptr) {
        getLogger()->critical("Input group does not exist. Please create it.");
        throw SystemError("Input group does not exist. Please create it.");
    }

    const gid_t input_gid = input_group->gr_gid;

    const int ngroups = getgroups(0, nullptr);
    std::vector<gid_t> groups(static_cast<std::size_t>(ngroups));
    getgroups(ngroups, groups.data());

    if (!(std::ranges::find(groups, input_gid) != groups.end())) {
        getLogger()->error("User is not a member of the 'input' group.");
        printInputGroupPermissionHelp();
        throw PermissionError("User not in 'input' group. See instructions above.");
    }

    getLogger()->info("User is a member of the 'input' group.");
}

/// Prints help information for input group permission issues
auto EventHandler::printInputGroupPermissionHelp() -> void
{
    std::println(stderr, R"(
===================== Permission Error =====================
TypeTrace requires access to input devices to function.

To grant access, add your user to the 'input' group:
    sudo usermod -a -G input $USER

Then log out and log back in for the changes to take effect.
============================================================
)");
}

/// Checks if input devices are accessible and functional
auto EventHandler::checkDeviceAccessibility() const -> void
{
    getLogger()->info("Checking for device accessibility...");

    if (li == nullptr) {
        getLogger()->critical("Libinput is not initialized. Cannot check device accessibility.");
        throw SystemError("Libinput is not initialized. Cannot check device accessibility.");
    }

    if (libinput_dispatch(li.get()) < 0) {
        getLogger()->critical("Failed to dispatch libinput events.");
        throw SystemError("Failed to dispatch libinput events.");
    }

    struct libinput_event *event = libinput_get_event(li.get());
    if ((event == nullptr) || libinput_event_get_type(event) != LIBINPUT_EVENT_DEVICE_ADDED) {
        getLogger()->critical("No input devices found or not accessible.");
        throw SystemError("No input devices found or not accessible.");
    }

    getLogger()->info("Input devices are accessible.");
    libinput_event_destroy(event);
}

/// Initializes libinput context and assigns seat
auto EventHandler::initializeLibinput() -> void
{
    getLogger()->info("Initializing libinput context...");

    static const struct libinput_interface interface = {
        .open_restricted = [](const char *const path, const int flags, void *) -> int {
            return ::open(path, flags);
        },
        .close_restricted = [](const int fd, void *) { ::close(fd); }
    };

    // Initialize udev
    udev.reset(udev_new());
    if (udev == nullptr) {
        getLogger()->critical("Failed to initialize udev.");
        throw SystemError("Failed to initialize udev.");
    }

    // Initialize libinput
    li.reset(libinput_udev_create_context(&interface, nullptr, udev.get()));
    if (li == nullptr) {
        getLogger()->critical("Failed to initialize libinput from udev.");
        throw SystemError("Failed to initialize libinput from udev.");
    }

    // Assign seat0
    if (libinput_udev_assign_seat(li.get(), "seat0") < 0) {
        getLogger()->critical("Failed to assign seat to libinput.");
        throw SystemError("Failed to assign seat to libinput.");
    }

    getLogger()->info("Libinput initialized successfully.");
}

/// Processes a libinput keyboard event into a keystroke event
auto EventHandler::processKeyboardEvent(struct libinput_event *const event)
  -> std::optional<KeystrokeEvent>
{
    auto *keyboard_event = libinput_event_get_keyboard_event(event);
    if (keyboard_event == nullptr) {
        getLogger()->warn("Failed to get keyboard event from libinput event.");
        return std::nullopt;
    }

    // Ignore releases, only process key presses
    if (libinput_event_keyboard_get_key_state(keyboard_event) != LIBINPUT_KEY_STATE_PRESSED) {
        return std::nullopt;
    }

    const auto key_code = libinput_event_keyboard_get_key(keyboard_event);
    const char *const raw_name = libevdev_event_code_get_name(EV_KEY, key_code);
    const std::string_view key_name = (raw_name != nullptr) ? raw_name : "UNKNOWN";

    KeystrokeEvent keystroke{
        .key_code = key_code,
        .key_name = {},
        .date = {},
    };

    const auto copy_size = std::min(key_name.size(), keystroke.key_name.size() - 1);
    std::copy_n(key_name.begin(), copy_size, keystroke.key_name.begin());
    *(keystroke.key_name.begin() + copy_size) = '\0';

    const auto now = std::chrono::system_clock::now();
    const auto date_str
      = std::format("{:%Y-%m-%d}", std::chrono::zoned_time{ std::chrono::current_zone(), now });
    std::copy_n(date_str.begin(),
                std::min(date_str.size(), keystroke.date.size() - 1),
                keystroke.date.begin());

    if (getLogger()->should_log(spdlog::level::debug)) {
        getLogger()->debug("Added keystroke [{}/{}] to buffer: {} (code: {})",
                           buffer.size(),
                           BUFFER_SIZE,
                           keystroke.key_name.data(),
                           key_code);
    }

    return keystroke;
}

/// Determines if the buffer should be flushed based on size and time
auto EventHandler::shouldFlush() const -> bool
{
    if (buffer.size() >= BUFFER_SIZE) {
        return true;
    }

    if (!buffer.empty()) {
        const auto elapsed = Clock::now() - last_flush_time;

        if (elapsed >= std::chrono::seconds(BUFFER_TIMEOUT)) {
            getLogger()->debug("Flushing buffer: time threshold reached ({}s elapsed).",
                               BUFFER_TIMEOUT);
            return true;
        }
    }

    return false;
}

/// Flushes the current buffer by calling the buffer callback
auto EventHandler::flushBuffer() -> void
{
    if (buffer.empty()) {
        return;
    }

    if (buffer_callback) {
        getLogger()->info("Flushing buffer with {} events to database.", buffer.size());
        buffer_callback(buffer);
    }

    buffer.clear();
    last_flush_time = Clock::now();
}

} // namespace typetrace
