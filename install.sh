#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
REPO_URL="https://github.com/domi413/TypeTrace.git"
APP_NAME="TypeTrace"
APP_ID="edu.ost.typetrace"
USER_LOCAL_PREFIX="$HOME/.local" # Install into user's local directory

# --- Helper Functions ---
print_info() {
    echo "INFO: $1"
}

print_warning() {
    echo "WARN: $1" >&2
}

print_error() {
    echo "ERROR: $1" >&2
    exit 1
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        print_error "Required command '$1' not found. Please install it and try again."
    fi
}

# --- Dependency Checks ---
check_command "git"
check_command "curl"

# --- Setup ---
# Create a temporary directory for cloning and building
WORK_DIR=$(mktemp -d)
# Ensure cleanup happens on script exit or interruption
trap 'cd / && rm -rf "$WORK_DIR"' EXIT # Go back to / before removing WORK_DIR

print_info "Created temporary working directory: $WORK_DIR"
cd "$WORK_DIR"

# --- Clone Repository ---
print_info "Cloning $APP_NAME repository from $REPO_URL..."
# Clone quietly to avoid cluttering output
git clone --depth 1 "$REPO_URL" . > /dev/null 2>&1
print_info "Repository cloned successfully."

# --- Installation Method Prompt ---
INSTALL_METHOD=""
echo ""
echo "How would you like to install $APP_NAME?"
echo "1) Flatpak (Sandboxed, user-install, recommended)"
echo "2) Meson (User-local install to $USER_LOCAL_PREFIX, requires build dependencies)"
while [[ "$INSTALL_METHOD" != "1" && "$INSTALL_METHOD" != "2" ]]; do
    read -p "Enter your choice (1 or 2): " INSTALL_METHOD < /dev/tty
done

# --- Installation Logic ---
if [[ "$INSTALL_METHOD" == "1" ]]; then
    # --- Flatpak Installation ---
    print_info "Starting Flatpak installation..."
    check_command "flatpak"
    check_command "flatpak-builder"

    MANIFEST_FILE="${APP_ID}.yaml"
    if [[ ! -f "$MANIFEST_FILE" ]]; then
        print_error "Flatpak manifest file '$MANIFEST_FILE' not found in repository."
    fi

    print_info "Building and installing $APP_NAME as a Flatpak (user)..."
    # Use the command from the Makefile, ensuring it's user install
    flatpak-builder --user --install --force-clean _build "$MANIFEST_FILE"

    print_info "$APP_NAME Flatpak installation complete."
    print_info "You can run it using: flatpak run $APP_ID"

