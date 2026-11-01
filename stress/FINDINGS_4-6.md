# HumanLang stress test, round 2 (programs 4 to 6)

Goal, as in round 1: find where HumanLang becomes hard to use, not just whether it runs long scripts.
Run everything again with `python stress/run_checks_2.py 4 5 speed` and `python stress/breaking.py`.

| # | Program | Size | Checked against Python | Result |
|---|---|---|---|---|
| 4 | `csv_report.hum` reads, cleans and totals a sales CSV | 159 lines | 60 random nasty CSV files | **25 files off by a cent** (see problem 2) |
| 4b | `csv_report_exact.hum`, same program done in whole cents | 193 lines | the same 60 files | 0 disagreements |
| 5 | `project/` library system in 5 modules | 181 lines joined | 40 random sessions | 0 disagreements, but it needed a join script (problem 1) |
| 6 | `breaking.py`, 85 deliberately broken programs | | | 0 Python crashes, 3 runaway programs (problem 3) |

**The interpreter is still solid.** 85 hostile programs gave no Python traceback; almost every message has a line number
and a hint. 20,000 CSV rows (476 KB) took 4 seconds. The trouble this round is not wrong answers from correct
programs, it is that three real-world needs (money, files, limits) have no good answer in the language.

## Where the language got hard (worst first)

### 1. A program cannot be split into files (HIGH, test 5)
`use` only switches on five built-in modules. `use "helpers.hum"`, `use helpers`, `import`, `include` and `run file` all fail, and the
error for `use helpers` lists only the built-in modules, so it never says that your own modules are impossible.
So "a project with several modules" had to be five `.hum` files joined by a script (`stress/project/build.py`) into one program.
Joining shows the next problems at once:
- **Everything is global.** Every module shares one set of names. There are no private helpers and no `util.pad`.
- **A second `define` of the same name silently replaces the first**, and a `define total` silently replaces a variable `total`. No heads-up,
  so two modules that both write `define helper` break each other without a word. (Tried in `c.hum`: `helper with 1` gave 2, then 101.)
- Error line numbers point into the joined file, not into the module you wrote.
- Editors, the tutorial and `hl check` all see one file, so nothing helps you keep modules apart.
*Suggestion:* an `include "file.hum"` (or `use "file.hum"`) statement is the minimum. Better: modules with their own names, a heads-up on a
second `define` of the same name, and line numbers that name the file.

### 2. Numbers are binary fractions, and the display hides it (HIGH, test 4)
`say 0.1 + 0.2` prints `0.3`, but `0.1 + 0.2 is 0.3` is **no**, and so is `19.99 * 100 is 1999`. The display rounds to 10 digits;
the stored value does not. `5 * 1.005` shows `5.025`, but `round of (5 * 1.005 * 100)` is `502`, not `503`.
In the CSV program 25 of 60 random files had at least one money total one cent off (all of them off by exactly one cent).
Nothing warned.
Doing it right (`csv_report_exact.hum`) cost 34 more lines: check the price text is digits, split it on ".", build a whole number and a
count of decimals, and finish with `floor of ((2 * units * whole * 100 + scale) / (2 * scale))`.
Related gaps that made money code long:
- `round` only rounds to whole numbers. There is no "round to 2 places" and no way to print `12.50` (it prints `12.5`), so every money
  program writes its own 8-line `money` helper (`stress/csv_report.hum`, `stress/project/util.hum`).
- There is no whole-number division. `floor of (a / b)` goes through a float, so with a 30-digit unit count the exact program printed
  `1499999999999999889089448902656.10133099161583616` for a total that should end in `...000.00`.
*Suggestion:* keep numbers as exact decimals (or whole numbers while they are whole), or at least make `is`, `round` and `say`
agree with each other; add `round X to N places`; add `A divided evenly by B` and a `text of X with 2 decimals`.

### 3. A program has no limits, and the command line does not stop it (HIGH, test 6)
- `repeat while yes` with nothing in it, or one that only says "spam", runs until killed (Ctrl-C works and prints "Stopped.").
  The playground has an output limit and a Stop button; `hl run` has neither.
- `set t to t + t` sixty times grows without limit: the operating system killed the process (exit -9) with no message at all.
  Under a memory limit the user sees a bare `MemoryError` with no line number.
- The same for `set l to l + l` forty times: no answer within 10 seconds.
*Suggestion:* `hl run --limit` (steps, output, memory), a default memory ceiling that stops with "this text grew past 1 GB, line N",
and the same output limit the playground already has.

