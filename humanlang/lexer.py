"""Lexer: turns HumanLang source text into indented lines of tokens."""
import re

from .errors import HLError
from .hints import CHARACTERS


class Tok:
    __slots__ = ("kind", "value")  # kind: NUM, STR, WORD, OP

    def __init__(self, kind, value):
        self.kind = kind
        self.value = value

    def __repr__(self):
        return f"Tok({self.kind}, {self.value!r})"


class Line:
    __slots__ = ("no", "indent", "toks")

    def __init__(self, no, indent, toks):
        self.no = no
        self.indent = indent  # indentation level (1 level = 4 spaces)
        self.toks = toks


WORD_RE = re.compile(r"[^\W\d]\w*")  # letters (any language), digits and _
NUM_RE = re.compile(r"\d+(?:\.\d+)?")
ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\", "{": "{", "}": "}"}
COMPARE_HINT = ("HL compares with words: is, is not, is less than, "
                "is greater than, is at least, is at most.")


def scan_string(s, i, lineno):
    """Scan a "..." text starting at s[i]. Returns (parts, next_index).

    parts is a list of ("t", literal_text) and ("e", expression_source).
    """
    i += 1
    parts, buf = [], []
    while i < len(s):
        c = s[i]
        if c == '"':
            if buf:
                parts.append(("t", "".join(buf)))
            return parts, i + 1
        if c == "\\" and i + 1 < len(s):
            nxt = s[i + 1]
            buf.append(ESCAPES.get(nxt, "\\" + nxt))
            i += 2
            continue
        if c == "{":
            j, depth = i + 1, 1
            while j < len(s) and depth:
                if s[j] == '"':
                    k = s.find('"', j + 1)
                    if k == -1:
                        break
                    j = k + 1
                    continue
                if s[j] == "{":
                    depth += 1
                elif s[j] == "}":
                    depth -= 1
                j += 1
            if depth:
                raise HLError('This text has a "{" without a matching "}".', lineno,
                              hint='To show a literal brace, write \\{ or \\}.')
            if buf:
                parts.append(("t", "".join(buf)))
                buf = []
            parts.append(("e", s[i + 1:j - 1]))
            i = j
            continue
        buf.append(c)
        i += 1
    raise HLError('This text is missing its closing quote (").', lineno)


def tokenize(s, lineno):
    toks, i, n = [], 0, len(s)
    while i < n:
        c = s[i]
        if c in " \t":
            i += 1
        elif c == '"':
            parts, i = scan_string(s, i, lineno)
            toks.append(Tok("STR", parts))
        elif c.isdigit():
            m = NUM_RE.match(s, i)
            text = m.group()
            toks.append(Tok("NUM", float(text) if "." in text else int(text)))
            i = m.end()
        elif c.isalpha() or c == "_":
            m = WORD_RE.match(s, i)
            toks.append(Tok("WORD", m.group()))
            i = m.end()
        elif c in "+-*/%(),":
            toks.append(Tok("OP", c))
            i += 1
        else:
            hint = None
            if c == "=":
                hint = ("To store a value, write: set name to value.  To compare two things, "
                        "write: name is value  (or: is not, is less than, is greater than, is at least, is at most).")
            elif c in "<>!":
                hint = COMPARE_HINT
            elif c in "“”":
                hint = 'Use straight quotes (") around text.'
            elif c in CHARACTERS:
                hint = CHARACTERS[c]
            raise HLError(f'I don\'t understand the character "{c}".', lineno, hint)
    return toks


def lex(source):
    lines = []
    for no, raw in enumerate(source.lstrip("﻿").splitlines(), 1):
        raw = raw.rstrip()
        stripped = raw.lstrip(" \t")
        if not stripped or stripped.startswith("note:"):
            continue
        lead = raw[:len(raw) - len(stripped)]
        if "\t" in lead:
            raise HLError("Tabs aren't allowed for indenting.", no,
                          hint="Use 4 spaces for each level of indentation, so every file looks the same everywhere.")
        if len(lead) % 4:
            raise HLError(f"This line is indented by {len(lead)} spaces, but indentation must be a multiple of 4.", no,
                          hint="Use exactly 4 spaces for each level.")
        lines.append(Line(no, len(lead) // 4, tokenize(stripped, no)))
    return lines
