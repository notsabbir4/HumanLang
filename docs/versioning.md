# Versioning and stability

HumanLang versions look like `0.3.1`, and sometimes `0.3.1.1`. The same number labels the language, the `hl`
program, the installer, the documentation and the editor extension, so there is only one thing to remember.

How big was the update? Pick one of three sizes:

| Size | What it is | Example | Promise |
|---|---|---|---|
| **Small** | A fix, a clearer message, a docs or website change | `0.3.1` -> `0.3.1.1` (next small one: `0.3.1.2`) | Every program that worked still works, and gives the same output. |
| **Big** | A real update: new phrases, new commands, new features | `0.3.1` -> `0.3.2` | Every program that worked still works. |
| **Massive** | A very large change, or one that can change what a working program does or stop it working | `0.3.1` -> `0.4.1` | Anything that can break a program is listed in `CHANGELOG.md` under "Breaking", with how to update. |

The numbers, left to right: `0.3.1.1` is *language stage* `0`, *massive step* `3`, *big step* `1`, *small step* `1`.
A big update starts the small number over (`0.3.1.2` -> `0.3.2`), and a massive one starts the big number over at `1`
(`0.3.5` -> `0.4.1`). The first number stays `0` until HumanLang is ready to be called 1.0.

Before 1.0 the language is still being shaped. A massive update may include breaking changes then, and
occasionally a big one may too. They are always announced in the changelog.

## Rules that keep programs working

1. **New words are not reserved.** A new phrase (like `contains` or `sorted of`) is recognised only where it
   makes sense, so programs that already use that word as a name keep working. A word may become reserved
   only in a massive update.
2. **Error message wording is not part of the promise.** It can improve in any release. What *is* promised:
   programs that ran still run, and programs that failed still fail (though perhaps with a better message).
3. **Deprecation takes two steps.** First a release says "this will go away", with the replacement, in the
   changelog and in the docs. The removal comes at least one big update later, and once we are past 1.0
   only in a major (first-number) version.
4. **Stable for scripts:** the `.hum` extension, `hl run FILE`, exit code `0` for success and `1` for an error,
   program output on standard output and error messages on standard error.
5. **Not stable:** the output of `hl --trace`, the language server's completion list, and anything in a
   file whose name starts with an underscore.

## How a release happens

1. Decide the size. Run `python tools/bump_version.py small` (or `big`, or `massive`). It works out the new number
   (or you can type one yourself, like `0.3.2`), changes the version everywhere it appears, and adds a changelog
   heading.
2. Fill in the changelog section (`CHANGELOG.md` has one section per version, newest first).
3. Run `python -m unittest discover -s tests` and commit.
4. On GitHub, publish a release with the tag `v` plus the version (for example `v0.3.1.1`). The release workflow
   builds the Windows installer, the programs for each system, and the VS Code extension.
   The website updates by itself every time something is pushed.

The VS Code extension format only has three numbers, so the extension uses the first three of the version
(`0.3.1.1` appears there as `0.3.1`).

`tests/test_release.py` fails if the version in `pyproject.toml`, `humanlang/__init__.py`, the VS Code
extension and the changelog ever disagree.
