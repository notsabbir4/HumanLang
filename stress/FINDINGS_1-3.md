# HumanLang stress test, round 1 (programs 1 to 3)

Goal: find where HumanLang becomes hard to use, not just whether it runs long scripts.
Each program was written the way a newcomer would write it, then attacked with hostile input.
Every program was also compared with a Python model on random inputs (`python stress/run_checks.py`).

| # | Program | Size | Checked against Python | Disagreements |
|---|---|---|---|---|
| 1 | `calc.hum` calculator with precedence | 144 lines | 400 random expressions | 0 |
| 2 | `grades.hum` grade manager | 182 lines | 60 random sessions, 158 checks | 0 |
| 3 | `contacts.hum` file-based contact manager | 212 lines | 25 random sessions x 3 separate runs | 0 |

**The interpreter itself was solid.** No crashes, no wrong arithmetic, friendly errors with line numbers,
5000 contacts load and sort in about 0.3 s. Every bug below was either in my own program or a gap in the language
that made a bug easy to write.

## Where the language got hard (worst first)

### 1. `set` inside a function silently makes a new variable (HIGH)
`set tokens to empty list` inside a function does not touch the `tokens` defined outside. It creates a private copy.
No error, no warning. The first run of the calculator printed "please type something" for every input and the
cause was invisible. The right word is `change`, but nothing says so.
*Suggestion:* when a function uses `set` on a name that already exists outside it, warn (or error) and say
"use `change` to update the outer variable, or pick a new name". `hl check` can detect this without running.

### 2. A program cannot raise its own error or stop early (HIGH)
There is no `fail with "message"` and no way to end the whole program outside a loop (`stop` only works in loops).
- The calculator needs a "problem" flag checked after every call: 16 of 144 lines are this plumbing, and 7
  `give back 0` lines exist only to unwind after an error.
- The contact manager needed a `book_ok` flag and an empty-loop trick to simulate "quit the program".
*Suggestion:* `fail with "text"` (catchable by `try ... if that fails`, message in `problem`) and `stop the program`.

### 3. A user function call swallows everything to its right (HIGH)
`f with 2 + 1` means `f(3)`, not `f(2) + 1`. Built-in phrases do the opposite: `length of "abc" times x` means
`(length of "abc") times x`. The reference describes only the built-in rule, so the two behave differently without
warning. In the grade report, `pad with "Name" and 14 plus pad with "Marks" and 5 ...` failed with
"You tried to add text to a number", which is true but does not point at the cause. 20 calls across the grades
and contacts programs needed defensive brackets.
*Suggestion:* make calls end where a calculation would (like built-ins), or document the rule prominently and add
a hint to that error: "a call takes everything after `with`; put the call in brackets".

### 4. No substring, no "find position" (MEDIUM-HIGH)
Text can only be taken apart one letter at a time. Removing a prefix needed a trick, and my first trick
(sort key `name~entry`, then strip by splitting on `~`) broke for the name `Zed~Zee`: it displayed `zee~Zed~Zee`.
Found only because the hostile test used a tilde.
*Suggestion:* phrases like `first 3 letters of X`, `letters 2 to 5 of X`, `position of "x" in X`.

### 5. Files: too little to be safe (MEDIUM-HIGH)
- No "does this file exist": a missing file and an unreadable one give the same "I can't open" error, so my
  program said "No contact file yet" when `contacts.txt` was actually a folder.
- Only "write" which replaces the whole file; no append, no backup, no rename, no delete. My first loader skipped
  damaged lines, so the next save **would have destroyed them** (clear from the code; the test run only listed, so it never
  saved). I changed the program to carry them along, but a newcomer would not think of it.
- `read file` does not accept a leading invisible byte-order mark. A file saved by an editor or exported from Excel
  with a BOM was rejected as "not a contact file". This will matter more for CSV (round 2). CRLF line endings were fine.
*Suggestion:* `file exists PATH`, `add VALUE to file PATH`, read tolerant of a BOM, and a distinct error for "is a folder".

### 6. Dynamic mistakes surface far from their cause (MEDIUM)
`load_book` gave back `nothing` on one path. The crash appeared about 180 lines later at
`how many items in book` ("not nothing"), with no mention of `load_book`. There are no types to catch this early.
*Suggestion:* when a value is `nothing` because a function gave back nothing, say which function:
"`book` is nothing because `load_book` ended without giving back a value."

### 7. No records or dictionaries (MEDIUM, structural)
Grades uses two lists that must stay in step; contacts packs fields into `name|phone|email` text and splits it back
on every access. Removing a student means rebuilding both lists. This is the main thing that grows painful as
programs get bigger. Not a bug, a limit, and it should be on the roadmap.

### 8. Lists inside lists are awkward (MEDIUM)
- Cannot change an inner list in place. Workaround: copy it out, change it, put it back (grades, `add_mark`).
- Writing `add 85 to item 2 of scores` gives a misleading error: `"item" is a word HL already uses, so it can't be a name`.
- `say` of a nested list is ambiguous: `list of list of 90, 80, list of 70, 85`.

### 9. Small things (LOW)
- No test like "is this a number?", so the calculator keeps a parallel `kinds` list.
- No sort by a key: grades has a 35-line hand-written selection sort.
- `sorted` compares by code point, so `Émile` sorts after `Zoe`.
- Reserved words such as `items` and `item` cannot be variable names (hit again while writing the merge sort earlier).

## What worked well
- Errors for ordinary mistakes (divide by zero, bad item number, wrong type) were clear and had line numbers.
- Text, loops, `ask number` re-prompting and `try / if that fails` were easy to use.
- Functions that read outer variables made global state simple, once `change` was used.
- Functions may be called before they are defined (needed for recursion between parse functions).
- UTF-8 names (`Amélie`) and Windows line endings worked.

## Suggested order of fixes
1. Warn when `set` shadows an outer variable inside a function (1).
2. `fail with` and `stop the program` (2).
3. Make call-argument rule consistent with built-ins, or add the hint (3).
4. Substring and position phrases (4).
5. `file exists`, append, BOM tolerance (5).
