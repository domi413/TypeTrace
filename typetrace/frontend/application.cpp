#include "application.hpp"

#include <gtkmm.h>
#include <print>

namespace typetrace::frontend {

// creates a new button with label "TypeTrace".
Application::Application() : button("TypeTrace")
{

    button.signal_clicked().connect(sigc::mem_fun(*this, &Application::on_button_clicked));

    // This packs the button into the Window (a container).
    set_child(button);
}

auto Application::on_button_clicked() -> void
{
    std::println("TypeTrace Frontend Started!");
}

} // namespace typetrace::frontend
