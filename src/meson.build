pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'typetrace'

blueprints = custom_target(
  'blueprints',
  input: files(
    'gtk/help-overlay.blp',
    'view/window.blp',
    'view/heatmap.blp',
    'view/verbose.blp',
  ),
  output: '.',
  command: [
    find_program('blueprint-compiler'),
    'batch-compile',
    '@OUTPUT@',
    '@CURRENT_SOURCE_DIR@',
    '@INPUT@',
  ],
)

gnome.compile_resources(
  'typetrace',
  'typetrace.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
  dependencies: blueprints,
)

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
conf.set('pkgdatadir', pkgdatadir)
configure_file(
  input: 'typetrace.in',
  output: 'typetrace',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'r-xr-xr-x',
)

sources = [
  '__init__.py',
  'main.py',
]
install_data(sources, install_dir: moduledir)

sources_model = [
  'model/__init__.py',
  'model/keystrokes.py'
]
install_data(sources_model, install_dir: moduledir / 'model')

sources_controller = [
  'controller/__init__.py',
  'controller/window.py',
  'controller/heatmap.py',
  'controller/verbose.py',
]
install_data(sources_controller, install_dir: moduledir / 'controller')

subdir('backend')
