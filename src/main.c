/// Main entry point for the TypeTrace backend application

#include "common.h"
#include "database.h"
#include "eventhandler.h"
#include "input_utils.h"
#include "paths.h"
#include "permission_check.h"
#include "version.h"

#include <errno.h>
#include <getopt.h>
#include <libinput.h>
#include <libudev.h>
#include <poll.h>
#include <signal.h>
#include <stdatomic.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

/// Global variables
static volatile atomic_bool running = true;
static struct libinput *global_li = nullptr;
static struct udev *global_udev = nullptr;

/// Debug mode control
bool debug_mode = false;

/// Database path
char db_file_path[MAX_PATH_LENGTH];

/// Forward declaration for signal handler
static void signal_handler(int signal);

// ============================================================================
// Static Functions
// ============================================================================

/// Check user permissions and device accessibility
static int check_permissions(struct libinput *li)
{
    int result = perm_check_input_group_membership();
    if (result != OK) {
        perm_print_permission_help();
        return result;
    }

    result = perm_check_device_accessibility(li);
    if (result != OK) {
        if (result == PERMISSION_ERROR) {
            perm_print_permission_help();
        } else {
            (void)fprintf(stderr, "No accessible input devices available\n");
        }
        return result;
    }

    return OK;
}

/// Clean up libinput and udev contexts
static void cleanup_input(struct libinput *li, struct udev *udev)
{
    DEBUG_PRINT("Cleaning up and exiting...\n");

    // Flush and free keystroke buffer
    db_cleanup_buffer();

    if (li) {
        libinput_unref(li);
    }
    if (udev) {
        udev_unref(udev);
    }
}

/// Initialize libinput and udev contexts
static int initialize_input(struct libinput **li, struct udev **udev)
{
    DEBUG_PRINT("initializing udev...\n");
    *udev = udev_new();
    if (!*udev) {
        (void)fprintf(stderr, "Failed to initialize udev.\n");
        return UDEV_FAILED;
    }
    DEBUG_PRINT("udev initialized successfully.\n");

    DEBUG_PRINT("initializing libinput from udev...\n");
    *li = libinput_udev_create_context(&INPUT_UTILS_LIBINPUT_INTERFACE, nullptr, *udev);
    if (!*li) {
        (void)fprintf(stderr, "Failed to initialize libinput from udev.\n");
        udev_unref(*udev);
        return LIBINPUT_FAILED;
    }
    DEBUG_PRINT("libinput initalized successfully.\n");

    DEBUG_PRINT("Assign seat0 to libinput...\n");
    if (libinput_udev_assign_seat(*li, "seat0") < 0) {
        (void)fprintf(stderr, "Failed to assign seat0 to libinput.\n");
        libinput_unref(*li);
        udev_unref(*udev);
        return SEAT_FAILED;
    }
    DEBUG_PRINT("libinput initialized successfully with seat0.\n");

    return OK;
}

/// Display program usage and help information
static void print_help(const char *program_name)
{
    printf("The backend of TypeTrace\n");
    printf("Version: %s\n", PROJECT_VERSION);
    printf("\nUsage: %s [OPTION…]\n", program_name);
    printf("\nOptions:\n");
    printf("\t-h, --help\tDisplay help then exit.\n");
    printf("\t-v, --version\tDisplay version then exit.\n");
    printf("\t-d, --debug\tEnable debug mode.\n");
    printf("\nWarning: This is the backend and is not designed to run by users.\n"
           "You should run the frontend of TypeTrace which will run this.\n");
}

/// Process command-line arguments
static int process_arguments(int argc, char *const argv[])
{
    const struct option k_long_options[] = {
        { "version", no_argument, nullptr, 'v' },
        {    "help", no_argument, nullptr, 'h' },
        {   "debug", no_argument, nullptr, 'd' },
        {   nullptr,           0, nullptr,   0 }
    };

    for (int opt = getopt_long(argc, argv, "vhd", k_long_options, nullptr); opt != -1;
         opt = getopt_long(argc, argv, "vhd", k_long_options, nullptr)) {

        switch (opt) {
            case 'v':
                printf("%s\n", PROJECT_VERSION);
                return INFORMATION_EXIT;
            case 'h':
                print_help(argv[0]);
                return INFORMATION_EXIT;
            case 'd':
                debug_mode = true;
                (void)fprintf(stderr, "Debug mode enabled\n");
                break;
            default:
                (void)fprintf(stderr, "Invalid option. Use -h or --help for usage.\n");
                return WRONG_ARGUMENT;
        }
    }

    if (optind < argc) {
        (void)fprintf(stderr, "Unexpected non-option arguments: ");
        while (optind < argc) {
            (void)fprintf(stderr, "%s ", argv[optind++]);
        }
        (void)fprintf(stderr, "\nUse -h or --help for usage.\n");
        return WRONG_ARGUMENT;
    }

    return OK;
}

