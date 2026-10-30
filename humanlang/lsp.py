"""A small language server for HumanLang (run with `hl lsp`).

Speaks the Language Server Protocol over stdin/stdout, so any LSP editor
(VS Code, Neovim, Helix, Zed ...) can show HL mistakes as you type, offer
completions, and format files.
"""
import json
import re
import sys

from .errors import HLError
from .formatter import format_source
from .lexer import lex
from .parser import MODULES, STATEMENT_WORDS, parse

KEYWORDS = sorted(set(STATEMENT_WORDS) | {
    "otherwise", "while", "each", "in", "with", "and", "or", "not", "is", "yes", "no", "nothing",
    "back", "times", "plus", "minus", "divided by", "mod", "less than", "greater than", "at least",
    "at most", "contains", "to the power of", "list of", "empty list", "item", "how many items in",
    "length of", "uppercase of", "lowercase of", "number of", "text of", "random number from",
    "random item from", "square root of", "absolute value of", "round of", "sum of", "largest of",
    "smallest of", "sorted of", "reversed of", "trim of", "read file", "the date today",
    "the time now", "if that fails", "problem",
})
NAME_PATTERNS = [
    (re.compile(r"^\s*(?:set|change)\s+([^\W\d]\w*)\s+to\b"), 6),
    (re.compile(r"^\s*define\s+([^\W\d]\w*)"), 3),
    (re.compile(r"^\s*for\s+each\s+([^\W\d]\w*)\s+in\b"), 6),
    (re.compile(r"\bsave\s+it\s+as\s+([^\W\d]\w*)"), 6),
]


def diagnose(text):
    """Return a list of LSP diagnostics for the program text."""
    try:
        parse(lex(text))
    except HLError as e:
        lines = text.splitlines()
        n = max((e.line or 1) - 1, 0)
        end = len(lines[n]) if n < len(lines) else 0
        start = len(lines[n]) - len(lines[n].lstrip()) if n < len(lines) else 0
        message = e.message + ("\n" + e.hint if e.hint else "")
        return [{"range": {"start": {"line": n, "character": start}, "end": {"line": n, "character": end}},
                 "severity": 1, "source": "HumanLang", "message": message}]
    return []


def completions(text):
    items = [{"label": k, "kind": 14} for k in KEYWORDS]
    items += [{"label": m, "kind": 9, "detail": "module"} for m in MODULES]
    seen = set()
    for line in text.splitlines():
        for pattern, kind in NAME_PATTERNS:
            m = pattern.search(line)
            if m and m.group(1) not in seen:
                seen.add(m.group(1))
                items.append({"label": m.group(1), "kind": kind,
                              "detail": "function" if kind == 3 else "variable"})
    return items


def read_message(stream):
    length = None
    while True:
        header = stream.readline()
        if not header:
            return None
        header = header.strip()
        if not header:
            break
        if header.lower().startswith(b"content-length:"):
            length = int(header.split(b":", 1)[1])
    if length is None:
        return None
    return json.loads(stream.read(length).decode("utf-8"))


def write_message(stream, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    stream.write(b"Content-Length: " + str(len(body)).encode() + b"\r\n\r\n" + body)
    stream.flush()


def serve(stdin=None, stdout=None):
    stdin = stdin or sys.stdin.buffer
    stdout = stdout or sys.stdout.buffer
    docs = {}
    shutdown = False

    def reply(msg, result=None):
        write_message(stdout, {"jsonrpc": "2.0", "id": msg["id"], "result": result})

    def publish(uri):
        write_message(stdout, {"jsonrpc": "2.0", "method": "textDocument/publishDiagnostics",
                               "params": {"uri": uri, "diagnostics": diagnose(docs[uri])}})

    while True:
        msg = read_message(stdin)
        if msg is None:
            return 0
        method, params = msg.get("method"), msg.get("params") or {}
        if method == "initialize":
            reply(msg, {"capabilities": {
                "textDocumentSync": 1,  # the editor sends the whole file on each change
                "completionProvider": {},
                "documentFormattingProvider": True},
                "serverInfo": {"name": "humanlang"}})
        elif method == "textDocument/didOpen":
            doc = params["textDocument"]
            docs[doc["uri"]] = doc["text"]
            publish(doc["uri"])
        elif method == "textDocument/didChange":
            uri = params["textDocument"]["uri"]
            docs[uri] = params["contentChanges"][-1]["text"]
            publish(uri)
        elif method == "textDocument/didClose":
            uri = params["textDocument"]["uri"]
            docs.pop(uri, None)
            write_message(stdout, {"jsonrpc": "2.0", "method": "textDocument/publishDiagnostics",
                                   "params": {"uri": uri, "diagnostics": []}})
        elif method == "textDocument/completion":
            reply(msg, completions(docs.get(params["textDocument"]["uri"], "")))
        elif method == "textDocument/formatting":
            text = docs.get(params["textDocument"]["uri"], "")
            tidy = format_source(text)
            n = len(text.splitlines())
            edits = [] if tidy == text else [{
                "range": {"start": {"line": 0, "character": 0}, "end": {"line": n + 1, "character": 0}},
                "newText": tidy}]
            reply(msg, edits)
        elif method == "shutdown":
            shutdown = True
            reply(msg, None)
        elif method == "exit":
            return 0 if shutdown else 1
        elif "id" in msg and method:
            write_message(stdout, {"jsonrpc": "2.0", "id": msg["id"],
                                   "error": {"code": -32601, "message": f"Not supported: {method}"}})
