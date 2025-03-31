APP_ID = edu.ost.typetrace
MANIFEST = $(APP_ID).yaml
BUILD_DIR = _build
INSTALL_DIR = _install
BP_DIR = subprojects/blueprint-compiler
BP_REPO = https://gitlab.gnome.org/jwestman/blueprint-compiler.git
BP_BRANCH = v0.16.0

# Default target
all: build


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

meson-uninstall:
	ninja uninstall -C $(BUILD_DIR)

meson-test: meson-setup
	meson test -C $(BUILD_DIR) --verbose

# Clean targets
clean:
	rm -rf $(BUILD_DIR) $(INSTALL_DIR)

# Phony targets
.PHONY: all flatpak-build flatpak-run flatpak-install meson-setup meson-build meson-install meson-uninstall clean
