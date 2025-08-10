### How to run the script

- use the make file: `make`

### Command Line Options

```
Usage: ./build/typetrace_backend [OPTION…]
Options:
	-h, --help      Display help then exit.
	-v, --version   Display version then exit.
	-d, --debug	    Enable debug mode.
```

### notes

#### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLI Class                                │
│  - Parses command line arguments                                │
│  - Sets up components based on arguments                        │
│  - Runs main event loop                                         │
│                                                                 │
│  + parseArguments(argc, argv)                                   │
│  + setupComponents()                                            │
│  + run()                                                        │
└─────────────────┬───────────────────────┬───────────────────────┘
                  │                       │
                  │ creates & configures  │ creates & configures
                  │                       │
                  ▼                       ▼
┌─────────────────────────────────┐   ┌─────────────────────────────────┐
│         EventHandler            │   │        DatabaseManager          │
│  - Owns keystroke buffer        │   │  - Handles database operations  │
│  - Reads keyboard events        │   │  - Writes buffer to database    │
│  - Manages flush conditions     │   │                                 │
│  - Notifies when buffer ready   │   │  + writeToDatabase(buffer)      │
│                                 │   │  + createTables()               │
│  + readEvent() -> bool          │   │                                 │
│  + setBufferCallback(callback)  │   └─────────────────────────────────┘
│  + shouldFlush() -> bool        │                   ▲
│                                 │                   │
└─────────────────────────────────┘                   │
                  │                                   │
                  │ callback when buffer ready        │
                  └───────────────────────────────────┘
```

##### Example implementation

```cpp
class CLI {
private:
    std::unique_ptr<DatabaseManager> dbManager;
    std::unique_ptr<EventHandler> eventHandler;

    // CLI-specific data from argument parsing
    std::filesystem::path dbPath;
    bool debugMode = false;
    unsigned int bufferSize = 50;

public:
    auto parseArguments(int argc, char* argv[]) -> bool;
    auto setupComponents() -> void;
    auto run() -> void;
};

class EventHandler {
private:
    std::vector<KeystrokeEvent> buffer;
    std::function<void(const std::vector<KeystrokeEvent>&)> bufferCallback;
    unsigned int maxBufferSize;
    std::chrono::steady_clock::time_point lastFlush;

public:
    auto setBufferCallback(std::function<void(const std::vector<KeystrokeEvent>&)> callback) -> void;
    auto readEvent() -> bool;
    auto shouldFlush() const -> bool;
};

class DatabaseManager {
private:
    std::unique_ptr<sqlite3, decltype(&sqlite3_close)> db;

public:
    explicit DatabaseManager(const std::filesystem::path& dbPath);
    auto writeToDatabase(const std::vector<KeystrokeEvent>& buffer) -> void;
    auto createTables() -> void;
};
```

#### Guidelines

##### Naming Conventions

- Types start with upper case: MyClass.
- Functions and variables start with lower case: myMethod.
- Constants are all upper case: const double PI=3.14159265358979323;.
- Macro names use upper case with underscores: INT_MAX.
- Template parameter names use camel case: InputIterator.
- All other names use snake case: unordered_map.

##### Class Organization

```cpp
class CLI {
public:
    // Constructors/destructors first
    explicit CLI(std::span<char *> args);

    // Core functionality (main purpose)
    auto run() -> void;
    auto parseArguments() -> bool;

    // Getters/setters together
    auto getDebugMode() const -> bool;
    auto setDebugMode(bool mode) -> void;

private:
    // Static functions first (class-level functionality)
    static auto showHelp(const char *program_name) -> void;
    static auto showVersion() -> void;
    [[nodiscard]] static auto getDatabasePath() -> std::filesystem::path;

    // Instance functions (object-specific functionality)
    auto setupComponents() -> void;
    auto cleanup() -> void;

    // Member variables: simple types first, then objects
    bool debug_mode{false};
    int counter{0};

    DatabaseManager db_manager;
    EventHandler event_handler;
};
```

1. **Related functions together** (all help functions, all setup functions)
2. **Getters/setters paired**
3. **Most important functions first**
4. **Alphabetical only within logical groups** (if at all)
5. **Implementation in the cpp file**
6. **Implementation should have the same order as the header file** (if possible)
