# HumanLang Reference

Everything HL understands, in one place. New to HL? Start with the Tutorial.

## Program basics

- Files end in `.hum` and are read from top to bottom.
- Indent the lines inside `if`, `repeat`, `for each`, `define` and `try` by **exactly 4 spaces**. Tabs are not allowed.
- `note: text` on its own line is a comment.
- A name is letters (any language), digits and `_`, and can't start with a digit. Names are case-sensitive.
- Reserved words can't be names: `say set change add subtract remove ask if otherwise repeat while for in define with give stop skip use try write and or not is yes no nothing list item items of to from times plus minus divided mod then`.

## Values

| Kind | Examples | Notes |
|---|---|---|
| number | `42`, `3.5`, `-7` | whole or decimal, no size limit for whole numbers |
| text | `"Hello"`, `"Hi {name}"` | `{ }` inserts a value; `\"` `\{` `\}` `\\` `\n` `\t` are escapes |
| yes/no | `yes`, `no` | the result of every question |
| list | `list of 1, 2, 3`, `empty list` | ordered, counting from 1 |
| nothing | `nothing` | what a function gives back when it gives back nothing |

HL never converts between kinds silently. `"5" + 1` is an error; use `number of "5"` or `text of 5`.

Lists are copied when stored in a variable or passed to a function.

## Statements

| Statement | Meaning |
|---|---|
| `say VALUE` | show a value |
| `set NAME to VALUE` | create a variable (or replace it) |
| `change NAME to VALUE` | update a variable that must already exist |
| `change item N of NAME to VALUE` | replace one item of a list |
| `add VALUE to NAME` | number: add; text: append; list: add an item at the end |
| `subtract VALUE from NAME` | subtract from a number |
| `remove VALUE from NAME` | remove the first matching item of a list |
| `ask "QUESTION" and save it as NAME` | read a line of text |
| `ask number "QUESTION" and save it as NAME` | read a number (asks again until valid) |
| `if QUESTION` + block | run the block when the answer is `yes` |
| `otherwise if QUESTION` + block | another question, if the ones before were `no` |
| `otherwise` + block | run when all the above were `no` |
| `repeat N times` + block | repeat; N must be a whole number, 0 or more |
| `repeat while QUESTION` + block | repeat while the answer is `yes` |
| `for each NAME in LIST_OR_TEXT` + block | go through items (or letters) one by one |
| `stop` / `skip` | leave the loop / go to its next round (only inside loops) |
| `define NAME with A and B` + block | make a function; `with ...` is left out if it needs no values |
| `give back VALUE` | send a value out of a function (only inside `define`) |
| `NAME with X and Y` | call a function (as a statement or inside a value) |
| `try` + block, then `if that fails` + block | catch an error; its message is in `problem` |
| `use MODULE` | switch on a module |
| `write VALUE to file PATH` | save text to a file (needs `use files`) |

## Questions (conditions)

| Phrase | Meaning |
|---|---|
| `a is b` / `a is not b` | equal / not equal (different kinds are never equal) |
| `a is less than b` / `a is greater than b` | smaller / bigger (two numbers, or two texts) |
| `a is at least b` / `a is at most b` | bigger or equal / smaller or equal |
| `text contains "x"` / `list contains x` | is it inside? |
| `not Q`, `Q and Q`, `Q or Q` | combine questions (`not` first, then `and`, then `or`) |

`if` and `repeat while` need a `yes` or `no`. A plain number or text there is an error.
Only one comparison is allowed per question; use `and` / `or` to combine.

## Calculations

Highest first:

| Order | Symbols | Words |
|---|---|---|
| 1 | `-x` | |
| 2 | `*  /  %` | `times`, `divided by`, `mod`, `to the power of` |
| 3 | `+  -` | `plus`, `minus` |
| 4 | comparisons | `is`, `is less than`, `contains`, ... |
| 5 | | `not` |
| 6 | | `and` |
| 7 | | `or` |

`/` always gives an exact answer (`7 / 2` is `3.5`). `%` and `mod` give the remainder.
Both sides of a calculation must be numbers (except `+`, which also joins two texts or two lists).
`repeat 3 times` and `x times y` don't clash: a line that ends with `times` is a repeat.

## Built-in phrases

Always available:

| Phrase | Result |
|---|---|
| `length of X`, `how many items in X` | letters in text, or items in a list |
| `uppercase of TEXT`, `lowercase of TEXT` | changed case |
| `number of TEXT` | text that looks like a number, as a number |
| `text of X` | any value, as text |
| `item N of X` | the Nth item of a list, or Nth letter of text (from 1) |
| `sorted of LIST`, `reversed of LIST_OR_TEXT` | a new, sorted or reversed copy |
| `random number from A to B` | a whole number from A to B, both included |
| `list of A, B, C`, `empty list` | make a list |

By module (`use math`, and so on):

| Module | Phrases |
|---|---|
| `math` | `square root of X`, `absolute value of X`, `round of X` (0.5 rounds up), `floor of X`, `ceiling of X`, `sum of LIST`, `largest of LIST`, `smallest of LIST` |
| `text` | `split TEXT by SEPARATOR`, `join LIST by SEPARATOR`, `replace OLD by NEW in TEXT`, `trim of TEXT` |
| `random` | `random item from LIST` |
| `dates` | `the date today` (`2026-10-29`), `the time now` (`17:05`) |
| `files` | `read file PATH`, and the statement `write VALUE to file PATH` |

A phrase's value ends where a calculation would: `length of name + 1` means `(length of name) + 1`.
Put brackets around anything longer.

## Functions

