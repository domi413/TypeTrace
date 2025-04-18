fs = import('fs')

conf = configuration_data()
conf.set('bindir', get_option('prefix') / get_option('bindir'))

# Desktop Entry
desktop_file = configure_file(
  input: 'edu.ost.typetrace.desktop.in',
  output: 'edu.ost.typetrace.desktop',
  configuration: conf,
  install_dir: get_option('datadir') / 'applications',
)

desktop_file_backend = configure_file(
  input: 'edu.ost.typetrace-backend.desktop.in',
  output: 'edu.ost.typetrace-backend.desktop',
  configuration: conf,
  install_dir: get_option('datadir') / 'applications',
)

desktop_utils = find_program('desktop-file-validate', required: false)
if desktop_utils.found()
  test('Validate desktop file', desktop_utils, args: [desktop_file, desktop_file_backend])
endif

# Metainfo (will probably be unnecessary)
appstream_file = fs.copyfile(
  'edu.ost.typetrace.metainfo.xml.in',
  'edu.ost.typetrace.metainfo.xml',
  install: true,
  install_dir: get_option('datadir') / 'metainfo',
)

appstreamcli = find_program('appstreamcli', required: false, disabler: true)
test(
  'Validate appstream file',
  appstreamcli,
  args: ['validate', '--no-net', '--explain', appstream_file],
)

# Gschema
install_data(
  'edu.ost.typetrace.gschema.xml',
  install_dir: get_option('datadir') / 'glib-2.0' / 'schemas',
)

compile_schemas = find_program('glib-compile-schemas', required: false, disabler: true)
test(
  'Validate schema file',
  compile_schemas,
  args: ['--strict', '--dry-run', meson.current_source_dir()],
)

# Services
configure_file(
  input: 'edu.ost.typetrace.service.in',
  output: 'edu.ost.typetrace.service',
  configuration: conf,
  install_dir: get_option('datadir') / 'dbus-1' / 'services',
)

subdir('icons')