### 4. An error inside a function does not say how you got there (MEDIUM, test 5 and 6)
With `outer` calling `middle` calling `inner`, the error is `Line 2: You asked for item 6 ...`, the line inside `inner`, and nothing else.
Passing text to a function that multiplies gives `Line 2: I can only multiply numbers, but this has text and a number.` and never says which call
sent the text. In a 180-line program with 14 functions this is the main thing that slows you down.
*Suggestion:* add "called from line 6 (middle), line 4 (outer), line 8" below the message.

### 5. `try` turns every problem into plain text (MEDIUM, test 5)
`problem` is only text: no line number, no kind. A program cannot tell its own `fail with "no member ann"` from a bug.
My own bug was `if find_book with id` (a number where HL wants yes or no). Inside `try` it was printed like a normal answer,
`error: I expected yes or no here, but got a number.`, six times, and looked like a user mistake. It took a run of the whole session to notice.
The message also gives no hint (the fix is `is not 0`).
*Suggestion:* put the line and a "this is a HumanLang error" flag in `problem`, or give it two parts (`problem` and `problem line`);
add the `is not 0` hint to the yes-or-no error.

### 6. Reading data files is all by hand (MEDIUM, test 4)
There is no CSV reading. The parser is a 48-line state machine that walks the text one letter at a time (the quoted-field rules need
four flags). It works, but it is the longest part of the program and the part a newcomer would never write correctly (quoted commas,
doubled quotes, line breaks inside quotes, a blank line, a short row). Smaller things:
- **Unknown escapes are kept silently.** `"p\rq"` is 4 letters long (a backslash, `r`, and so on) and `replace "\r" by "" in text` quietly does
  nothing. There is no way to write a carriage return, and no error for an escape HL does not know.
  (Reading is safe: `read file` turns Windows line endings into plain ones, so the CSV program handled CRLF.)
- Row numbers in messages count records, not lines in the file, so one quoted line break shifts every later number.
- Hostile files were handled well: empty file, header only, wrong columns, a binary file (clean "doesn't look like a text file"), an
  unclosed quote (the rest of the file becomes one field and is rejected as a short row), 30-digit numbers.
*Suggestion:* `read csv PATH` giving a list of records (using the header), and `write csv`; reject an unknown escape such as `\r` or support it.

### 7. Nested places are strict and the errors don't say so (MEDIUM, test 5)
`change field out of (item at of books) to ...` fails with `I expected a name here but found "("`: a place must be a name, `item N of NAME` or
`field KEY of PLACE`, with no brackets. The sentence the author tried to write is natural; the message does not explain the rule.
Also:
- `remove` works only by value (the first equal item). There is no "remove item 3", so removing a loan means finding the record again.
- A value is copied on `set`. `set loans to field loans of member` then `remove ... from loans` changes the copy and leaves the member alone,
  with no sign anything went wrong. (The project avoids it by naming the place each time.)
- There is no `repeat` that runs forever (`repeat while yes` is needed), and `from` can't be a parameter name (the hint there is fine).

### 8. Small things (LOW)
- `ask`, `repeat "a" times` and similar messages print `but got a` where the value is the text "a"; it reads like a word, not a value.
- `set my-name to 5` says `I expected "to" here but found "-"`; it never mentions that names use letters, digits and `_`.
- `number of "١٢"` (Arabic-Indic digits) gives 12. Python allows it; a beginner would call it a bug.
- `split "abc" by ""` gives letters and `replace "" by "x" in "abc"` gives `xaxbxcx`; both look like mistakes the language should report.
- `join (list of 1, 2) by ","` accepts numbers, while `+` between text and a number is an error: two different rules.
- `ask number` accepts `-0`.

## What worked well
- 85 hostile programs: no crash, every message names its line, and most say how to fix it.
- Stack limits (1000 calls), 1000 nested brackets, 200 nested `if`s, a 200,000-letter line, a BOM, CRLF source, emoji and right-to-left text,
  and a missing or binary file were all fine.
- Ctrl-C stops a runaway program cleanly (`Stopped.`, exit 130).
- Records, `fail with`, `stop the program`, `file exists` and `add ... to file` (round 1 fixes) made both programs short and made the
  library project read well. Random sessions of 5 to 60 commands matched Python in all 40 runs.

## Suggested order of fixes
1. An `include`/`use "file"` statement, plus a heads-up when a name is defined twice (1).
2. Make numbers exact, or make `round`, `is` and `say` agree; add `round to N places` and whole-number division (2).
3. Limits for `hl run`: output, steps and memory (3).
4. "Called from" lines under an error inside a function (4).
5. Line number and kind in `problem`; the `is not 0` hint (5).
6. `read csv` and a clear error for unknown escapes such as `\r` (6).
