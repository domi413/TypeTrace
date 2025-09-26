#pragma once

#include <gtkmm/button.h>
#include <gtkmm/window.h>

namespace TypeTrace::Frontend {

class TypeTraceWindow : public Gtk::Window
{
  public:
    TypeTraceWindow();
    TypeTraceWindow(const TypeTraceWindow &) = delete;
    TypeTraceWindow(TypeTraceWindow &&) = delete;

    auto operator=(const TypeTraceWindow &) -> TypeTraceWindow & = delete;
    auto operator=(TypeTraceWindow &&) -> TypeTraceWindow & = delete;

    ~TypeTraceWindow() override = default;

  protected:
    // Signal handlers:
    void on_button_clicked();

    // Member widgets:
    Gtk::Button button;
};

} // namespace TypeTrace::Frontend
