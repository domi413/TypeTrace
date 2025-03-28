backenddir = pkgdatadir / 'backend'
backend_eventsdir = backenddir / 'events'
backend_ipcdir = backenddir / 'ipc'

# Main backend files
backend_main_sources = [
  '__init__.py',
  'cli.py',
  'config.py',
  'db.py',
  'logging_setup.py',
  'sql.py',
]
install_data(
  backend_main_sources,
  install_dir: backenddir,
)

# Event files
backend_events_sources = [
  'events/__init__.py',
  'events/base.py',
  'events/linux.py',
  'events/windows_darwin.py',
]
install_data(
  backend_events_sources,
  install_dir: backenddir / 'events',
)

# IPC files
backend_ipc_sources = [
  'ipc/__init__.py',
  'ipc/base.py',
  'ipc/linux_darwin.py',
  'ipc/windows.py',
]
install_data(
  backend_ipc_sources,
  install_dir: backenddir / 'ipc',
)
