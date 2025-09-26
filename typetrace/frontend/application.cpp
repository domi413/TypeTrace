#include "application.hpp"

#include <gtkmm.h>
#include <print>

namespace TypeTrace::Frontend {

// creates a new button with label "TypeTrace".
TypeTraceWindow::TypeTraceWindow() : button("TypeTrace")
{

    // When the button receives the "clicked" signal, it will call the
    // on_button_clicked() method defined below.
    button.signal_clicked().connect(sigc::mem_fun(*this, &TypeTraceWindow::on_button_clicked));

    // This packs the button into the Window (a container).
    set_child(button);
}

void TypeTraceWindow::on_button_clicked()
{
    std::println("TypeTrace Frontend Started!");
}

} // namespace TypeTrace::Frontend
