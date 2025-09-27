#include "event_handler.hpp"

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
#include <sys/poll.h>
#include <sys/types.h>
#include <unistd.h>
#include <utility>
#include <vector>

namespace typetrace::backend {

auto EventHandler::setBufferCallback(
  std::function<void(const std::vector<KeystrokeEvent> &)> callback) -> void
{
    buffer_callback = std::move(callback);
}

auto EventHandler::trace() -> void
{
    struct pollfd pfd = { .fd = libinput_get_fd(li.get()), .events = POLLIN, .revents = 0 };

    const int result = poll(&pfd, 1, POLL_TIMEOUT_MS);

    if (result < 0) {
        getLogger()->error("Poll failed with error: {}", std::strerror(errno));
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

auto EventHandler::checkInputGroupMembership() -> void
{
    getLogger()->info("Checking for 'input' group membership...");

    struct group const *const input_group = getgrnam("input");
    if (input_group == nullptr) {
        throw SystemError("Input group does not exist. Please create it");
    }

    const gid_t input_gid = input_group->gr_gid;

    const int ngroups = getgroups(0, nullptr);
    std::vector<gid_t> groups(static_cast<std::size_t>(ngroups));
    getgroups(ngroups, groups.data());

    if (!(std::ranges::find(groups, input_gid) != groups.end())) {
        printInputGroupPermissionHelp();
        throw PermissionError("User not in 'input' group. See instructions above");
    }

    getLogger()->info("User is a member of the 'input' group");
}

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

auto EventHandler::checkDeviceAccessibility() const -> void
{
    getLogger()->info("Checking for device accessibility...");

    if (li == nullptr) {
        throw SystemError("Libinput is not initialized. Cannot check device accessibility");
    }

    if (libinput_dispatch(li.get()) < 0) {
        throw SystemError("Failed to dispatch libinput events");
    }

    struct libinput_event *event = libinput_get_event(li.get());
    if ((event == nullptr) || libinput_event_get_type(event) != LIBINPUT_EVENT_DEVICE_ADDED) {
        throw SystemError("No input devices found or not accessible");
    }

    getLogger()->info("Input devices are accessible");
    libinput_event_destroy(event);
}

auto EventHandler::initializeLibinput() -> void
{
    getLogger()->info("Initializing libinput context...");

    static const struct libinput_interface interface = {
        .open_restricted = [](const char *const path, const int flags, void *) -> int {
            return ::open(path, flags);
        },
        .close_restricted = [](const int fd, void *) -> void { ::close(fd); }
    };

    // Initialize udev
    udev.reset(udev_new());
    if (udev == nullptr) {
        throw SystemError("Failed to initialize udev");
    }

    // Initialize libinput
    li.reset(libinput_udev_create_context(&interface, nullptr, udev.get()));
    if (li == nullptr) {
        throw SystemError("Failed to initialize libinput from udev");
    }

    // Assign seat0
    if (libinput_udev_assign_seat(li.get(), "seat0") < 0) {
        throw SystemError("Failed to assign seat to libinput");
    }

    getLogger()->info("Libinput initialized successfully");
}

auto EventHandler::processKeyboardEvent(struct libinput_event *const event)
  -> std::optional<KeystrokeEvent>
{
    auto *keyboard_event = libinput_event_get_keyboard_event(event);
    if (keyboard_event == nullptr) {
        getLogger()->warn("Failed to get keyboard event from libinput event");
        return std::nullopt;
    }

    // Ignore releases, only process key presses
    if (libinput_event_keyboard_get_key_state(keyboard_event) != LIBINPUT_KEY_STATE_PRESSED) {
        return std::nullopt;
    }

    const auto key_code = libinput_event_keyboard_get_key(keyboard_event);
    const char *const raw_name = libevdev_event_code_get_name(EV_KEY, key_code);
    const auto time_now = std::chrono::system_clock::now();

    KeystrokeEvent keystroke{
        .key_code = key_code,
        .key_name = (raw_name != nullptr) ? raw_name : "UNKNOWN",
        .date = std::format("{:%Y-%m-%d}",
                            std::chrono::zoned_time{ std::chrono::current_zone(), time_now }),
    };

    getLogger()->debug("Added keystroke [{}/{}] to buffer: {} (code: {})",
                       buffer.size() + 1,
                       BUFFER_SIZE,
                       keystroke.key_name.data(),
                       key_code);

    return keystroke;
}

auto EventHandler::shouldFlush() const -> bool
{
    if (buffer.size() >= BUFFER_SIZE) {
        getLogger()->debug("Flushing buffer: size threshold reached ({} events)", buffer.size());
        return true;
    }

    if (!buffer.empty()) {
        const auto elapsed_duration = Clock::now() - last_flush_time;

        if (elapsed_duration >= std::chrono::seconds(BUFFER_TIMEOUT)) {
            getLogger()->debug("Flushing buffer: time threshold reached ({}s elapsed)",
                               BUFFER_TIMEOUT);
            return true;
        }
    }

    return false;
}

auto EventHandler::flushBuffer() -> void
{
    if (buffer.empty()) {
        return;
    }

    if (buffer_callback) {
        const auto elapsed_seconds = std::chrono::duration_cast<std::chrono::duration<double>>(
                                       Clock::now() - last_flush_time)
                                       .count();
        getLogger()->debug(
          "Flushing buffer with {} events in {:.2f}s to database", buffer.size(), elapsed_seconds);

        buffer_callback(buffer);
    }

    buffer.clear();
    last_flush_time = Clock::now();
}

} // namespace typetrace::backend
