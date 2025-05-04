#!/usr/bin/env bash

# --- Configuration ---
readonly REPO_URL="https://github.com/domi413/TypeTrace.git"
readonly API_URL="https://api.github.com/repos/domi413/TypeTrace/releases/latest"
readonly APP_NAME="TypeTrace"
readonly APP_ID="edu.ost.typetrace"
readonly USER_LOCAL_PREFIX="$HOME/.local"

# --- Colors ---
readonly C_RESET='\033[0m'
readonly C_BOLD='\033[1m'
readonly C_RED='\033[0;31m'
readonly C_GREEN='\033[0;32m'
readonly C_YELLOW='\033[0;33m'
readonly C_BLUE='\033[0;34m'
readonly C_CYAN='\033[0;36m'

# --- Helper Functions ---
_print_message() {
    local color="$1"
    local prefix="$2"
    local message="$3"

    printf "${color}${C_BOLD}%s:${C_RESET}${color} %b${C_RESET}\n" "$prefix" "$message" >&2
}

print_step() {
    printf "\n${C_CYAN}${C_BOLD}==>${C_RESET}${C_BOLD} %s${C_RESET}\n" "$1" >&2
}

print_success() {
    _print_message "$C_GREEN" "SUCCESS:" "$1"
}

print_info() {
    _print_message "$C_BLUE" "INFO:" "$1"
}

print_warning() {
    _print_message "$C_YELLOW" "WARNING:" "$1"
}

print_error() {
    _print_message "$C_RED" "ERROR:" "$1"
    exit 1
}

# Function to ensure script is running with root privileges
ensure_sudo() {
    if [[ $EUID -eq 0 ]]; then
        return 0
    fi

    if ! command -v sudo &>/dev/null; then
        print_error "'sudo' command not found.
        Cannot gain root privileges needed for this operation
        Please run the script using 'sudo'."
    fi

    print_warning "This operation requires root privileges."
    print_info "Attempting to re-run script with sudo..."

    sudo "$0" "$@"
    exit $?
}

