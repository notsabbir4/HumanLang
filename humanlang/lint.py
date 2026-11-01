"""Heads-up warnings: things that run, but probably don't do what the author hoped.

A warning is (line, message, hint), like the ones the parser collects.
Nothing here changes how a program runs.

The one check so far: inside a function, `set x to ...` (or `ask ... and save it as x`) makes a NEW private
variable. If a variable called x already exists outside the function, the outside one is left alone, which is
rarely what the author meant (they wanted `change`). We only warn when an outside x plausibly exists:
it was made before the function was written, or the function reads x before giving it a value.
"""

STATEMENTS = {"say", "set", "change", "changeitem", "add", "subtract", "remove", "addplace", "subtractplace",
              "removeplace", "ask", "if", "while", "times", "for", "define", "give", "stop", "skip", "use",
              "write", "append", "try", "callstmt", "fail", "exit", "setfield", "changefield"}


def lint(stmts):
    warnings = []
    _top(stmts, _assigned(stmts, False), set(), warnings)
    return warnings


def _blocks(s):
    """The statement lists nested inside one statement (not function bodies)."""
    kind = s[0]
    if kind == "if":
        return [body for _cond, body in s[2]] + ([s[3]] if s[3] else [])
    if kind in ("while", "times"):
        return [s[3]]
    if kind == "for":
        return [s[4]]
    if kind == "try":
        return [s[2], s[3]]
    return []


def _own_name(s):
    """The variable a statement creates, if any."""
    if s[0] == "set":
        return s[2]
    if s[0] == "ask":
        return s[4]
    if s[0] == "for":
        return s[2]
    return None


def _assigned(stmts, into_functions):
    """Names given a value by set / ask / for each in this block and the blocks inside it."""
    names = set()
    for s in stmts:
        n = _own_name(s)
        if n:
            names.add(n)
        if s[0] == "define" and into_functions:
            names |= _assigned(s[4], True)
        for block in _blocks(s):
            names |= _assigned(block, into_functions)
    return names


def _is_block(x):
    return (isinstance(x, list) and bool(x) and isinstance(x[0], tuple) and len(x[0]) > 1
            and isinstance(x[0][0], str) and x[0][0] in STATEMENTS and isinstance(x[0][1], int))


def _reads(node):
    """Every variable an expression (or a statement's own expressions) looks at; nested blocks are skipped."""
    found = set()
    if isinstance(node, tuple):
        if len(node) == 2 and node[0] == "var":
            found.add(node[1])
        else:
            for part in node:
                found |= _reads(part)
    elif isinstance(node, list) and not _is_block(node):
        for part in node:
            found |= _reads(part)
    return found


def _free_reads(body, params):
    """Names the function looks at before it has given them a value itself."""
    local, free = set(params), set()

    def visit(stmts):
        for s in stmts:
            if s[0] == "define":
                local.add(s[2])
                continue
            free.update(n for n in _reads(s) if n not in local)
            own = _own_name(s)
            if own:
                local.add(own)
            for block in _blocks(s):
                visit(block)

    visit(body)
    return free


def _top(stmts, everywhere, known, warnings):
    for s in stmts:
        if s[0] == "define":
            _function(s, known, everywhere, warnings, set())
            continue
        own = _own_name(s)
        if own:
            known.add(own)
        for block in _blocks(s):
            _top(block, everywhere, known, warnings)


def _function(s, known, everywhere, warnings, enclosing):
    name, params, body = s[2], set(s[3]), s[4]
    outside = (set(known) | enclosing | (everywhere & _free_reads(body, params))) - params
    _scan(body, outside, name, warnings, set(), params)


def _scan(stmts, outside, function, warnings, seen, params):
    for s in stmts:
        if s[0] == "define":
            _function(s, set(), outside, warnings, outside | _assigned(stmts, False) | params)
            continue
        var = s[2] if s[0] == "set" else s[4] if s[0] == "ask" else None
        if var is not None and var in outside and var not in seen:
            seen.add(var)
            how = f'"set {var} to ..."' if s[0] == "set" else f'"ask ... and save it as {var}"'
            warnings.append((
                s[1],
                f'{how} inside "{function}" makes a new private "{var}"; '
                f'the "{var}" outside the function stays as it is.',
                f'To update the outside "{var}", write: change {var} to ...   '
                f'If you wanted a separate variable, give it another name.'))
        for block in _blocks(s):
            _scan(block, outside, function, warnings, seen, params)
