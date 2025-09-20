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

### Contribution

- You need [vcpkg](https://vcpkg.io/en/) installed and in path (CMake will automatically fetch dependencies through vcpkg)
- Clang & CMake are required dependencies
- Only works on Linux (Not sure if only x64)
- First compilation may take some time because vcpkg must install all the libraries