# Checks if a list of commands are available in PATH
check_commands() {
    local missing_cmds=()
    for cmd in "$@"; do
        if ! command -v "$cmd" &>/dev/null; then
            missing_cmds+=("$cmd")
        fi
    done

    if [[ ${#missing_cmds[@]} -gt 0 ]]; then
        print_error "Required command(s) not found: ${missing_cmds[*]}.
        Please install them and try again."
    fi
}

# Function to prompt the user to log out
prompt_logout() {
    local choice=""
    while true; do
        read -rp "Do you want to log out now? (y/N): " choice </dev/tty
        choice=${choice,,}

        if [[ "$choice" == "y" || "$choice" == "n" || -z "$choice" ]]; then
            break
        else
            print_warning "Invalid input. Please enter 'y' or 'n'."
        fi
    done

    if [[ "$choice" == "y" ]]; then
        print_info "Attempting to initiate logout..."
        if command -v loginctl &>/dev/null && [[ -n "$XDG_SESSION_ID" ]]; then
            if loginctl terminate-session "$XDG_SESSION_ID"; then
                print_success "Logout command sent successfully via loginctl."
                print_info "Your session should terminate shortly."
                exit 0
            else
                print_info "loginctl command failed to terminate session $XDG_SESSION_ID."
                print_info "Please log out manually using your desktop environment's menu."
            fi
        else
            print_warning "Could not find 'loginctl' command or \$XDG_SESSION_ID."
            print_info "Cannot attempt automatic logout."
            print_info "Please log out manually."
        fi
    else
        print_info "Okay, please remember to log out manually soon."
    fi
}

prompt_add_to_input_group() {
    print_warning "User '$USER' is NOT in the 'input' group (or check failed)."
    print_warning "$APP_NAME requires access to input devices (/dev/input/event*)."
    print_info "Adding user '$USER' to the 'input' group requires elevated privileges."

    ensure_sudo "$@"

    print_info "Attempting 'usermod -aG input $USER' (as root)..."

    if usermod -aG input "$USER"; then
        print_success "Successfully added user '$USER' to the 'input' group."
        print_warning "${C_BOLD}User '$USER' MUST log out for the group change to take effect!${C_RESET}"
        return 0
    else
        print_error "Failed to add user '$USER' to the 'input' group even with root privileges.
        Check system logs. Manual step: 'sudo usermod -aG input $USER'"
    fi
}

# Checks if the current user is in the 'input' group
check_input_group() {
    print_step "Checking input group membership for user '$USER'"

    if id -Gn "$USER" | grep -qw input; then
        print_success "User '$USER' is already in the 'input' group."
        return 1
    else
        if prompt_add_to_input_group "$@"; then
            return 0
        else
            return 2
        fi
    fi
}

# Function to create temporary working directory
create_temp_workdir() {
    WORK_DIR=$(mktemp -d)
    if [[ $? -ne 0 || -z "$WORK_DIR" || ! -d "$WORK_DIR" ]]; then
        print_error "Failed to create temporary directory."
    fi
    print_info "Created temporary working directory: $WORK_DIR"
}

# Function to handle cleanup on exit
cleanup() {
    local exit_status=$?
    if [[ -n "$WORK_DIR" && -d "$WORK_DIR" ]]; then
        print_info "Cleaning up temporary directory: $WORK_DIR"
        cd /
        rm -rf "$WORK_DIR"
        print_success "Temporary directory cleaned up."
    fi

    if [[ "$exit_status" -ne 0 ]]; then
        printf "${C_RESET}\nScript finished with exit status %d.\n" "$exit_status" >&2
    fi

    exit "$exit_status"
}

trap cleanup EXIT SIGINT SIGTERM

# --- Installation Functions ---
install_flatpak() {
    print_step "Starting Flatpak installation"

    local flatpak_commands=(
        "flatpak"
        "curl"
        "jq"
    )
    check_commands "${flatpak_commands[@]}"

    print_info "Fetching latest release information from GitHub..."

    local download_url
    download_url=$(curl -s "$API_URL" | jq -r '.assets[] | select(.name == "typetrace.flatpak") | .browser_download_url')

    if [[ -z "$download_url" ]]; then
        print_error "Failed to find 'typetrace.flatpak' in the latest release."
    fi

    print_info "Found download URL: $download_url"

    local flatpak_file="$WORK_DIR/typetrace.flatpak"
    if curl -L -o "$flatpak_file" "$download_url"; then
        print_success "Successfully downloaded typetrace.flatpak"
    else
        print_error "Failed to download typetrace.flatpak from $download_url"
    fi

    print_info "Installing $APP_NAME as a Flatpak (user)..."
    if flatpak --user install -y "$flatpak_file"; then
        print_success "$APP_NAME Flatpak installation complete."
        print_info "You can run it using: ${C_BOLD}flatpak run $APP_ID${C_RESET}"
    else
        print_error "Flatpak installation failed."
    fi
}

install_local() {
    print_step "Starting Local Installation to $USER_LOCAL_PREFIX"

    local local_commands=(
        "meson"
        "ninja"
        "pkg-config"
        "curl"
        "jq"
    )
    check_commands "${local_commands[@]}"

    print_info "Checking for GTK4 dependency..."
    if ! pkg-config --modversion gtk4 &>/dev/null; then
        print_error "GTK4 not found. Please install GTK4 libraries and try again."
    fi
    print_success "GTK4 dependency found."

    print_info "Fetching latest release information from GitHub..."
    local latest_tag
    latest_tag=$(curl -s "$API_URL" | jq -r '.tag_name')

    if [[ -z "$latest_tag" ]]; then
        print_error "Failed to retrieve latest release tag from GitHub."
    fi
    print_info "Latest release tag: $latest_tag"

    print_step "Cloning $APP_NAME repository (tag: $latest_tag)"
    print_info "Source: $REPO_URL"
    if git clone --quiet --depth 1 --branch "$latest_tag" "$REPO_URL" .; then
        print_success "Repository cloned successfully at tag $latest_tag."
    else
        print_error "Failed to clone repository from $REPO_URL at tag $latest_tag"
    fi

    print_info "Configuring Meson build..."
    local build_dir="$WORK_DIR/build"
    if ! meson setup "$build_dir" --prefix="$USER_LOCAL_PREFIX" --buildtype=release; then
        print_error "Failed to configure Meson build."
    fi
    print_success "Meson build configured successfully."

    print_info "Compiling $APP_NAME..."
    if ! ninja -C "$build_dir"; then
        print_error "Failed to compile $APP_NAME."
    fi
    print_success "$APP_NAME compiled successfully."

    local manifest_dir="$USER_LOCAL_PREFIX/share/typetrace"
    local manifest_file="$manifest_dir/uninstall_manifest.txt"
    mkdir -p "$manifest_dir" || print_error "Failed to create manifest directory $manifest_dir."

    print_info "Installing $APP_NAME to $USER_LOCAL_PREFIX..."
    if ! ninja -C "$build_dir" install; then
        print_error "Failed to install $APP_NAME to $USER_LOCAL_PREFIX."
    fi

    local meson_manifest="$build_dir/meson-logs/install-log.txt"
    if [[ -f "$meson_manifest" ]]; then
        cp "$meson_manifest" "$manifest_file" || print_warning "Failed to copy install manifest to $manifest_file."
        print_success "Uninstall manifest copied to $manifest_file."
    else
        print_warning "Meson install manifest not found at $meson_manifest."
        print_info "Uninstallation may require manual cleanup of files in $USER_LOCAL_PREFIX."
    fi

    print_success "$APP_NAME installed successfully to $USER_LOCAL_PREFIX."

    print_info "The application should now be visible within your desktop environment."
    print_info "To run $APP_NAME using 'typetrace', ensure $USER_LOCAL_PREFIX/bin is in your PATH."
    print_info "You can run it directly using: ${C_BOLD}$USER_LOCAL_PREFIX/bin/typetrace${C_RESET}"
    print_info "To add to PATH, consider adding to ~/.bashrc or equivalent."
    print_info "To uninstall, run: ${C_BOLD}xargs -r rm -rf < \"$manifest_file\" && rm -r \"$HOME/.local/share/typetrace\"${C_RESET}"
    print_info "For the backend to be able to run automatically when the application starts you need to log out and in."
}

# --- Main Execution Function ---
main() {
    print_step "Starting $APP_NAME Installation Script"

    readonly BASE_COMMANDS=(
        "git"
        "curl"
    )
    check_commands "${BASE_COMMANDS[@]}"

    create_temp_workdir

    if ! cd "$WORK_DIR"; then
        print_error "Failed to change directory to $WORK_DIR"
    fi

    print_step "Select installation method"
    print_info "How would you like to install $APP_NAME?
        1) Flatpak (Sandboxed, user-local install)
        2) Local   (local install to $USER_LOCAL_PREFIX, requires GTK dependencies)"

    local INSTALL_METHOD=""
    while [[ "$INSTALL_METHOD" != "1" && "$INSTALL_METHOD" != "2" ]]; do
        read -rp $'\nEnter your choice (1 or 2): ' INSTALL_METHOD </dev/tty

        if [[ "$INSTALL_METHOD" != "1" && "$INSTALL_METHOD" != "2" ]]; then
            print_warning "Invalid input. Please enter '1' or '2'."
        fi
    done

    case "$INSTALL_METHOD" in
    1)
        install_flatpak
        ;;
    2)
        install_local "$@"
        ;;
    *)
        print_error "How did you get here?"
        ;;
    esac

    check_input_group "$@"
    local group_check_status=$?

    if [[ "$group_check_status" -eq 0 ]]; then
        prompt_logout
    elif [[ "$group_check_status" -eq 2 ]]; then
        print_error "Failed to handle group membership. Aborting further steps."
    fi

    print_step "Installation finished"
    print_success "$APP_NAME installation finished successfully"

    print_step "Cleanup"
}

main "$@"
