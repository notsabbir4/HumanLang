# Changelog

## 0.2.0 - 2026-11-01
Found by stress-testing HumanLang with a calculator, a grade manager and a file-based contact manager
(see `stress/FINDINGS_1-3.md`). Every problem those programs hit is addressed below.

### New
- **Heads-ups.** `hl run`, `hl check`, the editor and the playground now warn when `set` inside a function
  hides a variable of the same name from outside (use `change` to update it). The program still runs the same.
- **`fail with "message"`** raises your own error; `try` catches it. **`stop the program`** ends everything,
  from inside functions and loops too.
- **Records:** `record with name "Ann" and age 30`, `field name of person`, `change field` / `set field`,
  `person has field phone`, `keys of person`, `empty record`, `is a record`.
- **Changing things inside things:** `add 5 to item 2 of scores`, `change item 2 of item 1 of grid to 9`,
  `remove`/`subtract` the same way, and `field KEY of ...` anywhere a place is allowed.
- **Sorting by a field:** `sorted of people by field age`.
- **Text:** `first 3 letters of`, `last 3 letters of`, `letters 2 to 4 of`, `find "x" in text` (position or 0);
  the same on lists with `items`. (`use text`)
- **Files:** `file exists PATH`, `add VALUE to file PATH` (append), clearer errors that tell a missing file from a
  folder or a permission problem, and `read file` and program files skip a leading byte-order mark.
- **Type tests:** `x is a number`, `is a text`, `is a list`, `is a record` (and `is not a ...`).
- **Better error trail:** when `nothing` causes an error later, the message says which function gave it back.
- Nested lists print with brackets, `list of (list of 1, 2), (list of 3)`, so you can tell the nesting.
- Migration hints for `raise`/`throw`, `exit`, `substring`, `indexOf`, `dict`/`struct` and more.

### Breaking (and how to update)
- **`sorted of` text now sorts like a dictionary**: capitals and accents are ignored, so
  `apple, Banana, Émile, Zoe` instead of `Banana, Zoe, apple, Émile`. Numbers are unchanged. Programs that relied on
  capitals sorting first will see a different order.

### Deprecated (will change in a later 0.x version)
- **A function call takes everything to its right as its input** (`f with 2 + 1` is `f with (2 + 1)`), unlike
  the built-in phrases. 0.2.0 only prints a heads-up. To be safe, write `f with (2 + 1)` or `(f with 2) + 1`.

### Fixed
- `hl` and the playground accept program files saved with a byte-order mark (some Windows editors add one).
- Writing to a folder or a file you may not change now says so.

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
