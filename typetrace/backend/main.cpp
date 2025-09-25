#include "cli.hpp"

#include <cstdlib>
#include <exception>
#include <iostream>
#include <span>

/// The main entry point of the program
auto main(int argc, char *argv[]) -> int
{
    try {
        typetrace::Cli cli{ std::span<char *>(argv, static_cast<std::size_t>(argc)) };
        cli.run();
    } catch (const std::exception &e) {
        std::cerr << "Error: " << e.what() << "\n";
    }
}
