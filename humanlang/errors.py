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

    def format(self, source_lines=None):
        head = f"Line {self.line}: {self.message}" if self.line else self.message
        out = [head]
        if source_lines and self.line and 1 <= self.line <= len(source_lines):
            out.append("    " + source_lines[self.line - 1].strip())
        if self.hint:
            out.append(self.hint)
        return "\n".join(out)


def suggest(word, candidates):
    """Return a 'Did you mean ...?' hint, or None."""
    # a much longer name that merely contains the word (secret / make_secret) is not a typo of it
    pool = [c for c in set(candidates) if not (word in c and len(c) - len(word) > 2)]
    matches = difflib.get_close_matches(word, sorted(pool), n=1, cutoff=0.6)
    if matches:
        return f'Did you mean "{matches[0]}"?'
    return None
