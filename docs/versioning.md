# Versioning and stability

HumanLang uses three numbers, `MAJOR.MINOR.PATCH` (for example `0.1.1`). The same number labels the
language, the `hl` program, and the documentation, so there is only one thing to remember.

| Change | Bumps | Promise |
|---|---|---|
| Bug fix, clearer error message, faster, better docs | PATCH | Every program that worked still works, and gives the same output. |
| New phrase, new module, new command | MINOR | Every program that worked still works. |
| Something that can change what a working program does, or stop it working | MAJOR | Listed in `CHANGELOG.md` under "Breaking", with how to update. |

Before 1.0 the language is still being shaped. Minor versions may include breaking changes then, but they are
announced the same way.

## Rules that keep programs working

1. **New words are not reserved.** A new phrase (like `contains` or `sorted of`) is recognised only where it
   makes sense, so programs that already use that word as a name keep working. A word may become reserved
   only in a MAJOR version.
2. **Error message wording is not part of the promise.** It can improve in any release. What *is* promised:
   programs that ran still run, and programs that failed still fail (though perhaps with a better message).
3. **Deprecation takes two steps.** First a release says "this will go away", with the replacement, in the
   changelog and in the docs. The removal comes at least one MINOR release later, and only in a MAJOR
   version once we are past 1.0.
4. **Stable for scripts:** the `.hum` extension, `hl run FILE`, exit code `0` for success and `1` for an error,
   program output on standard output and error messages on standard error.
5. **Not stable:** the output of `hl --trace`, the language server's completion list, and anything in a
   file whose name starts with an underscore.

## How a release happens

1. Update `CHANGELOG.md` (it has one section per version, newest first).
2. Run `python tools/bump_version.py 0.1.2`. It changes the version everywhere it appears and adds the
   changelog heading.
3. `python -m unittest discover -s tests`, then `git tag v0.1.2 && git push --tags`. The release workflow
   builds the programs for each system.

`tests/test_release.py` fails if the version in `pyproject.toml`, `humanlang/__init__.py`, the VS Code
extension and the changelog ever disagree.