elif [[ "$INSTALL_METHOD" == "2" ]]; then
    # --- Meson User-Local Installation ---
    print_info "Starting Meson (user-local) installation..."
    check_command "meson"
    check_command "ninja"
    check_command "pkg-config"
    # Check for a C compiler
    if ! command -v gcc &> /dev/null && ! command -v clang &> /dev/null; then
        print_error "No C compiler (gcc or clang) found. Please install one."
    fi

    # --- Python Dependency Check ---
    PYTHON_CMD=""
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_error "Python (python3 or python) command not found. It is required for runtime dependencies."
    fi
    print_info "Using '$PYTHON_CMD' for Python checks."

    # List required Python modules and their corresponding pip package names
    declare -A PYTHON_DEPS
    PYTHON_DEPS=( ["appdirs"]="appdirs" ["evdev"]="python-evdev" ["dbus"]="dbus-python" )
    MISSING_DEPS=()
    PIP_PACKAGES=()

    print_info "Checking for required Python modules: ${!PYTHON_DEPS[*]}..."
    for module in "${!PYTHON_DEPS[@]}"; do
        if ! $PYTHON_CMD -c "import $module" &> /dev/null; then
            print_warning "Python module '$module' not found."
            MISSING_DEPS+=("$module")
            PIP_PACKAGES+=("${PYTHON_DEPS[$module]}")
        fi
    done

    if [[ ${#MISSING_DEPS[@]} -gt 0 ]]; then
        print_warning "The application requires the following missing Python modules: ${MISSING_DEPS[*]}"
        # Check for pip
        PIP_CMD=""
        if command -v pip3 &> /dev/null; then
             PIP_CMD="pip3"
        elif command -v pip &> /dev/null; then
             PIP_CMD="pip"
        fi

        if [[ -n "$PIP_CMD" ]]; then
            print_info "Found pip command: '$PIP_CMD'"
            INSTALL_CMD="$PIP_CMD install --user --upgrade ${PIP_PACKAGES[*]}" # Add --upgrade for good measure
            INSTALL_PY_DEPS=""
            while [[ "$INSTALL_PY_DEPS" != "y" && "$INSTALL_PY_DEPS" != "n" ]]; do
                 read -p "Attempt to install them using '$INSTALL_CMD'? (y/N): " INSTALL_PY_DEPS  < /dev/tty
                 INSTALL_PY_DEPS=$(echo "$INSTALL_PY_DEPS" | tr '[:upper:]' '[:lower:]')
                 if [[ -z "$INSTALL_PY_DEPS" ]]; then INSTALL_PY_DEPS="n"; fi
            done

            if [[ "$INSTALL_PY_DEPS" == "y" ]]; then
                print_info "Running: $INSTALL_CMD"
                if $INSTALL_CMD; then
                     print_info "Python dependencies installed successfully."
                else
                     print_error "Failed to install Python dependencies using pip. Please install them manually and re-run the script."
                fi
            else
                print_error "Python dependencies are missing. Please install them manually (e.g., '$INSTALL_CMD') and re-run the script."
                exit 1
            fi
        else
            # pip not found
            print_error "Python dependencies (${MISSING_DEPS[*]}) are missing, and 'pip' command was not found."
            print_error "Please install pip and the required packages (e.g., using your system package manager for pip, then 'pip install --user ${PIP_PACKAGES[*]}') and re-run the script."
            exit 1
        fi
    else
        print_info "All required Python modules are present."
    fi
    # --- End Python Dependency Check ---

    print_warning "Meson installation also requires development libraries for GTK4, Libadwaita, GLib, and Libevdev."
    print_warning "Example (Debian/Ubuntu): sudo apt install libgtk-4-dev libadwaita-1-dev libglib2.0-dev libevdev-dev meson ninja-build pkg-config"
    print_warning "Example (Fedora): sudo dnf install gtk4-devel libadwaita-devel glib2-devel libevdev-devel meson ninja-build pkgconfig"
    read -p "Press Enter to continue if you have these installed, or Ctrl+C to abort..."  < /dev/tty

    BUILD_DIR="_build"

    print_info "Configuring Meson build (prefix: $USER_LOCAL_PREFIX)..."
    meson setup "$BUILD_DIR" --prefix="$USER_LOCAL_PREFIX"

    print_info "Compiling $APP_NAME..."
    meson compile -C "$BUILD_DIR"

    print_info "Installing $APP_NAME to $USER_LOCAL_PREFIX..."
    meson install -C "$BUILD_DIR"

    print_info "$APP_NAME Meson installation complete."
    print_info "Executable installed to: $USER_LOCAL_PREFIX/bin/typetrace"
    print_warning "IMPORTANT: To run 'typetrace' directly from your terminal, ensure '$USER_LOCAL_PREFIX/bin' is included in your PATH environment variable."
    print_warning "You may need to add 'export PATH=\"$HOME/.local/bin:\$PATH\"' to your shell configuration file (e.g., ~/.bashrc, ~/.zshrc) and restart your shell or log out and log back in."
    print_warning("For icons and desktop files to be recognized, ensure your desktop environment checks '$USER_LOCAL_PREFIX/share' (this is often default). You may need to set/append to XDG_DATA_DIRS.")

fi

# --- Input Group Check (Requires sudo if modification is needed) ---
print_info "Checking if user '$USER' belongs to the 'input' group..."
if id -Gn "$USER" | grep -qw input; then
    print_info "User '$USER' is already in the 'input' group. No action needed."
else
    print_warning "User '$USER' is NOT in the 'input' group."
    print_warning "$APP_NAME needs access to input devices (/dev/input/event*) which usually requires membership in the 'input' or a similar group."
    ADD_TO_GROUP=""
    while [[ "$ADD_TO_GROUP" != "y" && "$ADD_TO_GROUP" != "n" ]]; do
        read -p "Add user '$USER' to the 'input' group using sudo? (y/N): " ADD_TO_GROUP  < /dev/tty
        ADD_TO_GROUP=$(echo "$ADD_TO_GROUP" | tr '[:upper:]' '[:lower:]')
        if [[ -z "$ADD_TO_GROUP" ]]; then # Default to No if user just presses Enter
            ADD_TO_GROUP="n"
        fi
    done

    if [[ "$ADD_TO_GROUP" == "y" ]]; then
        print_info "Attempting to add user '$USER' to 'input' group using sudo..."
        if sudo usermod -aG input "$USER"; then
            print_info "Successfully added user '$USER' to the 'input' group."
            print_warning "IMPORTANT: You MUST log out and log back in for the group change to take effect!"
        else
            print_error "Failed to add user to the 'input' group. Please do it manually (e.g., sudo usermod -aG input $USER) and then log out and back in."
        fi
    else
        print_warning "Skipping adding user to 'input' group. $APP_NAME might not function correctly without input device access."
    fi
fi

echo ""
print_info "$APP_NAME installation script finished."
# Traps

exit 0