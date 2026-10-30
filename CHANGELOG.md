# Changelog

## 0.1.1 - 2026-10-29
- Faster: programs run about twice as fast (loops, arithmetic, text, function calls).
- Friendlier errors for people coming from other languages: `print`, `return`, `else`, `elif`, `while`,
  `true`/`false`/`null`, `==`, `&&`, `[ ]`, `len(x)` and more now point to the HL way
  (see "Coming from another language" in the reference).
- Suggestions no longer propose a longer name that merely contains the word you typed.
- New: versioning policy, language-proposal process, roadmap, issue forms and community guide.

## 0.1.0 - first public release
- Language: variables, text with `{...}` interpolation, numbers, yes/no, lists, `if`/`otherwise`,
  `repeat`, `for each`, functions (`define` / `give back`), `try` / `if that fails`.
- Strict types: no silent conversion between text and numbers.
- Friendly errors with "Did you mean ...?" suggestions.
- Modules: `math`, `text`, `files`, `random`, `dates`.
- Tools: `hl run`, `hl check`, `hl format`, `hl run --trace`, REPL, language server (`hl lsp`),
  VS Code extension, in-browser playground.
