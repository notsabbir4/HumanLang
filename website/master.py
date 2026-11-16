"""Master 2.0 as an interactive course: functions, mistakes and how to catch them, modules, files, calculate and remember, and stepping.

Every exercise is CHECKED BY RUNNING IT in HumanLang (tests/test_courses_interactive.py): the right answer is what HL prints, a fill-in-the-blank
works, a puzzle has exactly one right order, a bug is on the line HL points at.
The shared parts (how an exercise is written, checked and exported) are in website/coursekit.py.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from coursekit import B, C, F, K, O, P, T, W, export_json as _export_json, part, run, unit  # noqa: E402,F401

COURSE = {"id": "master-2", "name": "Master 2.0", "key": "hl-master-2", "exam": 20,
          "lead": "You know the basics. Go deep: your own functions, catching mistakes, modules, files, formulas and memory. Tests after each unit, a grade and a certificate."}

SKILLS = {
    "func": "Writing functions", "call": "Calling functions", "scope": "Inside and outside a function", "recur": "Functions that call themselves",
    "errors": "Reading error messages", "try": "Catching mistakes (try)", "fail": "Making your own errors", "types": "What kind of thing is it?",
    "math": "The math module", "text": "The text module", "money": "Money and decimals", "files": "Files and spreadsheets", "split": "Splitting a program",
    "calc": "Calculating formulas", "memory": "Remembering between runs", "debug": "Stepping through a program",
}

TAGS = {
    "func-define": ("func", "A function is made with define, then its name, then with and the values it needs."),
    "func-giveback": ("func", "give back sends an answer out of the function so you can use it. Without it nothing comes out."),
    "func-indent": ("func", "The lines of a function are indented by 4 spaces."),
    "func-none": ("func", "A function that needs no values is used just by writing its name."),
    "call-with": ("call", "Call a function with its name, then with and the values: double with 4."),
    "call-and": ("call", "Use and between several values: add with 2 and 3."),
    "call-brackets": ("call", "Put brackets around a call that sits inside another: add with 1 and (add with 2 and 3)."),
    "call-math": ("call", "A call takes everything after with. double with 2 + 1 means double with (2 + 1). Use (double with 2) + 1 to calculate after the call."),
    "call-order": ("call", "Define a function first. A call can only use a function that already exists."),
    "scope-private": ("scope", "Variables made inside a function stay inside it. Outside, HL has never heard of them."),
    "scope-change": ("scope", "set always makes a NEW variable. Inside a function, use change to update a variable that lives outside."),
    "recur-base": ("recur", "A function that calls itself needs a way to stop, like if n is at most 1: give back 1."),
    "recur-step": ("recur", "factorial of n is n times factorial of n - 1, until it reaches 1."),
    "errors-line": ("errors", "The first line of an error says what went wrong and the line number. Look at that line first."),
    "errors-typo": ("errors", 'A line starting with a word HL does not know is often a typing mistake. HL says Did you mean "...".'),
    "errors-mix": ("errors", "Text and numbers do not mix. Build text with braces, or turn text into a number with number of."),
    "errors-stack": ("errors", "When a mistake happens inside a function, HL also lists the calls that led to it."),
    "try-after": ("try", "After try ... if that fails, the program keeps going."),
    "try-problem": ("try", "The message is saved in a variable called problem."),
    "try-skip": ("try", "When a line in try fails, the rest of the try lines are skipped and the if that fails lines run."),
    "fail-with": ("fail", "fail with \"message\" raises your own error. Whoever called the function can catch it with try."),
    "fail-kind": ("fail", 'problem_kind is "fail" for your own errors and "error" when HL found a mistake (usually a bug).'),
    "stop-program": ("fail", "stop the program ends the program on purpose, even inside functions and loops."),
    "types-isa": ("types", "x is a number, x is a text, x is a list, x is a record asks what kind of thing x is."),
    "math-use": ("math", "Switch the module on first with use math. Then square root of, sum of, largest of and more work."),
    "math-round": ("math", "round of 2.5 is 3: halves round up."),
    "text-use": ("text", "Switch the module on first with use text. Then split, join, replace, first 3 letters of and find work."),
    "text-find": ("text", "find gives the position (counting from 1), or 0 when the text is not there."),
    "text-pieces": ("text", "first 3 letters of word, last 2 letters of word and letters 2 to 4 of word take a piece of text."),
    "money-places": ("money", "text of X to 2 places makes text with exactly 2 decimals. round of X to 2 places rounds."),
    "money-exact": ("money", "Numbers are exact: 0.1 + 0.2 is exactly 0.3."),
    "money-even": ("money", "A divided evenly by B gives only the whole part of the division."),
    "files-use": ("files", "Switch the module on first with use files."),
    "files-write": ("files", "write replaces the whole file. add ... to file puts text at the end. file exists checks first."),
    "files-csv": ("files", "read csv turns a spreadsheet file into a list of records. Every value is text, so use number of to calculate."),
    "split-use": ("split", 'Move parts of a long program to another file and bring them in with use "money.hum" at the top.'),
    "split-limit": ("split", "hl run --time-limit 10 stops a program that runs too long."),
    "calc-formula": ("calc", "calculate works out a formula written as text, with brackets and the order of operations."),
    "calc-safe": ("calc", "calculate can only do maths, so it is safe on anything a person types. A formula that makes no sense is an error you can catch."),
    "memory-remember": ("memory", "remember saves something so it is still there next time. recall brings it back. forget throws it away."),
    "memory-first": ("memory", "The first time, recall gives nothing. Check for nothing and start with a value."),
    "debug-step": ("debug", "hl debug goes through a program one line at a time and shows which variables changed."),
    "debug-trace": ("debug", "hl run --trace prints each line right before it runs."),
    "other": ("func", "Read the lines again slowly and follow what each one does."),
}

# =====================================================================================================
U1 = unit(1, "Your own functions", "Make a mini-program with a name and use it again and again.", [
    part("Define and call", '''
A **function** is a mini-program with a name. You write it once and use it as often as you like. `define` makes it, `with` lists the values it needs, and `give back` sends an answer out.

```hum
define greet with name
    say "Hello, {name}!"

greet with "Sam"
greet with "Alex"
```

```hum
define double with n
    give back n * 2

say double with 21
set answer to double with 5
say "Ten is {answer}"
```
''',
         P('define double with n\n    give back n * 2\nsay double with 4', "8", [("4", "func-giveback"), ("double", "call-with"), ("n * 2", "func-giveback")], "func", "The function doubles what it is given: 4 * 2 = 8."),
         F('___ greet with name\n    say "Hi {name}"\ngreet with "Ana"', ["define"], "func", "define makes a function.", wrong=[(r"^(function|def|make|create|func)$", "func-define")]),
         W('Write the line that calls greet with "Zoe"', ['greet with "Zoe"'], "call", 'greet with "Zoe" calls the function.', ctx='define greet with name\n    say "Hi {name}"',
           wrong=[(r"^greet\(", "call-with"), (r"^call ", "call-with"), (r'^greet "Zoe"', "call-with")]),
         B('define double with n\n    n * 2\nsay double with 4', 2, "func", "The function needs give back to send the answer out: give back n * 2.", '    give back n * 2',
           goal="8")),
    part("Several values", '''
Use `and` between several values. If one call sits inside another, put brackets around the inner one:

```hum
define add_numbers with a and b
    give back a + b

say add_numbers with 2 and 3
say add_numbers with 1 and (add_numbers with 2 and 3)
```

A call takes **everything after `with`**. `double with 2 + 1` means `double with (2 + 1)`, which is 6. To calculate after the call, put the call in brackets: `(double with 2) + 1` is 5.
''',
         P('define add_numbers with a and b\n    give back a + b\nsay add_numbers with 1 and (add_numbers with 2 and 3)', "6", [("5", "call-brackets"), ("1", "call-and"), ("123", "call-and")], "call",
           "The inner call gives 5, then 1 + 5 = 6."),
         P('define double with n\n    give back n * 2\nsay (double with 2) + 1', "5", [("6", "call-math"), ("4", "call-math"), ("3", "call-math")], "call", "The brackets mean: double 2 first (4), then add 1."),
         T('define area with w and h\n    give back w * h\nsay "Area: {area with 3 and 4}"', "call", "area with 3 and 4 gives 12."),
         O(['define total with a and b', '    give back a + b', 'say total with 4 and 5'], "func", "The function must exist before it is called.")),
], [
    P('define square with n\n    give back n * n\nsay square with 5', "25", [("10", "func-giveback"), ("5", "func-giveback"), ("n * n", "func-giveback")], "func", "5 * 5 = 25."),
    P('define hello\n    say "Hi!"\nhello\nhello', "Hi!\nHi!", [("Hi!", "func-none"), ("hello\nhello", "func-none"), ("", "func-none")], "func", "A function with no values is called by its name. It runs twice."),
    P('define combine with a and b\n    give back a + b\nsay combine with 10 and 5', "15", [("105", "call-and"), ("10", "call-and"), ("5", "call-and")], "call", "10 + 5 = 15."),
    F('define triple with n\n    ___ back n * 3\nsay triple with 4', ["give"], "func", "give back sends the answer out.", wrong=[(r"^(return|send|answer|output)$", "func-giveback")]),
    F('define combine with a and b\n    give back a + b\nsay combine with 2 ___ 3', ["and"], "call", "and goes between the values.", wrong=[(r"^(,|\+|with|plus)$", "call-and")]),
    W('Call double with 8 and say the answer', ['say double with 8'], "call", "say double with 8.", ctx='define double with n\n    give back n * 2', wrong=[(r"^double with 8$", "call-with"), (r"^say double 8", "call-with")]),
    B('say double with 4\ndefine double with n\n    give back n * 2', 1, "call", "The function is defined AFTER it is used. Define it first.", 'define double with n\n    give back n * 2'),
    T('define join_names with a and b\n    give back "{a} and {b}"\nsay join_names with "Ann" and "Bo"', "call", "Both names go into the text."),
])

U2 = unit(2, "Inside and outside", "What a function can see, and a function that calls itself.", [
    part("Private variables", '''
Variables made inside a function stay inside it:

```hum-error
define make_secret
    set secret to 42

make_secret
say secret
```

**Changing a variable from inside a function.** `set` always makes a *new* variable. So inside a function, `set total to ...` makes a private `total` and leaves the outside one alone. To update the outside one, use `change`:

```hum
set total to 0
define add_to_total with n
    change total to total + n

add_to_total with 5
add_to_total with 10
say total
```
''',
         P('define make_secret\n    set secret to 42\nmake_secret\nsay secret', 'Line 4: I don\'t know "secret".', [("42", "scope-private"), ('Line 2: I don\'t know "secret".', "errors-line"), ("Nothing is shown", "scope-private")], "scope",
           "secret only exists inside make_secret. Outside, HL has never heard of it.", error=True),
         K('set total to 0\ndefine add_to_total with n\n    change total to total + n\nadd_to_total with 5\nadd_to_total with 10', "total", "15", ["0", "5", "10"], "scope", "change updates the outside total: 0 + 5 + 10 = 15."),
         K('set total to 0\ndefine add_to_total with n\n    set total to total + n\nadd_to_total with 5', "total", "0", ["5", "15", "nothing"], "scope",
           "set makes a NEW private total inside the function. The outside total stays 0. (HL prints a heads-up about this.)"),
         F('set total to 0\ndefine bump with n\n    ___ total to total + n\nbump with 7\nsay total', ["change"], "scope", "change updates the outside variable.", wrong=[(r"^(set|make|update)$", "scope-change")])),
    part("A function that calls itself", '''
A function can call itself. Here is the factorial of a number (5 factorial is 5 × 4 × 3 × 2 × 1):

```hum
define factorial with n
    if n is at most 1
        give back 1
    give back n * factorial with (n - 1)

say factorial with 5
say factorial with 10
```

It needs a way to **stop** (the `if n is at most 1` part). Without it, it would call itself forever.
''',
         P('define factorial with n\n    if n is at most 1\n        give back 1\n    give back n * factorial with (n - 1)\nsay factorial with 4', "24", [("10", "recur-step"), ("4", "recur-base"), ("1", "recur-base")], "recur", "4 * 3 * 2 * 1 = 24."),
         P('define countdown with n\n    if n is 0\n        say "Go!"\n        give back 0\n    say n\n    give back countdown with (n - 1)\nset done to countdown with 3', "3\n2\n1\nGo!", [("Go!", "recur-base"), ("3\n2\n1", "recur-base"), ("3\n2\n1\n0\nGo!", "recur-base")], "recur",
           "It says 3, 2, 1, then at 0 it says Go! and stops."),
         C("Why does a function that calls itself need an  if  to stop?", "Otherwise it would call itself forever", [("To make it faster", "recur-base"), ("HL asks for it", "recur-base"), ("It does not need one", "recur-base")], "recur",
           "A way to stop is called the base case. Without it the calls never end."),
         F('define factorial with n\n    if n is at most 1\n        give back 1\n    give back n * factorial with (n ___ 1)\nsay factorial with 3', ["-"], "recur", "Each call uses n - 1, so n gets smaller until it stops.", wrong=[(r"^\+$", "recur-step")])),
], [
    K('define bump\n    change n to n + 1\nset n to 0\nbump\nbump\nbump', "n", "3", ["0", "1", "2"], "scope", "bump runs three times and changes the outside n each time."),
    K('define bump\n    set n to 99\nset n to 1\nbump', "n", "1", ["99", "0", "100"], "scope", "set makes a new private n inside bump. The outside n stays 1."),
    P('define area with w and h\n    set result to w * h\n    give back result\nset a to area with 2 and 3\nsay result', "Line 5: I don't know \"result\".", [("6", "scope-private"), ("Line 4: I don't know \"area\".", "scope-private"), ("nothing", "scope-private")], "scope", "result lives only inside area, so outside it HL does not know it.", error=True),
    P('define power with b and e\n    if e is 0\n        give back 1\n    give back b * power with b and (e - 1)\nsay power with 2 and 4', "16", [("8", "recur-step"), ("2", "recur-base"), ("24", "recur-step")], "recur", "2 * 2 * 2 * 2 = 16."),
    P('define sum_to with n\n    if n is 0\n        give back 0\n    give back n + sum_to with (n - 1)\nsay sum_to with 4', "10", [("4", "recur-base"), ("24", "recur-step"), ("0", "recur-base")], "recur", "4 + 3 + 2 + 1 + 0 = 10."),
    F('set score to 0\ndefine win\n    ___ score to score + 10\nwin\nwin\nsay score', ["change"], "scope", "change updates the outside score.", wrong=[(r"^set$", "scope-change")]),
    C("A variable is made inside a function. Where can you use it?", "Only inside that function", [("Anywhere", "scope-private"), ("In every function", "scope-private"), ("Only after the program ends", "scope-private")], "scope", "It stays inside the function."),
    B('define double with n\n    give back n * 2\nsay double with 2 + 1\nsay n', 4, "scope", "n only exists inside double, so HL does not know it out here.", 'say double with (2 + 1)'),
])

U3 = unit(3, "When things go wrong", "Read error messages, and catch mistakes with try.", [
    part("Reading errors", '''
An error message tells you **what** went wrong, **where** (the line number and the line), and often **how to fix it**.

```hum-error
say "Total: " + 5
```

```hum-error
sya "hello"
```

Read the first line, then look at the line it shows. Most mistakes are typos. When the mistake happens inside a function, the message also lists the calls that led to it, so you can see which call sent the bad value.
''',
         P('sya "hello"', 'Line 1: I don\'t understand "sya" at the start of a line.', [('Line 1: I don\'t know "hello".', "errors-typo"), ("hello", "errors-typo"), ("Nothing: it works", "errors-typo")], "errors",
           'HL does not know the word sya, and suggests say.', error=True),
         P('say "Total: " + 5', "Line 1: You tried to add a number to text.", [("Total: 5", "errors-mix"), ("Total: + 5", "errors-mix"), ("Line 1: I don't understand \"say\" here.", "errors-mix")], "errors",
           "Text and numbers do not mix. Use braces: \"Total: {5}\".", error=True),
         B('say "Hello"\nsay "Total: " + 5\nsay "Bye"', 2, "errors", "The first error is on line 2. HL stops there.", 'say "Total: {5}"'),
         C("An error says  Line 7: ...  What do you do first?", "Look at line 7", [("Look at line 1", "errors-line"), ("Run it again", "errors-line"), ("Delete the program", "errors-line")], "errors", "The number tells you where HL got stuck.")),
    part("try and fail", '''
Sometimes you expect something might fail, like dividing by a number a person typed. Put it in `try`, and write what to do `if that fails`. The message is saved in `problem`:

```hum
try
    say 10 / 0
if that fails
    say "Oops: {problem}"
say "The program keeps going."
```

Your program can report a problem itself with `fail with`. A function can use it to refuse bad input, and whoever called the function catches it with `try`:

```hum
define safe_divide with a and b
    if b is 0
        fail with "I can't divide {a} by nothing."
    give back a / b

try
    say safe_divide with 10 and 2
    say safe_divide with 1 and 0
if that fails
    say "Oops: {problem}"
```
''',
         P('try\n    say 10 / 0\nif that fails\n    say "Oops"\nsay "Done"', "Oops\nDone", [("Done", "try-after"), ("Oops", "try-after"), ("Line 2: You can't divide by zero.", "try-after")], "try", "The division fails, so Oops is said. The program keeps going and says Done."),
         P('try\n    say "A"\n    say 1 / 0\n    say "B"\nif that fails\n    say "Failed"', "A\nFailed", [("A\nB", "try-skip"), ("Failed", "try-skip"), ("A\nFailed\nB", "try-skip")], "try", "A is said, then the division fails. B is skipped, and the fail part runs."),
         F('try\n    say 10 / 0\nif that ___\n    say "Oops: {problem}"', ["fails"], "try", "if that fails is what runs when try fails.", wrong=[(r"^(fail|error|breaks|else|otherwise)$", "try-after")]),
         P('define pick with n\n    if n is 0\n        fail with "zero is not allowed"\n    give back n\ntry\n    say pick with 0\nif that fails\n    say "refused: {problem}"', "refused: zero is not allowed", [("zero is not allowed", "try-problem"), ("refused: problem", "try-problem"), ("0", "fail-with")], "fail",
           "fail with raises the error. try catches it, and problem holds the message.")),
], [
    P('try\n    say 5 + 5\nif that fails\n    say "No"', "10", [("No", "try-after"), ("10\nNo", "try-after"), ("5", "try-after")], "try", "Nothing fails, so the if that fails part is skipped."),
    P('try\n    say 10 / 0\nif that fails\n    say problem', "You can't divide by zero.", [("problem", "try-problem"), ("Oops", "try-problem"), ("0", "try-problem")], "try", "problem holds the message."),
    P('say "start"\nstop the program\nsay "end"', "start", [("start\nend", "stop-program"), ("end", "stop-program"), ("", "stop-program")], "fail", "stop the program ends it right there."),
    P('set things to list of 5, "five"\nfor each thing in things\n    if thing is a number\n        say "number"\n    otherwise\n        say "other"', "number\nother", [("number\nnumber", "types-isa"), ("other\nother", "types-isa"), ("number", "types-isa")], "types",
      "5 is a number. The word five is text, so it goes to otherwise."),
    P('define pick with n\n    if n is 0\n        fail with "bad"\n    give back n\ntry\n    say pick with 0\nif that fails\n    say problem_kind', "fail", [("error", "fail-kind"), ("bad", "fail-kind"), ("0", "fail-kind")], "fail", 'Your own fail with makes problem_kind "fail". A mistake HL finds gives "error".'),
    F('try\n    say 10 / 0\n___ that fails\n    say "Oops"', ["if"], "try", "if that fails.", wrong=[(r"^(when|then|catch|on)$", "try-after")]),
    W('Write the line that says the problem', ['say problem'], "try", "problem holds the message.", ctx='try\n    say 10 / 0\nif that fails', indent=1, wrong=[(r"^say message", "try-problem"), (r"^say error", "try-problem")]),
    B('try\n    say 10 / 0\nif that fails\nsay "Oops: {problem}"', 4, "try", "The lines that belong to if that fails need 4 spaces in front.", '    say "Oops: {problem}"'),
])

U4 = unit(4, "More tools: modules", "Switch on the math and text tools.", [
    part("math", '''
Some features are switched on with `use`, to keep things simple until you need them.

| Module | What you get |
|---|---|
| `math` | `square root of`, `absolute value of`, `round of`, `floor of`, `ceiling of`, `sum of`, `largest of`, `smallest of` |
| `text` | `split`, `join`, `replace`, `trim of`, `first 3 letters of`, `last 3 letters of`, `letters 2 to 4 of`, `find` |

```hum
use math
set prices to list of 2.5, 4, 10.25
say "Total: {sum of prices}"
say "Most expensive: {largest of prices}"
say "Square root of 144: {square root of 144}"
say "2.5 rounds to {round of 2.5}"
```

**Money and decimals.** Numbers are exact, so shop arithmetic comes out the way you would do it on paper. `text of X to 2 places` makes text with exactly two decimals, so `12.5` prints as `12.50`. `A divided evenly by B` gives only the whole part of a division.

```hum
use math
say 0.1 + 0.2 is 0.3
set price to 19.99
set total to price * 3
say "Total: {text of total to 2 places}"
say "Whole euros: {total divided evenly by 1}"
```
''',
         P('use math\nsay sum of list of 1, 2, 3', "6", [("123", "math-use"), ("3", "math-use"), ("1 + 2 + 3", "math-use")], "math", "sum of adds up the list: 6."),
         P('use math\nsay largest of list of 4, 9, 2', "9", [("4", "math-use"), ("15", "math-use"), ("2", "math-use")], "math", "largest of gives the biggest item."),
         P('use math\nsay round of 2.5', "3", [("2", "math-round"), ("2.5", "math-round"), ("2.0", "math-round")], "math", "Halves round up, so 2.5 becomes 3."),
         P('say 0.1 + 0.2 is 0.3', "yes", [("no", "money-exact"), ("0.30000000000000004", "money-exact"), ("0.3", "money-exact")], "money", "Numbers are exact, so 0.1 + 0.2 really is 0.3."),
         P('use math\nsay text of 12.5 to 2 places', "12.50", [("12.5", "money-places"), ("12.500", "money-places"), ("12", "money-places")], "money", "text of ... to 2 places always shows two decimals.")),
    part("text", '''
```hum
use text
set words to split "one,two,three" by ","
say words
say join words by " + "
say replace "cat" by "dog" in "the cat sat"
say "[{trim of "   padded   "}]"
```

To take a piece of text, or find where something is:

```hum
use text
set word to "banana"
say first 3 letters of word
say last 2 letters of word
say letters 2 to 4 of word
say find "nan" in word
say find "z" in word
```

`find` gives the position (counting from 1), or `0` when the text isn't there.
''',
         P('use text\nsay first 3 letters of "banana"', "ban", [("ana", "text-pieces"), ("nan", "text-pieces"), ("bana", "text-pieces")], "text", "The first 3 letters of banana are ban."),
         P('use text\nsay find "nan" in "banana"', "3", [("2", "text-find"), ("0", "text-find"), ("yes", "text-find")], "text", "nan starts at the 3rd letter (counting from 1)."),
         P('use text\nsay find "z" in "banana"', "0", [("no", "text-find"), ("nothing", "text-find"), ("-1", "text-find")], "text", "find gives 0 when the text is not there."),
         P('use text\nsay replace "cat" by "dog" in "the cat sat"', "the dog sat", [("the cat sat", "text-use"), ("dog", "text-use"), ("the dog dog", "text-use")], "text", "replace swaps cat for dog.")),
], [
    P('use math\nsay square root of 144', "12", [("72", "math-use"), ("14", "math-use"), ("144", "math-use")], "math", "12 * 12 = 144."),
    P('use math\nsay smallest of list of 8, 3, 6', "3", [("8", "math-use"), ("17", "math-use"), ("6", "math-use")], "math", "smallest of gives the smallest."),
    P('use math\nsay absolute value of -7', "7", [("-7", "math-use"), ("0", "math-use"), ("49", "math-use")], "math", "The absolute value drops the minus sign."),
    P('say 17 divided evenly by 5', "3", [("3.4", "money-even"), ("2", "money-even"), ("4", "money-even")], "money", "5 goes into 17 three whole times."),
    P('use math\nsay round of 3.14159 to 2 places', "3.14", [("3.1", "money-places"), ("3.142", "money-places"), ("3", "money-places")], "money", "to 2 places keeps two decimals."),
    P('use text\nsay join (split "a,b,c" by ",") by "-"', "a-b-c", [("a,b,c", "text-use"), ("abc", "text-use"), ("a-b", "text-use")], "text", "split makes a list, join glues it back with -."),
    P('use text\nsay last 2 letters of "banana"', "na", [("an", "text-pieces"), ("a", "text-pieces"), ("ba", "text-pieces")], "text", "The last 2 letters of banana are na."),
    B('say first 3 letters of "banana"', 1, "text", "first 3 letters of needs the text module switched on: put use text on the line before it.", 'use text\nsay first 3 letters of "banana"',
      goal="ban"),
])

U5 = unit(5, "Files and bigger programs", "Read and write files, read spreadsheets, and split a program.", [
    part("Files", '''
Switch on files with `use files`. `write` replaces the whole file. `add ... to file` puts text at the end instead, and makes the file if it isn't there yet. `file exists` lets you check first.

```hum
use files
write "one\\n" to file "log.txt"
add "two\\n" to file "log.txt"
say read file "log.txt"
say file exists "log.txt"
say file exists "nothing-here.txt"
```
''',
         P('use files\nwrite "Hello from HL" to file "note.txt"\nsay read file "note.txt"', "Hello from HL", [("note.txt", "files-write"), ("Hello", "files-write"), ("", "files-write")], "files", "write saves the text, read file reads it back."),
         P('use files\nwrite "a" to file "f.txt"\nwrite "b" to file "f.txt"\nsay read file "f.txt"', "b", [("a", "files-write"), ("ab", "files-write"), ("a\nb", "files-write")], "files", "write replaces the whole file, so only b is left."),
         P('use files\nwrite "a" to file "f.txt"\nadd "b" to file "f.txt"\nsay read file "f.txt"', "ab", [("a", "files-write"), ("b", "files-write"), ("a b", "files-write")], "files", "add puts text at the end, after the a."),
         P('use files\nsay file exists "nothing-here.txt"', "no", [("yes", "files-write"), ("0", "files-write"), ("Line 2: I can't find the file.", "files-write")], "files", "file exists answers yes or no, and does not fail.")),
    part("Spreadsheets and bigger programs", '''
**Reading a spreadsheet.** A CSV file is a table saved as text. `read csv` turns it into a list of records, one per row, named by the first line (`use files` first). Every value is text, so use `number of` to calculate:

```text
use files
set rows to read csv "sales.csv"
set total to 0
for each row in rows
    add (number of (field units of row)) * (number of (field price of row)) to total
say "Total: {text of total to 2 places}"
```

**Splitting a program into files.** When a program gets long, move parts to other files and bring them in with `use` and the file name in quotes, at the top: `use "money.hum"`.

**Stopping a runaway program.** Ctrl+C stops a program that never ends, or you can give it a limit: `hl run --time-limit 10 myfile.hum`.
''',
         P('use files\nwrite "name,age\\nAnn,5\\nBo,7\\n" to file "p.csv"\nset rows to read csv "p.csv"\nsay how many items in rows', "2", [("3", "files-csv"), ("1", "files-csv"), ("name,age", "files-csv")], "files", "The first line holds the column names, so the 2 rows are Ann and Bo."),
         P('use files\nwrite "item,qty\\napple,2\\npear,3\\n" to file "s.csv"\nset total to 0\nfor each row in read csv "s.csv"\n    add number of (field qty of row) to total\nsay total', "5", [("23", "files-csv"), ("2", "files-csv"), ("0", "files-csv")], "files",
           "Every value is text, so number of turns qty into a number: 2 + 3 = 5."),
         C("How do you bring the functions from  money.hum  into your program?", 'use "money.hum"', [("import money", "split-use"), ("load money.hum", "split-use"), ("include money", "split-use")], "split", 'use with the file name in quotes, at the top.'),
         C("A program never ends. How do you give it a time limit?", "hl run --time-limit 10 myfile.hum", [("hl run --stop 10", "split-limit"), ("hl limit 10", "split-limit"), ("hl run --fast", "split-limit")], "split", "--time-limit 10 stops it after 10 seconds.")),
], [
    P('use files\nwrite "x" to file "a.txt"\nsay file exists "a.txt"', "yes", [("no", "files-write"), ("x", "files-write"), ("a.txt", "files-write")], "files", "The file was just written, so it exists."),
    P('use files\nwrite "1\\n" to file "n.txt"\nadd "2\\n" to file "n.txt"\nsay read file "n.txt"', "1\n2", [("1", "files-write"), ("12", "files-write"), ("2", "files-write")], "files", "Two lines: 1 and 2, each ends with a new line."),
    F('use ___\nwrite "hi" to file "t.txt"\nsay read file "t.txt"', ["files"], "files", "use files switches the file tools on.", wrong=[(r"^(file|disk|io|read)$", "files-use")]),
    F('use files\nwrite "a" to file "t.txt"\n___ "b" to file "t.txt"\nsay read file "t.txt"', ["add"], "files", "add puts text at the end of the file.", wrong=[(r"^(append|more|put)$", "files-write")]),
    P('use files\nwrite "n,v\\na,10\\nb,20\\n" to file "d.csv"\nset total to 0\nfor each row in read csv "d.csv"\n    add number of (field v of row) to total\nsay total', "30", [("1020", "files-csv"), ("10", "files-csv"), ("0", "files-csv")], "files", "10 + 20 = 30."),
    C("What is the first line of a CSV file used for?", "The names of the columns", [("A title", "files-csv"), ("A comment", "files-csv"), ("It is ignored", "files-csv")], "files", "read csv names each value by the first line."),
    B('write "hi" to file "t.txt"\nsay read file "t.txt"', 1, "files", "Files are switched on with use files. Put it on the first line.", 'use files\nwrite "hi" to file "t.txt"', goal="hi"),
    C("Why split a long program into files?", "Each file holds one part, so it is easier to read", [("It runs faster", "split-use"), ("It is smaller", "split-use"), ("HL needs it", "split-use")], "split", "Smaller files are easier to read and reuse."),
])

U6 = unit(6, "Calculate, remember and step", "Formulas from text, memory between runs, and stepping through a program.", [
    part("Formulas", '''
`calculate` works out a formula written as text. It understands brackets and the order of operations (times before plus), so a calculator can take whatever the person types.

```hum
say calculate "2 * (3 + 4)"
say calculate "2 + 3 * 4"
say calculate "10 / 4"
say calculate "sqrt(16) + 2^3"
say calculate "50% * 80"
```

It can only do maths, so it is safe to use on anything a person types. A formula that makes no sense is an error you can catch:

```hum
try
    say calculate "2 +"
if that fails
    say "That is not a formula."
```
''',
         P('say calculate "2 + 3 * 4"', "14", [("20", "calc-formula"), ("9", "calc-formula"), ("2 + 3 * 4", "calc-formula")], "calc", "Times comes before plus: 3 * 4 = 12, then + 2 = 14."),
         P('say calculate "(2 + 3) * 4"', "20", [("14", "calc-formula"), ("11", "calc-formula"), ("9", "calc-formula")], "calc", "Brackets first: 5 * 4 = 20."),
         P('say calculate "10 / 4"', "2.5", [("2", "calc-formula"), ("3", "calc-formula"), ("40", "calc-formula")], "calc", "10 divided by 4 is exactly 2.5."),
         P('try\n    say calculate "2 +"\nif that fails\n    say "Not a formula"', "Not a formula", [("2", "calc-safe"), ("Line 2: I can't calculate that.", "calc-safe"), ("2 +", "calc-safe")], "calc", "2 + has no second number, so calculate fails and the fail part runs.")),
    part("Remembering and stepping", '''
`remember` saves something so it is still there the next time the program runs. `recall` brings it back, and `forget` throws it away. On your computer it is saved in a `.hl-memory` folder next to your program. On a web page it is saved in the browser.

```hum
set visits to recall visits
if visits is nothing
    set visits to 0
add 1 to visits
remember visits
say "You have been here {visits} time(s)."
```

Run it again on your computer and it says 2, then 3. To save something under another name, say `remember score as "high score"` and `recall "high score"`.

**Finding mistakes: step through.** Type `hl debug myprogram.hum` to go through a program one line at a time. You see what each line does in plain words and which variables changed. In the Playground press **Step through**. `hl run --trace myfile.hum` prints each line right before it runs.
''',
         P('set v to recall visits\nif v is nothing\n    set v to 0\nadd 1 to v\nremember v as visits\nsay v', "1", [("0", "memory-first"), ("nothing", "memory-first"), ("2", "memory-first")], "memory", "The first time nothing was remembered, so v starts at 0 and becomes 1."),
         C("What does  recall visits  give the very first time?", "Nothing", [("0", "memory-first"), ("An error", "memory-first"), ("The word visits", "memory-first")], "memory", "Nothing was saved yet, so you get nothing. Check for it and start with a value."),
         C("Which command goes through a program one line at a time?", "hl debug myprogram.hum", [("hl step myprogram.hum", "debug-step"), ("hl slow myprogram.hum", "debug-step"), ("hl check myprogram.hum", "debug-step")], "debug", "hl debug shows each line and what changed."),
         C("What does  hl run --trace  do?", "Prints each line right before it runs", [("Makes the program faster", "debug-trace"), ("Deletes memory", "debug-trace"), ("Runs it twice", "debug-trace")], "debug", "You watch your program think, line by line.")),
], [
    P('say calculate "sqrt(16) + 2^3"', "12", [("6", "calc-formula"), ("10", "calc-formula"), ("24", "calc-formula")], "calc", "sqrt(16) is 4, 2^3 is 8: 4 + 8 = 12."),
    P('say calculate "50% * 80"', "40", [("4000", "calc-formula"), ("130", "calc-formula"), ("50", "calc-formula")], "calc", "50% is half, and half of 80 is 40."),
    P('say calculate "2 * (3 + 4)"', "14", [("10", "calc-formula"), ("24", "calc-formula"), ("9", "calc-formula")], "calc", "Brackets first: 2 * 7 = 14."),
    F('try\n    say ___ "2 +"\nif that fails\n    say "Not a formula"', ["calculate"], "calc", "calculate works out a formula written as text.", wrong=[(r"^(calc|compute|eval|evaluate)$", "calc-formula")]),
    P('remember score\nsay "saved"', 'Line 1: I don\'t know "score".', [("saved", "memory-remember"), ("Nothing", "memory-remember"), ("Line 2: I don't know \"score\".", "memory-remember")], "memory",
      "remember saves a variable, so score has to exist first. Make it with set.", error=True),
    P('set score to 7\nremember score\nforget score\nset back to recall score\nsay back', "nothing", [("7", "memory-remember"), ("0", "memory-remember"), ("score", "memory-remember")], "memory", "forget throws it away, so recall gives nothing."),
    C("What does  remember score as \"high score\"  do?", "Saves score under the name high score", [("Makes a variable called high score", "memory-remember"), ("Prints the score", "memory-remember"), ("Deletes the score", "memory-remember")], "memory", "You can recall it later with recall \"high score\"."),
    C("Which is true about calculate?", "It can only do maths, so it is safe on what a person types", [("It can run any program", "calc-safe"), ("It only works on whole numbers", "calc-safe"), ("It needs use math", "calc-safe")], "calc", "It works out formulas and nothing else, so nobody can sneak a program in."),
])

UNITS = [U1, U2, U3, U4, U5, U6]


def export_json(render_markdown, highlight):
    return _export_json(sys.modules[__name__], render_markdown, highlight)
