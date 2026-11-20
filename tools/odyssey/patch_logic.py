"""Turns logic_v1.hum (hub, World 1, World 5) into logic.hum (all seven worlds)."""
import re

src = open("logic_v1.hum", encoding="utf-8").read()


def span(name):
    m = re.search(r"^define " + re.escape(name) + r"(?: |\n)", src, re.M)
    assert m, name
    start = m.start()
    lines = src[start:].split("\n")
    n = 1
    while n < len(lines) and (lines[n] == "" or lines[n].startswith((" ", "\t"))):
        n += 1
    block = "\n".join(lines[:n])
    return start, start + len(block) + 1


def replace_def(name, new):
    global src
    a, b = span(name)
    src = src[:a] + new.rstrip("\n") + "\n\n" + src[b:]


def sub(old, new, count=1):
    global src
    assert src.count(old) >= 1, old
    src = src.replace(old, new) if count == 0 else src.replace(old, new, count)


def drop_def(name):
    global src
    a, b = span(name)
    src = src[:a] + src[b:]


exec(open("patch_parts.py", encoding="utf-8").read())
open("logic.hum", "w", encoding="utf-8").write(src)
