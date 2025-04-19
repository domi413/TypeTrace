datadir = get_option('prefix') / get_option('datadir')
pkgdatadir = datadir / meson.project_name()
moduledir = pkgdatadir / meson.project_name()

blueprints = custom_target(
  'blueprints',
  input: files(
    'gtk/help-overlay.blp',
    'view/preferences.blp',
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
conf.set('application_id', 'edu.ost.typetrace')
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('datadir', datadir)
conf.set('pkgdatadir', pkgdatadir)
conf.set('VERSION', meson.project_version())
configure_file(
  input: '../typetrace.in',
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
  install_dir: moduledir,
)

sources = [
  '__init__.py',
  'application.py',
]
install_data(sources, install_dir: moduledir)

sources_model = [
  'model/__init__.py',
  'model/database_manager.py',
  'model/keystrokes.py',
  'model/layouts.py',
]
install_data(sources_model, install_dir: moduledir / 'model')

sources_controller = [
  'controller/__init__.py',
  'controller/window.py',
  'controller/heatmap.py',
  'controller/verbose.py',
  'controller/preferences.py',
]
install_data(sources_controller, install_dir: moduledir / 'controller')

sources_controller_utils = [
  'controller/utils/__init__.py',
  'controller/utils/dialog_utils.py',
  'controller/utils/desktop_utils.py'
]
install_data(sources_controller_utils, install_dir: moduledir / 'controller' / 'utils')

subdir('backend')
