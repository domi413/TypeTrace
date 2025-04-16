#!/usr/bin/env bash

# --- Configuration ---
readonly REPO_URL="https://github.com/domi413/TypeTrace.git"
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

    printf "${color}${C_BOLD}%s:${C_RESET}${color} %s${C_RESET}\n" "$prefix" "$message" >&2
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
# If not root, attempts to re-execute the script using sudo.
# Usage: ensure_sudo "$@"
ensure_sudo() {
    # Check if already running as root
    if [[ $EUID -eq 0 ]]; then
        return 0
    fi

    # Not root, check if sudo command exists
    if ! command -v sudo &>/dev/null; then
        print_error "'sudo' command not found.\n
            Cannot gain root privileges needed for this operation.\n
            Please run the script using 'sudo'."
    fi

    print_warning "This operation requires root privileges."
    print_info "Attempting to re-run script with sudo..."

    # Execute sudo, passing all original arguments
    sudo "$0" "$@"

    exit $?
}

# Checks if a list of commands are available in PATH
# Usage: check_commands "cmd1" "cmd2" "cmd3"
check_commands() {
    local missing_cmds=()
    for cmd in "$@"; do
        if ! command -v "$cmd" &>/dev/null; then
            missing_cmds+=("$cmd")
        fi
    done

    if [[ ${#missing_cmds[@]} -gt 0 ]]; then
        print_error "Required command(s) not found: ${missing_cmds[*]}. Please install them and try again."
    fi
}

# Function to prompt the user to log out and optionally attempt it
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
        print_error "Failed to add user '$USER' to the 'input' group even with root privileges.\n
                     Check system logs. Manual step: 'sudo usermod -aG input $USER'"
    fi
}

# Checks if the current user is in the 'input' group and prompts to add if not
# Usage: check_input_group
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

# Function to create and manage temporary working directory
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
    fi

    printf "${C_RESET}\nScript finished with exit status %d.\n" "$exit_status" >&2
    exit "$exit_status"
}

# Set up trap to call cleanup function on exit signals
trap cleanup EXIT SIGINT SIGTERM

# --- Installation Functions ---
install_flatpak() {
    print_step "Starting Flatpak installation"

    local flatpak_commands=(
        "flatpak"
        "flatpak-builder"
    )
    check_commands "${flatpak_commands[@]}" # Exits on error

    local manifest_file="${APP_ID}.yaml"
    if [[ ! -f "$manifest_file" ]]; then
        print_error "Flatpak manifest file '$manifest_file' not found in repository."
    fi

    print_info "Building and installing $APP_NAME as a Flatpak (user)..."

    if flatpak-builder --user --install --force-clean _build "$manifest_file"; then
        print_success "$APP_NAME Flatpak installation complete."
        print_info "You can run it using: ${C_BOLD}flatpak run $APP_ID${C_RESET}"
    else
        print_error "Flatpak build or installation failed."
    fi
}

install_local() {
    # TODO: Implement local install
    true # placeholder
}

# --- Main Execution Function ---
main() {
    print_step "Starting $APP_NAME Installation Script"

    readonly BASE_COMMANDS=(
        "git"
        "curl"
    )
    check_commands "${BASE_COMMANDS[@]}" # Exits on error

    create_temp_workdir

    # Change to working directory
    if ! cd "$WORK_DIR"; then
        print_error "Failed to change directory to $WORK_DIR"
    fi

    print_step "Cloning $APP_NAME repository"
    print_info "Source: $REPO_URL"
    if git clone --quiet --depth 1 "$REPO_URL" .; then
        print_success "Repository cloned successfully."
    else
        print_error "Failed to clone repository from $REPO_URL"
    fi

    printf '\n%sHow would you like to install %s?%s\n' "$C_BOLD" "$APP_NAME" "$C_RESET" >&2
    printf '  %s1)%s Flatpak (Sandboxed, user-local install)\n' "$C_YELLOW" "$C_RESET" >&2
    printf '  %s2)%s Local   (local install to %s%s%s, requires GTK dependencies)\n' "$C_YELLOW" "$C_RESET" "$C_BOLD" "$USER_LOCAL_PREFIX" "$C_RESET" >&2

    local INSTALL_METHOD=""
    while [[ "$INSTALL_METHOD" != "1" && "$INSTALL_METHOD" != "2" ]]; do
        if [[ -t 0 ]]; then
            read -rp "Enter your choice (1 or 2): " INSTALL_METHOD </dev/tty

            if [[ "$INSTALL_METHOD" != "1" && "$INSTALL_METHOD" != "2" ]]; then
                print_warning "Invalid input. Please enter '1' or '2'."
            fi
        else
            print_error "Cannot determine installation method non-interactively.\n
                         Please run in a terminal."
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
        print_error "How tf did you get here?"
        ;;
    esac

    check_input_group "$@"
    local group_check_status=$?

    # Ask for logout if check_input_group returns 0
    if [[ "$group_check_status" -eq 0 ]]; then
        prompt_logout
    elif [[ "$group_check_status" -eq 2 ]]; then
        print_error "Failed to handle group membership. Aborting further steps."
    fi

    print_step "$APP_NAME installation script finished successfully"

    # trap will handle cleanup and exit
}

# --- Script Entry Point ---
main "$@"
