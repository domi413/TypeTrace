#include "application.hpp"

#include <gtkmm/application.h>

auto main(int argc, char *argv[]) -> int
{
    auto app = Gtk::Application::create("org.typetrace.frontend");
    return app->make_window_and_run<typetrace::frontend::Application>(argc, argv);
}
