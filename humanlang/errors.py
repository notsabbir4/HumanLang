"""Friendly errors for HumanLang.

Every error says what went wrong, where, and (when possible) how to fix it.
"""
import difflib


class HLError(Exception):
    def __init__(self, message, line=None, hint=None):
        super().__init__(message)
        self.message = message
        self.line = line
        self.hint = hint
        self.file = None         # the name of the file the line is in, when it is not the main program
        self.source_text = None  # the text of that line, when it is not in the main program
        self.trace = []          # [(function, line it was called from, file of that line)], innermost first
        self.own = False         # True for "fail with" (the program's own problem), False for a mistake HL found

    def where(self):
        return f"line {self.line}" + (f" of {self.file}" if self.file else "")

    def format(self, source_lines=None):
        if self.line:
            head = "Line " + str(self.line) + (f" of {self.file}" if self.file else "") + f": {self.message}"
        else:
            head = self.message
        out = [head]
        if self.source_text is not None:
            out.append("    " + self.source_text.strip())
        elif source_lines and self.line and 1 <= self.line <= len(source_lines):
            out.append("    " + source_lines[self.line - 1].strip())
        if self.hint:
            out.append(self.hint)
        if self.trace:
            out.extend(trace_lines(self.trace))
        return "\n".join(out)


def trace_lines(trace, limit=8):
    """How the program got to the mistake: each function, and the line that called it."""
    names = [t[0] for t in trace]
    steps = []
    for k, (fn, line, file) in enumerate(trace):
        inside = f', inside "{names[k + 1]}"' if k + 1 < len(trace) else ""
        steps.append(f"  line {line}{' of ' + file if file else ''}{inside}")
    if len(steps) > limit:
        steps = steps[:limit - 3] + [f"  ... {len(steps) - limit + 1} more calls ..."] + steps[-2:]
    return [f'This happened inside "{names[0]}", which was called from:'] + steps


def suggest(word, candidates):
    """Return a 'Did you mean ...?' hint, or None."""
    # a much longer name that merely contains the word (secret / make_secret) is not a typo of it
    pool = [c for c in set(candidates) if not (word in c and len(c) - len(word) > 2)]
    matches = difflib.get_close_matches(word, sorted(pool), n=1, cutoff=0.6)
    if matches:
        return f'Did you mean "{matches[0]}"?'
    return None


def format_warning(warning, source_lines=None):
    """A heads-up (line, message, hint) as text, laid out like an error."""
    line, message, hint = warning[:3]
    file = warning[3] if len(warning) > 3 else None  # warnings from another file carry its name and the line's text
    out = [f"Heads up, line {line}{' of ' + file if file else ''}: {message}"]
    if len(warning) > 4:
        out.append("    " + warning[4].strip())
    elif source_lines and line and 1 <= line <= len(source_lines):
        out.append("    " + source_lines[line - 1].strip())
    if hint:
        out.append(hint)
    return "\n".join(out)
