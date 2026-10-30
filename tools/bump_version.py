"""Change the version everywhere it appears.   Usage: python tools/bump_version.py 0.1.2 [--root DIR]"""
import datetime
import json
import os
import re
import sys


def bump(root, new):
    if not re.fullmatch(r"\d+\.\d+\.\d+", new):
        raise SystemExit(f'"{new}" is not a version like 0.1.2')
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
    edit("editors/vscode/package.json", r'"version": "[^"]+"', f'"version": "{new}"')
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
    print("Now: write the changelog lines, run the tests, then: git tag v" + args[0])
