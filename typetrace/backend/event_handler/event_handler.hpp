#ifndef TYPETRACE_EVENTHANDLER_HPP
#define TYPETRACE_EVENTHANDLER_HPP

#include "types.hpp"

#include <chrono>
#include <functional>
#include <libinput.h>
#include <libudev.h>
#include <memory>
#include <optional>
#include <vector>

namespace typetrace {

using Clock = std::chrono::steady_clock;

class EventHandler
{
  public:
    /// Constructs an event handler and initializes libinput and device access
    EventHandler()
    {
        initializeLibinput();
        checkInputGroupMembership();
        checkDeviceAccessibility();

        last_flush_time = Clock::now();
    };

    /// Sets the callback function to be called when the buffer needs to be flushed
    auto setBufferCallback(std::function<void(const std::vector<KeystrokeEvent> &)> callback)
      -> void;

    /// Traces keyboard events and processes them into keystroke events
    auto trace() -> void;

  private:
    /// Checks if the current user is a member of the 'input' group
    static auto checkInputGroupMembership() -> void;

    /// Prints help information for input group permission issues
    static auto printInputGroupPermissionHelp() -> void;

    /// Checks if input devices are accessible and functional
    auto checkDeviceAccessibility() const -> void;

    /// Initializes libinput context and assigns seat
    auto initializeLibinput() -> void;

    /// Processes a libinput keyboard event into a keystroke event
    [[nodiscard]] auto processKeyboardEvent(struct libinput_event *event)
      -> std::optional<KeystrokeEvent>;

    /// Determines if the buffer should be flushed based on size and time
    [[nodiscard]] auto shouldFlush() const -> bool;

    /// Flushes the current buffer by calling the buffer callback
    auto flushBuffer() -> void;

    std::vector<KeystrokeEvent> buffer;
    Clock::time_point last_flush_time;

    std::function<void(const std::vector<KeystrokeEvent> &)> buffer_callback;

    std::unique_ptr<struct libinput, decltype(&libinput_unref)> li{ nullptr, &libinput_unref };
    std::unique_ptr<struct udev, decltype(&udev_unref)> udev{ nullptr, &udev_unref };
};

} // namespace typetrace

#endif
