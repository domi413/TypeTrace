#include <gtkmm/button.h>
#include <gtkmm/window.h>

namespace typetrace::frontend {

class Application : public Gtk::Window
{
  public:
    Application();

  private:
    void on_button_clicked();

    Gtk::Button button;
};

} // namespace typetrace::frontend
