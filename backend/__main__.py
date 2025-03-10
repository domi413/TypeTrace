"""Entry point for TypeTrace when run as a module."""

from __future__ import annotations

import sys

from typetrace.cli import main

if __name__ == "__main__":
    sys.exit(main())
