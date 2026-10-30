"""Fill in the `output` blocks of docs/*.md by running the examples. Read the result afterwards!"""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from docs_runner import fill  # noqa: E402

for path in sorted(glob.glob(os.path.join(os.path.dirname(__file__), "..", "docs", "*.md"))):
    print(f"{os.path.basename(path)}: {fill(path)} output block(s) updated")
