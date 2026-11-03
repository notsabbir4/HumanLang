"""Change the version everywhere it appears.

Usage:  python tools/bump_version.py small|big|massive [--root DIR]
        python tools/bump_version.py 0.3.2 [--root DIR]        (or any version you type)

   small    0.3.1   -> 0.3.1.1    a fix, a clearer message, a docs change (again: 0.3.1.1 -> 0.3.1.2)
   big      0.3.1.1 -> 0.3.2      a real update: new phrases, new commands, new features
   massive  0.3.2   -> 0.4.1      a very large change, or one that can break working programs
"""
import datetime
import json
import os
import re
import sys


VERSION = r"\d+\.\d+\.\d+(\.\d+)?"


def next_version(current, size):
    """small: add or raise the 4th number. big: raise the 3rd. massive: raise the 2nd, 3rd starts again at 1."""
    parts = [int(x) for x in current.split(".")]
    major, minor, patch = parts[:3]
    micro = parts[3] if len(parts) > 3 else 0
    if size == "small":
        return f"{major}.{minor}.{patch}.{micro + 1}"
    if size == "big":
        return f"{major}.{minor}.{patch + 1}"
    return f"{major}.{minor + 1}.1"


def current_version(root):
    with open(os.path.join(root, "humanlang", "__init__.py"), encoding="utf-8") as f:
        return re.search(r'__version__ = "([^"]+)"', f.read()).group(1)


def bump(root, new):
    if new in ("small", "big", "massive"):
        new = next_version(current_version(root), new)
    if not re.fullmatch(VERSION, new):
        raise SystemExit(f'"{new}" is not a version like 0.3.2 or 0.3.1.1 (or one of: small, big, massive)')
    changes = []

    def edit(rel, pattern, replacement, flags=0):
        path = os.path.join(root, rel)
        with open(path, encoding="utf-8") as f:
            text = f.read()
        updated, n = re.subn(pattern, replacement, text, count=1, flags=flags)
        if n != 1:
            raise SystemExit(f"could not find the version in {rel}")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(updated)
        changes.append(rel)

    edit("pyproject.toml", r'^version = "[^"]+"', f'version = "{new}"', re.M)
    edit("humanlang/__init__.py", r'__version__ = "[^"]+"', f'__version__ = "{new}"')
    # VS Code only understands three numbers, so the extension uses the first three
    edit("editors/vscode/package.json", r'"version": "[^"]+"', f'"version": "{".".join(new.split(".")[:3])}"')
    path = os.path.join(root, "CHANGELOG.md")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    if f"## {new}" in text:
        raise SystemExit(f"CHANGELOG.md already has a section for {new}")
    stamp = datetime.date.today().isoformat()
    text = text.replace("# Changelog\n", f"# Changelog\n\n## {new} - {stamp}\n- (describe what changed)\n", 1)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    changes.append("CHANGELOG.md")
    json.load(open(os.path.join(root, "editors/vscode/package.json"), encoding="utf-8"))  # still valid JSON
    return changes


if __name__ == "__main__":
    args = sys.argv[1:]
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    if "--root" in args:
        i = args.index("--root")
        root = args[i + 1]
        del args[i:i + 2]
    if len(args) != 1:
        raise SystemExit(__doc__)
    for rel in bump(root, args[0]):
        print("updated", rel)
    new_version_ = current_version(root)
    print("Now: write the changelog lines, run the tests, then publish a release with the tag v" + new_version_)
