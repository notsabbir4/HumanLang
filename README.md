<p align="center"><img src="assets/logo.png" alt="HumanLang" width="460"></p>

# HumanLang (HL)

**Code that reads like you talk.** HumanLang is a programming language for people who have never programmed:
plain English sentences, no braces or semicolons, and error messages that tell you how to fix the problem.

```
ask "What is your name?" and save it as name
ask number "How old are you?" and save it as age

if age is at least 18
    say "Welcome, {name}!"
otherwise
    say "Hi {name}, come back in {18 - age} years."
```

```
Line 2: I don't know "nmae".
    say "Hello {nmae}"
Did you mean "name"?
```

- **Try it now:** the website has a playground that runs in your browser, plus a tutorial and a reference.
- **Learn:** [docs/tutorial.md](docs/tutorial.md) (about an hour, every example is tested) and [docs/reference.md](docs/reference.md).

## Install

```
pip install humanlang        # once published; until then: pip install .
hl --version
```

Or download a single program for Windows, macOS or Linux from the Releases page (no Python needed).
More detail: [website/install_page.md](website/install_page.md).

## Use

| Command | What it does |
|---|---|
| `hl` | interactive prompt (arrow keys and history) |
| `hl run FILE.hum` | run a program. Add `--trace` to watch each line as it runs |
| `hl check FILE.hum` | find mistakes in how a program is written, without running it |
| `hl format FILE.hum` | tidy indentation and spacing (`--check` only reports) |
| `hl lsp` | language server: live errors, completion and formatting in any LSP editor |

**VS Code:** copy `editors/vscode` into `~/.vscode/extensions/humanlang`, run `npm install` inside it once,
and restart VS Code. Highlighting works straight away; live errors need `hl` on your PATH
(or set `humanlang.command`, for example to `python3 -m humanlang`).

## Principles

1. One phrase means exactly one thing. No guessing, no silent conversion (`"5" + 1` is an error).
2. Small core: a handful of sentence patterns instead of free-form English.
3. Every error says what went wrong, where, and how to fix it.
4. Indentation is 4 spaces, always. Lists count from 1.

## Develop

```
pip install -e . markdown
python -m unittest discover -s tests      # unit, golden-program, docs-example, website, language-server tests
python tests/fuzz.py 5000                 # random inputs must never crash HL
python website/build.py                   # build the website into website/dist
python tools/docs_fill.py                 # refresh the `output` blocks in docs/ after changing an example
```

Layout: `humanlang/` (lexer, parser, interpreter, errors, formatter, language server, CLI) &middot;
`docs/` &middot; `website/` &middot; `editors/vscode/` &middot; `examples/` &middot; `tests/` &middot; `packaging/`.
See [CONTRIBUTING.md](CONTRIBUTING.md) before changing the language itself.

More: [ROADMAP.md](ROADMAP.md) &middot; [docs/versioning.md](docs/versioning.md) (what stays stable) &middot;
[docs/proposals](docs/proposals/README.md) (how language changes are decided) &middot;
[docs/community.md](docs/community.md) &middot; [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Releasing

`python tools/bump_version.py 0.1.2`, fill in the changelog, then `git tag v0.1.2 && git push --tags`.
The release workflow builds programs for Windows, macOS and Linux and attaches them to the release.

Licensed under the MIT License.
