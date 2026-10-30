"""Entry point used to build the stand-alone `hl` program with PyInstaller."""
import sys

from humanlang.cli import main

if __name__ == "__main__":
    sys.exit(main())
