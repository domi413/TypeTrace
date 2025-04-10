APP_ID = edu.ost.typetrace
MANIFEST = $(APP_ID).yaml
BUILD_DIR = _build
INSTALL_DIR = _install
BP_DIR = subprojects/blueprint-compiler
BP_REPO = https://gitlab.gnome.org/jwestman/blueprint-compiler.git
BP_BRANCH = v0.16.0

# Default target
all: meson-run

clean:
	rm -rf $(BUILD_DIR) $(INSTALL_DIR)

# Flatpak targets
flatpak-build: clean $(MANIFEST)
	flatpak-builder --force-clean $(BUILD_DIR) $(MANIFEST)

flatpak-run: flatpak-build
	flatpak-builder --run $(BUILD_DIR) $(MANIFEST) typetrace

flatpak-install: clean
	flatpak-builder --install --user $(BUILD_DIR) $(MANIFEST)

# Meson targets
meson-setup: clean
	meson setup $(BUILD_DIR) --prefix=$(CURDIR)/$(INSTALL_DIR)

meson-build: meson-setup
	meson compile -C $(BUILD_DIR)

meson-install: meson-build
	meson install -C $(BUILD_DIR)

meson-run: $(INSTALL_DIR)/bin/typetrace
	env GSETTINGS_SCHEMA_DIR=$(INSTALL_DIR)/share/glib-2.0/schemas $(INSTALL_DIR)/bin/typetrace

$(INSTALL_DIR)/bin/typetrace:
	$(MAKE) meson-install

# Phony targets
.PHONY: all flatpak-build flatpak-run flatpak-install meson-setup meson-build meson-install clean
