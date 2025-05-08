moduledir = pkgdatadir / 'frontend'

blueprints = custom_target(
  'blueprints',
  input: files(
    'gtk/help-overlay.blp',
    'view/preferences.blp',
    'view/window.blp',
    'view/heatmap.blp',
    'view/verbose.blp',
    'view/statistics.blp',
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
  'controller/statistics.py',
  'controller/preferences.py',
]
install_data(sources_controller, install_dir: moduledir / 'controller')

sources_controller_utils = [
  'controller/utils/__init__.py',
  'controller/utils/dialog_utils.py',
  'controller/utils/desktop_utils.py',
  'controller/utils/color_utils.py',
]
install_data(sources_controller_utils, install_dir: moduledir / 'controller' / 'utils')

sources_service = [
  'service/__init__.py',
  'service/backend_connector.py',
]
install_data(sources_service, install_dir: moduledir / 'service')

sources_controller_utils_charts = [
  'controller/utils/charts/__init__.py',
  'controller/utils/charts/base_chart.py',
  'controller/utils/charts/line_chart.py',
  'controller/utils/charts/pie_chart.py',
]
install_data(sources_controller_utils_charts, install_dir: moduledir / 'controller' / 'utils' / 'charts')
