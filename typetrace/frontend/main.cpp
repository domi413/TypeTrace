#include "application.hpp"

#include <gtkmm/application.h>

int main(int argc, char *argv[])
{
    auto app = Gtk::Application::create("org.typetrace.frontend");
    return app->make_window_and_run<TypeTrace::Frontend::TypeTraceWindow>(argc, argv);
}
