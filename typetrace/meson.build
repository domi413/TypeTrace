datadir = get_option('prefix') / get_option('datadir')
pkgdatadir = datadir / meson.project_name()

conf = configuration_data()
conf.set('application_id', 'edu.ost.typetrace')
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('datadir', datadir)
conf.set('pkgdatadir', pkgdatadir)
conf.set('VERSION', meson.project_version())
configure_file(
  input: 'typetrace.in',
  output: 'typetrace',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'r-xr-xr-x',
)

configure_file(
  input: 'config.py',
  output: 'config.py',
  configuration: conf,
  install: true,
  install_dir: pkgdatadir,
)

sources = [
  '__init__.py',
  'sql.py',
  'logging_setup.py',
]
install_data(sources, install_dir: pkgdatadir)

subdir('frontend')
subdir('backend')
