fs = import('fs')

# Desktop Entry
desktop_file = fs.copyfile(
  'edu.ost.typetrace.desktop.in',
  'edu.ost.typetrace.desktop',
  install: true,
  install_dir: get_option('datadir') / 'applications',
)

desktop_utils = find_program('desktop-file-validate', required: false)
if desktop_utils.found()
  test('Validate desktop file', desktop_utils, args: [desktop_file])
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
conf = configuration_data()
conf.set('bindir', get_option('prefix') / get_option('bindir'))
configure_file(
  input: 'edu.ost.typetrace.service.in',
  output: 'edu.ost.typetrace.service',
  configuration: conf,
  install_dir: get_option('datadir') / 'dbus-1' / 'services',
)

# Backend Service
configure_file(
  input: 'edu.ost.typetrace-backend.service.in',
  output: 'edu.ost.typetrace-backend.service',
  configuration: conf,
  install_dir: get_option('libdir') / 'systemd' / 'user',
)

subdir('icons')