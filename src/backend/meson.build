moduledir = pkgdatadir / 'backend'

backend_sources = [
  '__init__.py',
  'cli.py',
  'config.py',
  'db.py',
  'devices.py',
  'events.py',
  'logging_setup.py',
  'sql.py',
]

install_data(
  backend_sources,
  install_dir: moduledir,
  # install_mode: ['rw-r--r--', 'root', 'root'] TODO: figure out permissions
)

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('pkgdatadir', pkgdatadir)
configure_file(
  input: 'typetrace-backend.in',
  output: 'typetrace-backend',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'r-xr-xr-x',
)