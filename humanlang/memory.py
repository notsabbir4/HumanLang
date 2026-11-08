"""Remembering things between runs: `remember score`, `recall score`, `forget score`.

A Memory holds named values. It starts from a saved copy (a file, or the browser's storage) and tells the host when
something changed, so the host can save it again. Values may be numbers, text, yes/no, nothing, lists and records.
"""
import json
import os
from decimal import Decimal

MAX_KEYS = 200
MAX_KEY_LENGTH = 100
MAX_VALUE_CHARS = 100_000
MAX_TOTAL_CHARS = 1_000_000


class MemoryError_(Exception):
    pass


def to_data(v, depth=0):
    """A HumanLang value as plain JSON data. Exact decimals are kept as {"d": "1.25"}."""
    if depth > 40:
        raise MemoryError_("That value has too many things inside each other to remember.")
    if v is None or isinstance(v, (bool, str)):
        return v
    if isinstance(v, int):
        return v
    if isinstance(v, (Decimal, float)):
        return {"d": str(v)}
    if isinstance(v, list):
        return [to_data(x, depth + 1) for x in v]
    if isinstance(v, dict):
        return {"r": {str(k): to_data(x, depth + 1) for k, x in v.items()}}
    raise MemoryError_("I can only remember numbers, text, yes/no, lists and records.")


def from_data(d):
    if isinstance(d, dict):
        if "d" in d and len(d) == 1:
            return Decimal(d["d"])
        if "r" in d and len(d) == 1:
            return {k: from_data(x) for k, x in d["r"].items()}
        return None
    if isinstance(d, list):
        return [from_data(x) for x in d]
    return d


class Memory:
    def __init__(self, data=None, path=None):
        self.data = {}
        self.path = path
        self.changed = False
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except ValueError:
                data = None
        if isinstance(data, dict):
            self.data = {str(k): v for k, v in list(data.items())[:MAX_KEYS]}
        elif path and os.path.isfile(path):
            try:
                with open(path, encoding="utf-8") as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict):
                    self.data = loaded
            except (OSError, ValueError):
                self.data = {}

    def check_key(self, key):
        if not isinstance(key, str) or not key.strip():
            raise MemoryError_("What to remember needs a name.")
        if len(key) > MAX_KEY_LENGTH:
            raise MemoryError_(f"A name to remember can have at most {MAX_KEY_LENGTH} letters.")

    def remember(self, key, value):
        self.check_key(key)
        data = to_data(value)
        text = json.dumps(data)
        if len(text) > MAX_VALUE_CHARS:
            raise MemoryError_(f"That is too much to remember under one name (the limit is {MAX_VALUE_CHARS} letters).")
        if key not in self.data and len(self.data) >= MAX_KEYS:
            raise MemoryError_(f"I can remember at most {MAX_KEYS} different names. Use forget to make room.")
        if sum(len(json.dumps(v)) for k, v in self.data.items() if k != key) + len(text) > MAX_TOTAL_CHARS:
            raise MemoryError_("That is too much to remember in total. Use forget to make room.")
        if self.data.get(key) != data:
            self.data[key] = data
            self.changed = True

    def recall(self, key):
        self.check_key(key)
        return from_data(self.data.get(key))

    def forget(self, key):
        self.check_key(key)
        if key in self.data:
            del self.data[key]
            self.changed = True

    def dump(self):
        return json.dumps(self.data)

    def take_changes(self):
        """The whole saved copy as JSON if anything changed since the last call, else None (the host saves it)."""
        if not self.changed:
            return None
        self.changed = False
        return self.dump()

    def save(self):
        """Write to the file (the command line's way of remembering)."""
        if self.path and self.take_changes() is not None:
            os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
            tmp = self.path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(self.dump())
            os.replace(tmp, self.path)
