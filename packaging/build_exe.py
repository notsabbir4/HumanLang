"""Builds the single-file `hl` program with PyInstaller (used by the release and installer workflows).

HumanLang's own source files go along as data: `hl build` puts them inside a game's web page so the page can run HL itself.
"""
import os
import sys

import PyInstaller.__main__

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(here)
sep = os.pathsep
PyInstaller.__main__.run([
    "--onefile", "--name", "hl", "--icon", os.path.join(here, "icon.ico"),
    "--add-data", f"{os.path.join(root, 'humanlang')}{sep}humanlang_src",
    os.path.join(here, "hl_entry.py"),
])
sys.exit(0)
