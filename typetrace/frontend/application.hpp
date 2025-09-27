#include <gtkmm/button.h>
#include <gtkmm/window.h>

namespace typetrace::frontend {

class Application : public Gtk::Window
{
  public:
    Application();

  private:
    auto onButtonClicked() -> void;

    Gtk::Button button;
};

} // namespace typetrace::frontend
