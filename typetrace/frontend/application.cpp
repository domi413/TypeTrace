#include "application.hpp"

#include <print>
#include <sigc++-3.0/sigc++/functors/mem_fun.h>

namespace typetrace::frontend {

Application::Application() : button("TypeTrace")
{

    button.signal_clicked().connect(sigc::mem_fun(*this, &Application::onButtonClicked));

    // This packs the button into the Window (a container).
    set_child(button);
}

// NOLINTNEXTLINE(readability-convert-member-functions-to-static)
auto Application::onButtonClicked() -> void
{
    std::println("TypeTrace Frontend Started!");
}

} // namespace typetrace::frontend
