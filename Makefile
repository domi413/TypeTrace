APP_ID = edu.ost.typetrace
MANIFEST = $(APP_ID).yaml
BUILD_DIR = _build
INSTALL_DIR = _install
REPO_DIR = _repo
BP_DIR = subprojects/blueprint-compiler
BP_REPO = https://gitlab.gnome.org/jwestman/blueprint-compiler.git
BP_BRANCH = v0.16.0

# Default target
all: meson-install

clean:
	rm -rf $(BUILD_DIR) $(INSTALL_DIR)

test: $(INSTALL_DIR)/bin/typetrace
	env GSETTINGS_SCHEMA_DIR=$(INSTALL_DIR)/share/glib-2.0/schemas $(INSTALL_DIR)/bin/typetrace -d

$(INSTALL_DIR)/bin/typetrace:
	$(MAKE) meson-install

# Flatpak targets
flatpak-build: clean $(MANIFEST)
	flatpak-builder --force-clean --repo=$(REPO_DIR) $(BUILD_DIR) $(MANIFEST)

flatpak-run: flatpak-build
	flatpak-builder --run $(BUILD_DIR) $(MANIFEST) typetrace

flatpak-install: clean
	flatpak-builder --install --user $(BUILD_DIR) $(MANIFEST)

flatpak-export: flatpak-build
	flatpak build-bundle $(REPO_DIR) typetrace.flatpak $(APP_ID) --runtime-repo=https://flathub.org/repo/flathub.flatpakrepo
	@echo "Flatpak bundle created: $(FLATPAK_BUNDLE)"

# Meson targets
meson-setup: clean
	meson setup $(BUILD_DIR) --prefix=$(CURDIR)/$(INSTALL_DIR)

meson-build: meson-setup
	meson compile -C $(BUILD_DIR)

meson-install: meson-build
	meson install -C $(BUILD_DIR)

# Phony targets
.PHONY: all flatpak-build flatpak-run flatpak-install meson-setup meson-build meson-install clean
