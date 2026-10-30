# Contributing to HumanLang

Thank you for helping! HL has one job: be easy for beginners. Every change is judged against that.

## Set up
```
git clone https://github.com/notsabbir4/humanlang && cd humanlang
pip install -e .
python -m unittest discover -s tests      # must pass before you open a pull request
python tests/fuzz.py 5000                 # must report 0 crashes
```

## Changing the language
HL stays small and unambiguous, so syntax changes need more than code:
1. A short example showing why a beginner needs it.
2. One meaning only: the new phrase must not be readable two ways.
3. A friendly error for the most likely mistake with it.
4. Tests (including a bad-input test), and docs in `docs/` (code blocks there are run by the tests).

## Writing docs
Code blocks marked `hum` in `docs/*.md` are executed by `tests/test_docs.py`.
Write the code, leave an empty ```` ```output ```` block under it, then run `python tools/docs_fill.py`
and read what it filled in.

## Error messages
Say what went wrong, where, and how to fix it, in plain English. No jargon (no "token", "syntax error", "parse").

## Versioning
Breaking changes to the language need a major version and a note in `CHANGELOG.md`.
