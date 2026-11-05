# Changelog

## 0.4.1 - 2026-11-06

HumanLang can now **design**. Until now a program could only print words. Now it can show a page with text, buttons,
boxes and grids, draw shapes (a football, a house) and make pixel art (a little person), all in plain words, so a
beginner can make how something looks without learning another language. Clicks and buttons that do things come next.

### New
- **Pages:** `show a page titled "My page"` starts a page, and `put a heading`, `put a text`, `put a button`,
  `put an input`, `put a box` and `put a row` fill it. Looks go after `with`: `background`, `colour`, `size`, `bold`,
  `rounded`, `shadow`, `padding`, `space between`, `columns` (a grid), `width`, `height`, `align` and more. Colours are
  names (`sky blue`, `dark red`), codes like `"#ff8800"`, or a variable holding one.
- **Drawings:** `put a drawing`, then shapes at a spot: `circle`, `oval`, `rectangle`, `square`, `triangle`, `line`,
  `polygon` and `text`.
- **Pixel art:** `put pixel art` with `where "h" is brown` and one line of letters per row of squares.
- Pages are built by a real program, so `for each`, `repeat`, `if`, variables and functions work inside them.
  A calculator's 16 buttons are one loop; a function can draw a ball again and again.
- **See it where you work:** the website Playground shows a **Preview** tab that follows your typing; in VS Code the
  Run button (or "HumanLang: Open design preview") shows a preview beside your code; `hl run` opens the page in your
  browser; `hl build FILE.hum` saves it as one web page (`FILE.html`) you can put on any website; `hl page` gives the
  page to other tools.
- Clear mistakes for pages: unknown colours suggest the right one, a thing that can't have a look lists what it can
  have, pixel-art rows that don't match say which line is wrong.
- New tutorial chapter "Design: pages, buttons and drawings" and a reference section, with the real result shown
  next to every example on the website. Three examples in the Playground: a calculator's looks, a football, a pixel hero.
- Editors: new colours and snippets (`page`, `button`, `drawing`, `pixelart`) in VS Code, and completion for the new words.

### Notes
- The new words (`show a page`, `put a ...`) only mean something at the start of a line in a page, so programs that
  already use `show`, `put` or `page` as names keep working.
- Pages are safe: they contain no scripts, and everything you write is escaped.

## 0.3.1.1 - 2026-11-03

### New
- **Download page.** The website now has real download buttons (it picks your system), a very simple step-by-step
  install guide for Windows, Mac and Linux, and one-line installs for Mac and Linux. The "install with Python" option
  was removed from the page.
- **VS Code extension download.** `HumanLang-VSCode.vsix` is now part of every release. It gives colours, live error
  messages, snippets and a **Run** button (also Ctrl+F5) for `.hum` files.
- **Editors guide.** A new page explains, step by step, how to set up VS Code (and VSCodium, Cursor, Windsurf) and how
  to run HumanLang from Notepad++, Sublime Text, JetBrains editors, Vim/Neovim, Emacs, Helix and Zed, plus language
  server settings for editors that support them.
- **What's new page** on the website, built from this changelog.
- **New game: PROJECT ORPHEUS** on the Games page, and pictures for both games (on the cards and on each game's page).
- **Typing animation in games.** Game text now appears letter by letter, like someone typing, so there is time to
  read it. Click the screen or press Space to skip ahead, and choose Slow, Normal, Fast or Instant. The choice is
  remembered, and people who ask their computer for less motion get Instant.
- Version numbers now follow the rules in `docs/versioning.md`: small `0.3.1` to `0.3.1.1`, big `0.3.1` to `0.3.2`,
  massive `0.3.1` to `0.4.1`. `python tools/bump_version.py small|big|massive` does the bump.

## 0.3.1 - 2026-11-02

### New
- **Windows installer.** Each release now has `HumanLang-Setup.exe`. Double-click it and `.hum` files get the HumanLang
  icon in File Explorer, double-clicking a `.hum` file runs it (the window stays open so you can read the result),
  and you can type `hl` in any terminal. It installs for you only (no administrator password) and uninstalls from
  Windows "Installed apps". Windows may show a "protected your PC" notice because the installer is not signed:
  choose "More info", then "Run anyway".

### Fixed
- The release no longer tries to upload to PyPI (the name `humanlang` there belongs to another project).
- The README install line no longer points to that other project.

## 0.3.0 - 2026-11-02
Found by stress-testing HumanLang with a CSV processor, a five-file project and 94 deliberately broken programs
(see `stress/FINDINGS_4-6.md`). Every problem those programs hit is addressed below.

### New
- **Use other files:** `use "helpers.hum"` brings in another HumanLang file (once, however often it is named; names are
  looked up next to the file that says `use`). Errors, heads-ups and `hl check` name the file and line.
  HL prints a heads-up when a `define` (or `set`) replaces a function or variable of the same name, in any file.
- **Exact numbers.** `0.1 + 0.2 is 0.3` is now `yes`, and money adds up like it does on paper. New phrases:
  `round of X to 2 places`, `text of X to 2 places` (so `12.5` prints as `12.50`), and `A divided evenly by B`
  (the whole part of a division, exact for numbers of any size).
- **Limits and safe stops.** A text or list made by joining is stopped at 50 million letters / 10 million items, a
  program that prints more than 20 million letters is stopped, and running out of memory is a message instead of a
  crash. `hl run --time-limit SECONDS` and `--max-output LETTERS` stop a runaway program, and Ctrl+C says which line
  it was on. `repeat forever` is a loop you leave with `stop`.
- **Where an error happened.** An error inside a function lists the calls that led to it ("called from line 4, inside
  middle").
- **Telling errors apart.** Inside `if that fails`, `problem_line` is the line it happened on and `problem_kind` is
  `"fail"` for your own `fail with` and `"error"` for a mistake HumanLang found. `problem` is unchanged.
- **CSV:** `read csv PATH` (a list of records named by the first line), `read csv PATH as rows`, and
  `write csv LIST to file PATH`. Quoted commas, quotes and line breaks, blank lines, Windows line endings and a
  leading byte-order mark all work.
- **Escapes:** `"\r"` is a carriage return. An escape HL does not know (like `\U` in `"C:\Users"`) now prints a
  heads-up; it still stays as two characters.
- **Places:** brackets around a place work (`change field out of (item at of books) to 9`), and
  `remove item 3 from list` removes by position.
- Clearer messages: text values are quoted (`but got "a"`), `my-name` explains that names use `_`, a number used as
  yes/no suggests `if x is not 0`, and `import`/`include`/`require` point to `use "file.hum"`.

### Breaking (and how to update)
- **Numbers are exact decimals instead of binary floats.** Programs that printed `0.3` for `0.1 + 0.2` still do; what
  changes is that comparisons now agree with what is shown (`0.1 + 0.2 is 0.3` was `no`, and is now `yes`), and
  `round` of values like `5 * 1.005 * 100` follows the exact value. Fractions keep 40 digits, so `1 / 3 * 3 is 1` is
  still `no`. Results beyond 40 digits are rounded and shown like `1.5e+400` (they were `infinity` before 1e308).
- `split TEXT by ""` and `replace "" by ... in TEXT` are now errors (they split into letters / put text between
  every letter, which was almost never meant). To go through the letters, write `for each letter in text`.
- `"\r"` in text is now a carriage return (it was two characters, a backslash and `r`).
- `number of` and `ask number` accept only the digits 0 to 9 (they accepted other scripts' digits, such as Arabic-Indic).

### Still planned
- The rule that a function call takes everything to its right (see 0.2.0) is unchanged and still has a heads-up.

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
