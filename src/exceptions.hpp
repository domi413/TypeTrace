
#ifndef TYPETRACE_EXCEPTIONS_HPP
#define TYPETRACE_EXCEPTIONS_HPP

#include <stdexcept>
#include <string>

namespace typetrace {

class ConfigurationError : public std::runtime_error
{

  public:
    explicit ConfigurationError(const std::string &msg) :
      std::runtime_error("Configuration error: " + msg)
    {
    }
};

class DatabaseError : public std::runtime_error
{
  public:
    explicit DatabaseError(const std::string &msg) : std::runtime_error("Database error: " + msg) {}
};

class PermissionError : public std::runtime_error
{
  public:
    explicit PermissionError(const std::string &msg) :
      std::runtime_error("Permission error: " + msg)
    {
    }
};

class SystemError : public std::runtime_error
{
  public:
    explicit SystemError(const std::string &msg) : std::runtime_error("System error: " + msg) {}
};

} // namespace typetrace

#endif
