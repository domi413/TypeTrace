### How to run the backend (Frontend is WIP)

- use the make file: `make`

### Command Line Options

```
The backend of TypeTrace
Version: 0.1.0

Usage: ./build/Release/typetrace/backend/typetrace_backend [OPTION…]

Options:
 -h, --help      Display help then exit.
 -v, --version   Display version then exit.
 -d, --debug     Enable debug mode.

Warning: This is the backend and is not designed to run by users.
You should run the frontend of TypeTrace which will run this.
```

### Contribution

- You need [conan](https://conan.io/) installed and in path (CMake will automatically fetch dependencies through conan)
- `gtkmm-4.0` must be installed on your system
- Clang & CMake are required dependencies
- Only works on Linux (Not sure if only x64)
