pkgdatadir = (get_option('prefix') / get_option('datadir') / meson.project_name())
moduledir = pkgdatadir / 'typetrace'

blueprints = custom_target('blueprints',
  input: files(
    'window.blp',
    'gtk/help-overlay.blp',
  ),
  output: '.',
  command: [find_program('blueprint-compiler'), 'batch-compile', '@OUTPUT@', '@CURRENT_SOURCE_DIR@', '@INPUT@'],
)

gnome.compile_resources('typetrace',
  'typetrace.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
  dependencies: blueprints,
)

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
# conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'typetrace.in',
  output: 'typetrace',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'r-xr-xr-x'
)

typetrace_sources = [
  '__init__.py',
  'main.py',
  'window.py',
]

install_data(typetrace_sources, install_dir: moduledir)
