backenddir = pkgdatadir / 'backend'
backend_eventsdir = backenddir / 'events'

# Main backend files
backend_main_sources = [
  '__init__.py',
  'cli.py',
  'db.py',
  'dbus_service.py',
]
install_data(
  backend_main_sources,
  install_dir: backenddir,
)

# Config file

config_source = [
  '../config.py'
]

# Event files
backend_events_sources = [
  'events/__init__.py',
  'events/base.py',
  'events/linux.py',
]
install_data(
  backend_events_sources,
  install_dir: backenddir / 'events',
)
