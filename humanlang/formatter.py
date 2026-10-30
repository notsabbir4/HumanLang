"""Formatter: one consistent style for every .hum file.

It only changes whitespace: indentation (4 spaces per level), repeated spaces,
trailing spaces, extra blank lines. Comments and text inside quotes are kept.
"""
from .errors import HLError
from .lexer import scan_string


def _squash(line):
    """Collapse runs of spaces/tabs outside quotes into a single space."""
    out, i, pending_space = [], 0, False
    while i < len(line):
        c = line[i]
        if c in " \t":
            pending_space = True
            i += 1
            continue
        if pending_space and out:
            out.append(" ")
        pending_space = False
        if c == '"':
            try:
                _, j = scan_string(line, i, 0)
            except HLError:
                j = len(line)  # broken text: leave the rest exactly as it is
            out.append(line[i:j])
            i = j
        else:
            out.append(c)
            i += 1
    return "".join(out)


def format_source(source):
    entries = []  # (kind, text, indent_in_spaces)
    for raw in source.lstrip("﻿").splitlines():
        raw = raw.rstrip()
        if not raw.strip():
            entries.append(("blank", "", 0))
            continue
        stripped = raw.lstrip(" \t")
        lead = raw[:len(raw) - len(stripped)].replace("\t", "    ")
        kind = "comment" if stripped.startswith("note:") else "code"
        text = stripped if kind == "comment" else _squash(stripped)
        entries.append((kind, text, len(lead)))

    # indentation levels for code lines, using a stack of the indents seen so far
    stack, levels = [0], {}
    for n, (kind, _, indent) in enumerate(entries):
        if kind != "code":
            continue
        while len(stack) > 1 and indent < stack[-1]:
            stack.pop()
        if indent > stack[-1]:
            stack.append(indent)
        levels[n] = len(stack) - 1

    out, last_blank = [], True  # True at the start, so no leading blank lines
    for n, (kind, text, _) in enumerate(entries):
        if kind == "blank":
            if not last_blank:
                out.append("")
            last_blank = True
            continue
        if kind == "code":
            level = levels[n]
        else:  # a comment sits at the level of the next code line
            level = next((levels[m] for m in range(n + 1, len(entries)) if m in levels), 0)
        out.append("    " * level + text)
        last_blank = False
    while out and out[-1] == "":
        out.pop()
    return "\n".join(out) + "\n" if out else ""
