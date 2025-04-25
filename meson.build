project(
  'typetrace',
  version: '0.1.0',
  meson_version: '>= 1.0.0',
  default_options: [
    'warning_level=2',
    'werror=false',
  ],
)

gnome = import('gnome')
python = import('python')

dependency('gtk4', version: '>= 4.0')
dependency('libadwaita-1', version: '>= 1.6')
find_program('blueprint-compiler', required: true)

subdir('data')
subdir('typetrace')

gnome.post_install(
  glib_compile_schemas: true,
  gtk_update_icon_cache: true,
  update_desktop_database: true,
)