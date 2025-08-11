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
    EventHandler()
    {
        initializeLibinput();
        checkInputGroupMembership();
        checkDeviceAccessibility();

        last_flush_time = Clock::now();
    };

    auto setBufferCallback(std::function<void(const std::vector<KeystrokeEvent> &)> callback)
      -> void;
    auto trace() -> void;

  private:
    static auto checkInputGroupMembership() -> void;
    static auto printInputGroupPermissionHelp() -> void;
    static auto processKeyboardEvent(struct libinput_event *event) -> std::optional<KeystrokeEvent>;

    auto checkDeviceAccessibility() const -> void;
    auto initializeLibinput() -> void;
    [[nodiscard]] auto shouldFlush() const -> bool;
    auto flushBuffer() -> void;

    std::vector<KeystrokeEvent> buffer;
    Clock::time_point last_flush_time;
    std::function<void(const std::vector<KeystrokeEvent> &)> buffer_callback;

    std::unique_ptr<struct libinput, decltype(&libinput_unref)> li{ nullptr, &libinput_unref };
    std::unique_ptr<struct udev, decltype(&udev_unref)> udev{ nullptr, &udev_unref };
};

} // namespace typetrace

#endif