- `define` makes a function; its variables are private to it. Functions can read and `change` variables that exist outside.
- Values go in with `with ... and ...`; give nested calls brackets: `add with 1 and (add with 2 and 3)`.
- A function that reaches the end without `give back` gives back `nothing`.
- A function can call itself, up to 1000 levels deep.
- A function with no inputs is used by writing just its name.

## Coming from another language

If you already know Python, JavaScript, Java or similar, these are the HL equivalents. HL also points you here
when you type the other form by mistake.

| You might type | In HL |
|---|---|
| `print("hi")` | `say "hi"` |
| `x = 5` | `set x to 5` (new) or `change x to 5` (existing) |
| `x += 1`, `x++` | `add 1 to x` |
| `x == 5`, `x != 5` | `x is 5`, `x is not 5` |
| `<`, `>`, `<=`, `>=` | `is less than`, `is greater than`, `is at most`, `is at least` |
| `&&`, `\|\|`, `!` | `and`, `or`, `not` |
| `true`, `false`, `null` | `yes`, `no`, `nothing` |
| `if (...) { ... } else { ... }` | `if ...` then `otherwise`, with the lines indented |
| `elif` / `else if` | `otherwise if` |
| `while cond:` | `repeat while cond` |
| `for i in range(3)` | `repeat 3 times` |
| `for x in items` | `for each x in items` |
| `break`, `continue` | `stop`, `skip` |
| `def f(a, b): return a + b` | `define f with a and b` then `give back a + b` |
| `f(1, 2)` | `f with 1 and 2` |
| `[1, 2, 3]`, `items[0]` | `list of 1, 2, 3`, `item 1 of items` (counting starts at 1) |
| `len(x)` | `length of x` or `how many items in x` |
| `str(5)`, `int("5")` | `text of 5`, `number of "5"` |
| `input()` | `ask "Question?" and save it as x` |
| `f"Hi {name}"` | `"Hi {name}"` |
| `# comment` | `note: comment` |
| `try / except` | `try` then `if that fails` (the message is `problem`) |
| `import math` | `use math` |

## Errors

Every error has the same shape:

```text
Line 2: I don't know "nmae".
    say "Hello {nmae}"
Did you mean "name"?
```

| You see | Usually means |
|---|---|
| `I don't know "x".` | a typo in a name, or you haven't made `x` yet with `set` |
| `I don't understand "x" at the start of a line.` | a typo in a command word (`sya` for `say`) |
| `I expected "to" here but found ...` | a missing word; the message shows an example |
| `You tried to add a number to text.` | mixed kinds; use `number of` or `{ }` |
| `I expected yes or no here` | an `if` was given a number or text |
| `I expected an indented block under this line.` | the lines inside an `if`/`repeat`/... aren't indented |
| `Tabs aren't allowed for indenting.` | use 4 spaces |
| `You can't divide by zero.` | exactly that |
| `You asked for item 5, but there are only 2 items.` | list items count from 1 |
| `This needs the "math" module.` | add `use math` near the top |

## Command line

| Command | Does |
|---|---|
| `hl` | interactive prompt (`exit` to leave) |
| `hl run FILE.hum` | run a program (`--trace` shows each line as it runs) |
| `hl check FILE.hum` | find mistakes in how the program is written, without running it |
| `hl format FILE.hum` | tidy spacing and indentation (`--check` only reports) |
| `hl lsp` | language server for editors |
| `hl --version` | show the version |

Exit codes: `0` success, `1` the program or command had an error, `130` stopped with Ctrl+C.

## Grammar

For the curious. `[ x ]` means optional, `{ x }` means repeated.

```text
program      = { statement } ;
statement    = say | set | change | add | subtract | remove | ask | if | repeat
             | while | for | define | give | stop | skip | use | write | try | call ;

say          = "say" expr ;
set          = "set" NAME "to" expr ;
change       = "change" ( NAME | "item" arith "of" NAME ) "to" expr ;
add          = "add" expr "to" NAME ;
subtract     = "subtract" expr "from" NAME ;
remove       = "remove" expr "from" NAME ;
ask          = "ask" [ "number" ] arith "and" "save" "it" "as" NAME ;
if           = "if" expr [ "then" ] block { "otherwise" "if" expr [ "then" ] block } [ "otherwise" block ] ;
repeat       = "repeat" arith "times" block ;
while        = "repeat" "while" expr [ "then" ] block ;
for          = "for" "each" NAME "in" expr block ;
define       = "define" NAME [ "with" NAME { "and" NAME } ] block ;
give         = "give" "back" [ expr ] ;
use          = "use" ( "math" | "random" | "text" | "files" | "dates" ) ;
write        = "write" expr "to" "file" expr ;
try          = "try" block "if" "that" "fails" block ;
call         = NAME [ "with" arith { "and" arith } ] ;
block        = NEWLINE INDENT statement { statement } DEDENT ;

expr         = andExpr { "or" andExpr } ;
andExpr      = notExpr { "and" notExpr } ;
notExpr      = "not" notExpr | comparison ;
comparison   = arith [ "contains" arith
                     | "is" [ "not" ] [ "less than" | "greater than" | "at least" | "at most" ] arith ] ;
arith        = term { ( "+" | "-" | "plus" | "minus" ) term } ;
term         = unary { ( "*" | "/" | "%" | "times" | "divided by" | "mod" | "to the power of" ) unary } ;
unary        = "-" unary | primary ;
primary      = NUMBER | TEXT | "yes" | "no" | "nothing" | NAME | "(" expr ")"
             | "list" "of" arith { "," arith } | "empty" "list"
             | "item" arith "of" primary | call | builtin ;
```
