"""Heads-up warnings: things that run, but probably don't do what the author hoped.

A warning is (line, message, hint), like the ones the parser collects.
Nothing here changes how a program runs.
"""


def lint(stmts):
    """Find places where a function makes a new private variable that hides one from outside it."""
    warnings = []
    outer = _assigned(stmts, into_functions=False)
    _walk(stmts, outer, None, warnings)
    return warnings


def _blocks(s):
    """The nested statement lists inside one statement (not including function bodies)."""
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


def _assigned(stmts, into_functions):
    """Names given a value by set / ask in this block (and its if/loop/try blocks)."""
    names = set()
    for s in stmts:
        if s[0] == "set":
            names.add(s[2])
        elif s[0] == "ask":
            names.add(s[4])
        elif s[0] == "for":
            names.add(s[2])
        elif s[0] == "define" and into_functions:
            names |= _assigned(s[4], True)
        for block in _blocks(s):
            names |= _assigned(block, into_functions)
    return names


def _walk(stmts, outer, function, warnings, seen=None):
    seen = set() if seen is None else seen
    for s in stmts:
        if s[0] == "define":
            name, params, body = s[2], set(s[3]), s[4]
            # a function inside a function can also see the outer function's own variables
            visible = outer | _assigned(body, False) if function else outer
            _walk(body, visible - params, name, warnings, set())
            continue
        if function is not None:
            var = s[2] if s[0] == "set" else s[4] if s[0] == "ask" else None
            if var is not None and var in outer and var not in seen:
                seen.add(var)
                how = f'"set {var} to ..."' if s[0] == "set" else f'"ask ... and save it as {var}"'
                warnings.append((
                    s[1],
                    f'{how} inside "{function}" makes a new private "{var}"; '
                    f'the "{var}" outside the function stays as it is.',
                    f'To update the outside "{var}", write: change {var} to ...   '
                    f'If you wanted a separate variable, give it another name.'))
        for block in _blocks(s):
            _walk(block, outer, function, warnings, seen)