/// Run the main event loop for input handling
static void run_event_loop(struct libinput *li)
{
    // Set up polling for libinput events
    struct pollfd fds = { .fd = libinput_get_fd(li), .events = POLLIN };

    // Main event loop
    while (running) {
        const int poll_result = poll(&fds, 1, POLL_TIMEOUT_MS);

        if (poll_result > 0) {
            if (fds.revents & POLLIN) {
                int result = eh_handle_events(li);
                if (result != OK) {
                    (void)fprintf(stderr,
                                  "Event handling issue with code %d. Continuing...\n",
                                  result);
                    if (fflush(stderr) != 0) {
                        perror("Failed to flush stderr");
                    }
                }
            }
        } else if (poll_result < 0 && errno != EINTR) {
            perror("Poll error");
            break;
        }

        db_check_and_flush_buffer(false);
    }

    db_check_and_flush_buffer(false);
}

/// Initialize the database path and create necessary directories
static int setup_database(void)
{
    if (paths_resolve_db_path(db_file_path, sizeof(db_file_path)) != 0) {
        (void)fprintf(stderr, "Failed to determine database path\n");
        return BUFFER_ERROR;
    }

    if (paths_ensure_db_directories(db_file_path) != 0) {
        (void)fprintf(stderr, "Failed to create database directory\n");
        return BUFFER_ERROR;
    }

    return OK;
}

/// Set up signal handlers for graceful termination
static int setup_signal_handlers(void)
{
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = signal_handler;
    sa.sa_flags = SA_RESTART;
    sigemptyset(&sa.sa_mask);

    // Block all signals during signal handler execution
    sigfillset(&sa.sa_mask);

    // Install signal handlers
    if (sigaction(SIGINT, &sa, nullptr) == -1) {
        perror("Failed to set SIGINT handler");
        return BUFFER_ERROR;
    }

    if (sigaction(SIGTERM, &sa, nullptr) == -1) {
        perror("Failed to set SIGTERM handler");
        return BUFFER_ERROR;
    }

    return OK;
}

/// Signal handler for SIGINT and SIGTERM
static void signal_handler(const int signal)
{
    static volatile sig_atomic_t exiting = 0;

    // Avoid handling the signal twice
    if (exiting) {
        return;
    }
    exiting = 1;

    DEBUG_PRINT("Received signal %d, exiting gracefully...\n", signal);
    (void)fprintf(stderr, "\nReceived interrupt, shutting down gracefully...\n");

    // Flush the keystroke buffer before exiting
    db_check_and_flush_buffer(true);

    // Set running flag to false to break the main loop
    running = false;
}

// ============================================================================
// Public Functions
// ============================================================================

/// Main function for the TypeTrace backend
int main(int argc, char *const argv[])
{
    int result = process_arguments(argc, argv);
    if (result != OK) {
        return result;
    }

    struct libinput *li = nullptr;
    struct udev *udev = nullptr;

    result = initialize_input(&li, &udev);
    if (result != OK) {
        return result;
    }

    result = check_permissions(li);
    if (result != OK) {
        cleanup_input(li, udev);
        return result;
    }

    if (setup_database() != OK) {
        cleanup_input(li, udev);
        return BUFFER_ERROR;
    }
    DEBUG_PRINT("Database path: %s\n", db_file_path);

    // Store in global variables for signal handler
    global_li = li;
    global_udev = udev;

    // Reset the global running flag
    running = true;

    if (setup_signal_handlers() != OK) {
        (void)fprintf(stderr, "Failed to set up signal handlers\n");
        cleanup_input(li, udev);
        return BUFFER_ERROR;
    }

    DEBUG_PRINT("Starting event loop...\n");
    printf("TypeTrace backend started. Press Ctrl+C to exit.\n");
    if (fflush(stdout) != 0) {
        perror("Failed to flush stdout");
    }
    run_event_loop(li);

    cleanup_input(li, udev);

    return OK;
}
