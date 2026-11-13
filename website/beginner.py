"""Beginner+ as an interactive course (think Duolingo): short teach cards, small exercises, a quick test after every unit,
extra practice built from the mistakes a person makes, a final exam, a grade (A+ ... F) and a certificate.

Every exercise here is CHECKED BY RUNNING IT in HumanLang (tests/test_beginner.py): the right answer really is what HL prints,
a fill-in-the-blank really works, a puzzle has exactly one right order, a bug really is on the line we say.
The page is built from this data (website/courses.py) and played by website/static/learn.js.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from humanlang.errors import HLError  # noqa: E402
from humanlang.interpreter import Interpreter  # noqa: E402

# ---- what a person can be good or bad at ------------------------------------------------------
SKILLS = {
    "say": "Showing things with say", "quotes": "Text needs quotes", "order": "Lines run top to bottom", "notes": "Notes",
    "vars": "Variables (set)", "update": "Changing a variable", "names": "Naming things",
    "join": "Putting values inside text", "math": "Calculating", "textops": "Joining and measuring text", "types": "Text or number?",
    "ask": "Asking questions", "if": "Making decisions", "compare": "Comparing things", "indent": "Indenting lines",
    "repeat": "Repeating things", "lists": "Lists", "foreach": "Going through a list",
    "func": "Functions", "scope": "Variables inside functions", "project": "Putting it together", "debug": "Finding mistakes",
}

# a mistake we can recognise: which skill it belongs to, and what to tell the person
TAGS = {
    "quotes-missing": ("quotes", 'Text goes inside quotes: say "Hello". Without quotes HL thinks Hello is a name.'),
    "quotes-shown": ("quotes", "The quotes are not printed. They only mark where the text starts and ends."),
    "say-shown": ("say", "say is the instruction, so it is not printed. Only what you give to say is shown."),
    "say-word": ("say", "In HumanLang the word that shows something is say (not print or show)."),
    "order-mixed": ("order", "HL runs the lines from the top to the bottom, one by one, in the order they are written."),
    "note-run": ("notes", "A line that starts with note: is only for people. HL skips it."),
    "note-word": ("notes", "A note starts with the word note: and a colon."),
    "var-name-shown": ("vars", "say name shows what is INSIDE the variable, not its name."),
    "set-word": ("vars", "A variable is made with set: set age to 12."),
    "var-before-set": ("vars", "A variable must be made with set before you use it."),
    "update-not-run": ("update", "add, subtract and change really change the variable. Read every line in order."),
    "update-word": ("update", "Use add 1 to x, subtract 1 from x, or change x to something."),
    "update-shown": ("update", "change x to x * 3 means: work out x * 3, then keep the answer in x."),
    "set-vs-change": ("update", "Use change to update a variable that already exists. It catches typing mistakes for you."),
    "name-space": ("names", "A name cannot have spaces. Use an underscore: my_score."),
    "name-digit": ("names", "A name cannot start with a digit. 2nd_place is not allowed, place_2 is."),
    "name-reserved": ("names", "Some words belong to HL (like list, to, item), so they cannot be names."),
    "name-case": ("names", "Names are case-sensitive: Name and name are two different variables."),
    "braces-missing": ("join", "To put a value inside text, wrap it in curly braces: \"Hi {name}\"."),
    "braces-shown": ("join", "HL fills in what is inside { }. The braces themselves are not printed."),
    "braces-calc": ("join", "Anything can go inside the braces, including a calculation: {age + 1}."),
    "math-precedence": ("math", "Multiplication happens before addition, like in maths class. Use brackets to change the order."),
    "math-mod": ("math", "mod is the remainder after dividing: 17 mod 5 is 2."),
    "math-word": ("math", "You can write symbols (+ - * /) or words (plus, minus, times)."),
    "join-space": ("textops", "+ joins text exactly as it is. No space is added."),
    "join-shown": ("textops", "+ between two pieces of text joins them into one."),
    "text-num-mix": ("types", "HL never guesses. Text and numbers do not mix: it stops and tells you."),
    "ask-save": ("ask", "ask needs a place to keep the answer: ask \"Name?\" and save it as name."),
    "ask-word": ("ask", "The word that waits for the person to type is ask."),
    "ask-number": ("ask", "When you need a number to calculate with, use ask number."),
    "ask-shown": ("ask", "The question is shown, then the answer the person typed, then your program carries on."),
    "if-skip": ("if", "The lines under an if only run when the question is yes. Otherwise HL skips them."),
    "if-indent": ("indent", "The lines that belong to an if are indented by 4 spaces."),
    "if-otherwise": ("if", "otherwise runs when the if was not true."),
    "at-least": ("compare", "at least means bigger OR equal. greater than means bigger only."),
    "and-or": ("compare", "and needs BOTH to be yes. or needs at least ONE to be yes."),
    "compare-word": ("compare", "HL compares with words: is, is not, is less than, is greater than, is at least, is at most."),
    "repeat-count": ("repeat", "repeat 3 times runs the lines inside exactly 3 times."),
    "while-update": ("repeat", "Inside repeat while, change something that the question looks at, or it never stops."),
    "while-edge": ("repeat", "Check the last round: is at most 3 includes 3, is less than 3 does not."),
    "stop-skip": ("repeat", "stop leaves the loop for good. skip only jumps to the next round."),
    "loop-body": ("repeat", "Only the indented lines are repeated. The lines after them run once, at the end."),
    "list-from-one": ("lists", "Counting starts at 1: item 1 is the first item."),
    "list-end": ("lists", "add puts the new item at the END of the list."),
    "list-count": ("lists", "how many items in x gives the number of items."),
    "list-copy": ("lists", "When you put a list in another variable, HL makes a copy. Changing the copy leaves the original alone."),
    "list-word": ("lists", "A list is made with: list of a, b, c."),
    "foreach-item": ("foreach", "for each x in list runs the lines once for every item. x is the current item."),
    "foreach-word": ("foreach", "To go through a list, write: for each item in list."),
    "func-define": ("func", "A function is made with define, and the values it needs come after with."),
    "func-giveback": ("func", "give back sends an answer out of the function so you can use it."),
    "func-call": ("func", "Call a function by its name, then with and the values."),
    "func-order": ("func", "Define the function first. A call can only use a function that already exists."),
    "scope-private": ("scope", "Variables made inside a function stay inside it."),
    "scope-change": ("scope", "To update a variable that lives outside the function, use change (set makes a new private one)."),
    "debug-line": ("debug", "The message tells you the line number. Look at that line first."),
    "debug-typo": ("debug", "A name that HL does not know is often a typing mistake. Check the spelling."),
    "debug-step": ("debug", "Step through shows what each line does, and which variables changed."),
    "project-plan": ("project", "Read a program top to bottom, and keep track of every variable as you go."),
    "other": ("project", "Read the lines again slowly and follow what each one does."),
}


def run(code, inputs=()):
    """(output_text, error_text_or_None) exactly as the terminal would show them."""
    out, answers = [], list(inputs)

    def inp(prompt):
        if not answers:
            raise EOFError
        a = answers.pop(0)
        out.append(prompt + a + "\n")
        return a

    interp = Interpreter(out=out.append, inp=inp)
    err = None
    try:
        interp.run(code)
    except HLError as e:
        err = e.format(code.splitlines())
    return "".join(out), err


# ---- how an exercise is written -----------------------------------------------------------------
def _opts(right, wrong):
    o = [{"t": right, "ok": True}]
    for w in wrong:
        t, tag = (w, "other") if isinstance(w, str) else w
        o.append({"t": t, "ok": False, "tag": tag})
    return o


def P(code, right, wrong, skill, why, inputs=(), error=False, q=None):
    """Predict: what does this program print? (error=True: what does HL say?)"""
    return {"kind": "predict", "code": code, "inputs": list(inputs), "error": error, "skill": skill, "why": why, "q": q,
            "options": _opts(right, wrong)}


def T(code, skill, why, inputs=(), q=None):
    """Type what the program prints (the answer is worked out by really running it)."""
    return {"kind": "type", "code": code, "inputs": list(inputs), "skill": skill, "why": why, "q": q}


def F(code, accept, skill, why, wrong=(), inputs=(), q=None):
    """Fill the gap (___) so the program works."""
    return {"kind": "fill", "code": code, "accept": list(accept), "inputs": list(inputs), "skill": skill, "why": why,
            "wrong": list(wrong), "q": q}


def O(lines, skill, why, inputs=(), q=None):
    """Put the lines in order."""
    return {"kind": "order", "lines": list(lines), "inputs": list(inputs), "skill": skill, "why": why, "q": q}


def B(code, bad, skill, why, fix, goal=None, inputs=(), q=None):
    """Tap the line that has the mistake. fix = the corrected line. goal = what it should print (when the bug is silent)."""
    return {"kind": "bug", "code": code, "bad": bad, "fix": fix, "goal": goal, "inputs": list(inputs), "skill": skill,
            "why": why, "q": q}


def W(task, accept, skill, why, wrong=(), ctx="", goal=None, inputs=()):
    """Write one line of HumanLang."""
    return {"kind": "write", "task": task, "accept": list(accept), "ctx": ctx, "goal": goal, "inputs": list(inputs), "skill": skill,
            "why": why, "wrong": list(wrong)}


def K(code, var, right, wrong, skill, why):
    """Trace: after the last line has run, what is in a variable? (this is what Step through shows you)"""
    return {"kind": "trace", "code": code, "var": var, "inputs": [], "skill": skill, "why": why, "options": _opts(right, wrong)}


def C(q, right, wrong, skill, why, code=None):
    """A plain multiple-choice question (with an optional program to look at)."""
    return {"kind": "choose", "q": q, "code": code, "inputs": [], "skill": skill, "why": why, "options": _opts(right, wrong)}


def part(title, teach, *ex):
    return {"title": title, "teach": teach.strip("\n") + "\n", "ex": list(ex)}


def unit(n, title, blurb, parts, bank):
    return {"n": n, "title": title, "blurb": blurb, "parts": parts, "bank": bank}


# =====================================================================================================
# THE UNITS
# =====================================================================================================
U1 = unit(1, "Say hello", "Make HumanLang say things.", [
    part("Say it", '''
A program is a list of instructions for the computer. The first one you learn is **say**. It shows something on the screen.

```hum
say "Hello, world!"
```

The words inside the quotes are called **text**. The quotes are not shown. They only tell HL where the text starts and ends.
''',
         P('say "Hi there"', "Hi there", [('"Hi there"', "quotes-shown"), ('say "Hi there"', "say-shown"), ("Hi", "other")],
           "quotes", "The quotes only mark the text. HL shows what is inside them: Hi there."),
         F('___ "Good morning"', ["say"], "say", "say is the word that shows something on the screen.",
           wrong=[(r"^(print|show|display|echo)$", "say-word")]),
         W("Write a line that makes HL show: Hello", ['say "Hello"'], "quotes", 'Write say, then the text inside quotes: say "Hello".',
           wrong=[(r"^say\s+Hello$", "quotes-missing"), (r"^(print|show|display)\b", "say-word")], goal="Hello")),
    part("Many lines", '''
A program can have many lines. HL runs them **from top to bottom**, one at a time.

```hum
say "Hello!"
say "My name is HumanLang."
say "Nice to meet you."
```
''',
         T('say "One"\nsay "Two"\nsay "Three"', "order", "Each say shows its text on its own line, in the order the lines are written."),
         O(['say "First"', 'say "Second"', 'say "Third"'], "order", "HL runs the lines in the order they are written, so the order you choose is the order you see.",
           q="Put the lines in the right order so the program shows First, Second, Third."),
         B('say "Hello"\nsay Bye', 2, "quotes", "Text needs quotes. Without them HL thinks Bye is a name it should already know.",
           'say "Bye"')),
    part("Notes", '''
You can leave a note for yourself or for other people. A line that starts with `note:` is **ignored** by the computer.

```hum
note: this line does nothing, it is only for people
say "Notes are free"
```
''',
         P('note: say "Surprise"\nsay "Hi"', "Hi", [("Surprise", "note-run"), ("Surprise\nHi", "note-run")], "notes",
           "The first line is a note, so HL skips it completely. Only the second line runs."),
         C("What is a note: line for?", "A message for people. The computer ignores it.",
           [("It shows text on the screen", "note-run"), ("It makes the program run faster", "other")], "notes",
           "Notes explain your program to people (including you, next week). HL ignores them."),
         W("Write a note that says: this shows a greeting", ["note: this shows a greeting"], "notes", "A note starts with note: and then anything you like.",
           wrong=[(r"^(#|//|--)", "note-word"), (r"^note\s+[^:]", "note-word")])),
], [
    P('say "A"\nsay "B"', "A\nB", [("AB", "order-mixed"), ("B\nA", "order-mixed"), ('"A"\n"B"', "quotes-shown")], "order",
      "Two lines, two say instructions: A first, then B, each on its own line."),
    T('say "Cats"\nsay "and"\nsay "dogs"', "order", "Three say lines, three lines of output, in order."),
    F('say "Welcome"\n___ "Enjoy"', ["say"], "say", "Every line that shows something starts with say.", wrong=[(r"^(print|show|echo)$", "say-word")]),
    W("Make HL show: Good night", ['say "Good night"'], "quotes", 'say, then the text in quotes: say "Good night".',
      wrong=[(r"^say\s+Good night$", "quotes-missing"), (r"^(print|show)", "say-word")], goal="Good night"),
    B('say "Start"\nnote this is a note\nsay "End"', 2, "notes", "A note needs note: with a colon. Without the colon HL tries to run it as an instruction.",
      "note: this is a note"),
    O(['say "3"', 'say "2"', 'say "1"', 'say "Go!"'], "order", "The order of the lines is the order of the output.", q="Make the countdown: 3, 2, 1, Go!"),
    C("How does HL run the lines of a program?", "From top to bottom, one line at a time",
      [("From bottom to top", "order-mixed"), ("All lines at the same moment", "order-mixed"), ("In any order it likes", "order-mixed")], "order",
      "HL goes down the page, one line at a time. That is why the order matters."),
])

U2 = unit(2, "Remember things", "Keep a value with a name, like a box with a label.", [
    part("Variables", '''
A **variable** is a name for a value, like a label on a box. `set` makes one:

```hum
set name to "Sam"
set age to 20
say name
say age
```

`say name` shows what is **inside** the variable, so it shows Sam, not the word name.
''',
         P('set name to "Mia"\nsay name', "Mia", [("name", "var-name-shown"), ('"Mia"', "quotes-shown"), ("set name to Mia", "say-shown")], "vars",
           "name is a box that holds Mia. say name shows what is in the box."),
         F('___ age to 12\nsay age', ["set"], "vars", "set makes a variable: set age to 12.", wrong=[(r"^(let|var|make|put|int)$", "set-word")]),
         T('set city to "Dhaka"\nset year to 2026\nsay city\nsay year', "vars", "Each say shows what is inside its variable, in the order of the say lines.")),
    part("Change them", '''
Use `add`, `subtract` and `change` to update a variable that already exists:

```hum
set score to 10
add 5 to score
subtract 2 from score
say score
change score to score * 2
say score
```
''',
         P('set score to 10\nadd 5 to score\nsay score', "15", [("10", "update-not-run"), ("105", "update-not-run"), ("5", "update-not-run")], "update",
           "score starts at 10. add 5 to score makes it 15."),
         F('set lives to 3\n___ 1 from lives\nsay lives', ["subtract"], "update", "subtract 1 from lives takes one away: 3 becomes 2.",
           wrong=[(r"^(remove|minus|take|sub|decrease)$", "update-word")]),
         P('set x to 4\nchange x to x * 3\nsay x', "12", [("4", "update-not-run"), ("x * 3", "update-shown"), ("7", "update-shown")], "update",
           "change x to x * 3 works out 4 * 3 = 12, then keeps 12 in x.")),
    part("Good names", '''
**Rules for names**

- Use letters, digits and `_`, with **no spaces**: `total_price`, `age2`.
- A name can't start with a digit.
- Names are **case-sensitive**, so `Name` and `name` are different.
- A few words are taken by HL itself (like `list`, `to`, `item`).
''',
         C("Which one is a good variable name?", "total_price",
           [("total price", "name-space"), ("2nd_place", "name-digit"), ("list", "name-reserved")], "names",
           "total_price has no spaces, does not start with a digit and is not a word HL uses."),
         B('set my score to 5\nsay "Saved"', 1, "names", "A name cannot have spaces. Use an underscore: my_score.", "set my_score to 5"),
         P('set Name to "Ana"\nset name to "Zed"\nsay Name', "Ana", [("Zed", "name-case"), ("Ana\nZed", "name-case"), ("Name", "var-name-shown")], "names",
           "Name and name are two different variables. say Name shows Ana.")),
], [
    P('set pet to "cat"\nsay pet', "cat", [("pet", "var-name-shown"), ('"cat"', "quotes-shown")], "vars", "say pet shows what is inside pet."),
    W("Make a variable called age with the value 12", ["set age to 12"], "vars", "set, the name, to, the value: set age to 12.",
      wrong=[(r"^age\s*=\s*12$", "set-word"), (r"^(let|var)\b", "set-word"), (r"^set age 12$", "set-word")]),
    W("Add 5 to the variable score", ["add 5 to score"], "update", "add 5 to score.", ctx="set score to 1",
      wrong=[(r"^score\s*(\+=|=)", "update-word"), (r"^add score", "update-word")]),
    B('set total to 1\nchange totl to 2\nsay total', 2, "update", "totl is a typing mistake. change only works on a variable that exists, so HL tells you.",
      "change total to 2"),
    P('set a to 2\nset b to 3\nadd b to a\nsay a', "5", [("2", "update-not-run"), ("3", "update-not-run"), ("23", "update-not-run")], "update",
      "add b to a puts 2 + 3 = 5 into a."),
    T('set coins to 5\nsubtract 2 from coins\nadd 10 to coins\nsay coins', "update", "5 - 2 = 3, then 3 + 10 = 13."),
    C("Which line makes a variable that does not exist yet?", "set size to 3", [("change size to 3", "set-vs-change"), ("add 3 to size", "set-vs-change")],
      "vars", "set makes a new variable. change, add and subtract need one that already exists."),
])

U3 = unit(3, "Text and numbers", "Words, numbers and how to put them together.", [
    part("Values inside text", '''
Put a value inside text by wrapping it in `{ }`. HL fills it in:

```hum
set name to "Sam"
set age to 20
say "Hi {name}, next year you will be {age + 1}."
```

Anything can go inside the braces, including a calculation.
''',
         P('set name to "Sam"\nsay "Hi {name}!"', "Hi Sam!", [("Hi name!", "braces-missing"), ("Hi {name}!", "braces-shown"), ('Hi "Sam"!', "quotes-shown")], "join",
           "HL replaces {name} with what is inside name."),
         F('set age to 20\nsay "Next year: {___}"', ["age + 1"], "join", "Anything can go in the braces, even a calculation: {age + 1}.",
           wrong=[(r"^age$", "braces-calc")]),
         W("Write a line that shows: I am 9 (use the variable age)", ['say "I am {age}"'], "join", "Put {age} inside the text so HL fills it in.",
           ctx="set age to 9", goal="I am 9", wrong=[(r'^say "I am age"$', "braces-missing"), (r'^say "I am " \+ age$', "text-num-mix")])),
    part("Calculating", '''
Numbers work like a calculator:

```hum
say 2 + 3
say 10 - 4
say 6 * 7
say 20 / 8
say 17 mod 5
say 2 + 3 * 4
say (2 + 3) * 4
```

`mod` is the remainder after dividing: 17 mod 5 is 2. Multiplication happens **before** addition, like in maths class. Use brackets to change the order.
''',
         P('say 2 + 3 * 4', "14", [("20", "math-precedence"), ("9", "math-precedence"), ("24", "math-precedence")], "math",
           "3 * 4 happens first (12), then + 2 makes 14."),
         T('say 10 - 4\nsay 6 * 7\nsay 17 mod 5', "math", "10 - 4 = 6, 6 * 7 = 42, and 17 mod 5 is the remainder: 2."),
         F('say (2 + 3) ___ 4', ["*", "times"], "math", "Brackets first: 2 + 3 = 5. Then 5 * 4 = 20.", wrong=[(r"^(x|X)$", "math-word")])),
    part("Joining text", '''
Join two pieces of text with `+`. Some tools work on text too:

```hum
set first to "Human"
set second to "Lang"
say first + second
say length of "Human"
say uppercase of "hello"
```

**HL never guesses.** Text and numbers are different things, and HL won't quietly mix them:

```hum-error
say "5" + 1
```
''',
         P('say "Hu" + "man"', "Human", [("Hu man", "join-space"), ("Hu + man", "join-shown"), ("Hu\nman", "join-shown")], "textops",
           "+ joins the two pieces into one piece of text, with nothing between them."),
         P('say uppercase of "hi"', "HI", [("hi", "other"), ('"HI"', "quotes-shown"), ("2", "other")], "textops", "uppercase of makes all letters capital."),
         C('What happens with say "5" + 1 ?', "HL stops and says you tried to add a number to text",
           [("It shows 6", "text-num-mix"), ("It shows 51", "text-num-mix")], "types",
           "HL never guesses. Use number of \"5\" to turn text into a number, or build text with braces.", code='say "5" + 1')),
], [
    P('set n to 7\nsay "n is {n}"', "n is 7", [("n is n", "braces-missing"), ("n is {n}", "braces-shown")], "join", "{n} is replaced by 7."),
    P('set a to 3\nset b to 4\nsay "{a} and {b}: {a * b}"', "3 and 4: 12", [("a and b: a * b", "braces-missing"), ("3 and 4: 7", "math-word")], "join",
      "Each { } is replaced. {a * b} is 3 * 4 = 12."),
    C("What is 17 mod 5?", "2", [("3", "math-mod"), ("3.4", "math-mod"), ("12", "math-mod")], "math", "17 = 5 * 3 + 2, so the remainder is 2."),
    P('say (1 + 2) * 3', "9", [("7", "math-precedence"), ("5", "math-precedence")], "math", "Brackets first: 1 + 2 = 3. Then 3 * 3 = 9."),
    T('say 20 / 8\nsay 2 + 3', "math", "20 / 8 = 2.5. HL shows decimals when it needs to."),
    P('say length of "Human"', "5", [("4", "other"), ("6", "other"), ("Human", "other")], "textops", "Human has 5 letters."),
    W('Write a line that joins "Sun" and "shine" and shows the result', ['say "Sun" + "shine"'], "textops", "Use + between two pieces of text.", goal="Sunshine",
      wrong=[(r'^say "Sun shine"$', "join-space")]),
    P('set a to "Hi"\nset b to " there"\nsay a + b', "Hi there", [("Hithere", "join-space"), ("a + b", "join-shown")], "textops", "The space is part of the second text, so it is kept."),
    C('Which line is fine in HL?', 'say "Age: {5}"', [('say "Age: " + 5', "text-num-mix"), ('say "5" + 5', "text-num-mix")], "types",
      "Text and numbers do not mix with +. Put the number in braces and HL joins them for you."),
])

U4 = unit(4, "Ask questions", "Ask the person a question and use the answer.", [
    part("Asking", '''
`ask` waits for the person running the program to type something, and keeps it in a variable:

```hum
ask "What is your name?" and save it as name
say "Nice to meet you, {name}!"
```

```input
Sam
```

The screen shows your question, then what the person typed.
''',
         P('ask "Your pet?" and save it as pet\nsay "Cute: {pet}"', "Your pet? Rex\nCute: Rex",
           [("Cute: Rex", "ask-shown"), ("Your pet?\nCute: ", "ask-shown"), ("Your pet? Rex\nCute: pet", "braces-missing")], "ask",
           "The question is shown with the typed answer after it. Then the next line runs.", inputs=["Rex"], q="The person types: Rex"),
         F('___ "Your name?" and save it as name\nsay "Hi {name}"', ["ask"], "ask", "ask asks the question and waits for an answer.",
           wrong=[(r"^(input|prompt|question|get|read)$", "ask-word")], inputs=["Ana"], q="The person types: Ana"),
         W('Write a line that asks "Your city?" and saves the answer as city', ['ask "Your city?" and save it as city'], "ask",
           'ask "question" and save it as name.', wrong=[(r'^ask "Your city\?"$', "ask-save"), (r"^(input|prompt)", "ask-word")])),
    part("Asking for a number", '''
What the person types is **text**. When you want a number, use `ask number`. It keeps asking until the answer really is a number:

```hum
ask number "How old are you?" and save it as age
say "In 10 years you will be {age + 10}."
```

```input
twenty
20
```
''',
         P('ask number "Age?" and save it as age\nsay age + 1', "Age? 9\n10", [("Age? 9\n91", "text-num-mix"), ("Age? 9\n9", "update-not-run"), ("10", "ask-shown")],
           "ask", "ask number makes age a real number, so 9 + 1 = 10.", inputs=["9"], q="The person types: 9"),
         C("A program must add two numbers the person types. Which ask should it use?", "ask number",
           [("ask (text)", "ask-number"), ("say", "ask-word")], "ask", "ask number checks the answer is a number, so you can calculate with it."),
         T('ask number "Bill?" and save it as bill\nsay "Half: {bill / 2}"', "ask", "50 / 2 = 25. Remember the question and the typed answer come first.",
           inputs=["50"], q="The person types: 50")),
], [
    P('ask "Colour?" and save it as c\nsay "I like {c} too"', "Colour? blue\nI like blue too", [("I like blue too", "ask-shown"), ("Colour? blue\nI like c too", "braces-missing")],
      "ask", "Question and answer first, then the say line.", inputs=["blue"], q="The person types: blue"),
    P('ask number "Age?" and save it as age\nsay age', 'Age? abc\n"abc" isn\'t a number. Please type a number.\nAge? 4\n4',
      [("Age? abc\nabc", "ask-number"), ("Age? 4\n4", "ask-shown")], "ask", "ask number keeps asking until the answer is really a number.",
      inputs=["abc", "4"], q="The person types: abc, and then 4"),
    F('ask "Name?" and ___ it as n\nsay "Hello {n}"', ["save"], "ask", "and save it as n keeps the answer in n.", inputs=["Mo"], q="The person types: Mo"),
    W('Write a line that asks for a number: "How many?" and saves it as count', ['ask number "How many?" and save it as count'], "ask",
      'ask number "question" and save it as name.', wrong=[(r'^ask "How many\?" and save it as count$', "ask-number")]),
    T('ask "Name?" and save it as n\nask number "Age?" and save it as a\nsay "{n} is {a}"', "ask", "Two questions, each followed by its answer. Then the final say.",
      inputs=["Zoe", "11"], q="The person types: Zoe, and then 11"),
    B('ask "Name?" as n\nsay "Hi {n}"', 1, "ask", "ask needs and save it as to say where the answer is kept.", 'ask "Name?" and save it as n', inputs=["Al"]),
    P('ask number "A?" and save it as a\nask number "B?" and save it as b\nsay a * b', "A? 3\nB? 4\n12", [("A? 3\nB? 4\n34", "text-num-mix"), ("12", "ask-shown")], "ask",
      "Both answers are numbers, so a * b = 12.", inputs=["3", "4"], q="The person types: 3, and then 4"),
])

U5 = unit(5, "Make decisions", "Do one thing or another with if.", [
    part("if", '''
`if` runs its lines only when something is true. The lines that belong to it are **indented by 4 spaces**:

```hum
set age to 20
if age is at least 18
    say "You are an adult."
say "Done"
```

The last line is not indented, so it always runs.
''',
         P('set n to 7\nif n is greater than 5\n    say "Big"\nsay "Done"', "Big\nDone", [("Big", "loop-body"), ("Done", "if-skip"), ("Done\nBig", "order-mixed")], "if",
           "7 is greater than 5, so Big is shown. Done is not indented, so it always runs."),
         P('set n to 2\nif n is greater than 5\n    say "Big"\nsay "Done"', "Done", [("Big\nDone", "if-skip"), ("Big", "if-skip"), ("Done\nDone", "other")], "if",
           "2 is not greater than 5, so the indented line is skipped."),
         B('set age to 20\nif age is at least 18\nsay "Adult"', 3, "indent", "The lines that belong to an if are indented by 4 spaces.", '    say "Adult"')),
    part("otherwise", '''
Add `otherwise` for the other case, and `otherwise if` for more:

```hum
set age to 15
if age is at least 18
    say "Adult"
otherwise if age is at least 13
    say "Teenager"
otherwise
    say "Child"
```

HL goes down the choices and runs the **first** one that is true.
''',
         P('set t to 15\nif t is at least 20\n    say "Warm"\notherwise\n    say "Cold"', "Cold", [("Warm", "if-otherwise"), ("Warm\nCold", "if-otherwise"), ("Cold\nWarm", "if-otherwise")],
           "if", "15 is not at least 20, so the otherwise part runs."),
         O(['set age to 10', 'if age is at least 18', '    say "Adult"', 'otherwise', '    say "Child"'], "if",
           "Set the variable first. Then the if. Its lines are indented. otherwise comes after them.", q="Put the lines in order to show Child."),
         F('set score to 60\nif score is at least 90\n    say "A"\n___ if score is at least 50\n    say "B"\notherwise\n    say "C"', ["otherwise"], "if",
           "otherwise if gives another choice. 60 is at least 50, so B.", q="The program should show B.")),
    part("Comparing", '''
**Comparing things**

| You write | It means |
|---|---|
| `a is b` | equal |
| `a is not b` | not equal |
| `a is less than b` | smaller |
| `a is greater than b` | bigger |
| `a is at least b` | bigger or equal |
| `a is at most b` | smaller or equal |

Combine questions with `and`, `or` and `not`:

```hum
set age to 30
set has_ticket to yes
if age is at least 18 and has_ticket
    say "Welcome in!"
```
''',
         C("Which one means bigger OR equal?", "is at least", [("is greater than", "at-least"), ("is at most", "at-least"), ("is not", "compare-word")], "compare",
           "at least includes the number itself. greater than does not."),
         P('set age to 30\nset has_ticket to no\nif age is at least 18 and has_ticket\n    say "In"\notherwise\n    say "Out"', "Out", [("In", "and-or")], "compare",
           "and needs both. has_ticket is no, so the whole question is no."),
         P('set age to 10\nset vip to yes\nif age is at least 18 or vip\n    say "In"\notherwise\n    say "Out"', "In", [("Out", "and-or")], "compare",
           "or needs only one to be yes. vip is yes.")),
], [
    P('set a to 5\nif a is 5\n    say "five"', "five", [("a", "other"), ("5", "other")], "if", "a is 5 asks: is a equal to 5? Yes."),
    P('set a to 5\nif a is not 5\n    say "different"\notherwise\n    say "same"', "same", [("different", "compare-word")], "compare", "a is not 5 is no, so otherwise runs."),
    P('set n to 10\nif n is at most 10\n    say "ok"', "ok", [("n", "other"), ("10", "other")], "compare", "at most includes 10 itself."),
    P('set n to 10\nif n is less than 10\n    say "small"\notherwise\n    say "not small"', "not small", [("small", "at-least")], "compare",
      "10 is not less than 10, so otherwise runs."),
    B('set n to 3\nif n is greater than 2\nsay "bigger"', 3, "indent", "Indent the line that belongs to the if by 4 spaces.", '    say "bigger"'),
    F('set n to 4\nif n is at least 3 ___ n is at most 5\n    say "between"', ["and"], "compare", "and: both must be true. 4 is at least 3 and at most 5.",
      wrong=[(r"^or$", "and-or")]),
    W("Write the line that starts a decision: is age at least 18?", ["if age is at least 18"], "if", "if, then the question.", ctx='set age to 20\nsay "x"',
      wrong=[(r"^if age >= 18$", "compare-word"), (r"^if age is 18 or more$", "compare-word")]),
    O(['set temp to 30', 'if temp is greater than 25', '    say "Hot"', 'otherwise', '    say "Nice"'], "if", "The if line, its indented line, then otherwise and its line.",
      q="Put the lines in order to show Hot."),
])

U6 = unit(6, "Repeat things", "Do something again and again without copying it.", [
    part("repeat", '''
Computers are good at doing the same thing many times.

```hum
repeat 3 times
    say "Hip hip hooray!"
```

Only the **indented** lines are repeated.
''',
         P('repeat 3 times\n    say "Hey"', "Hey\nHey\nHey", [("Hey", "repeat-count"), ("Hey\nHey", "repeat-count"), ("Hey\nHey\nHey\nHey", "repeat-count")], "repeat",
           "3 times means exactly 3 rounds."),
         T('repeat 2 times\n    say "A"\n    say "B"', "repeat", "Each round runs both indented lines: A, B, then A, B again."),
         F('repeat ___ times\n    say "Go"', ["4"], "repeat", "Four Go lines need repeat 4 times.", q="The program should show Go four times.")),
    part("repeat while", '''
`repeat while` keeps going as long as a question stays yes:

```hum
set count to 1
repeat while count is at most 5
    say "Count: {count}"
    add 1 to count
```

Something inside the loop must change, or the question never becomes no and it repeats forever.
''',
         P('set n to 1\nrepeat while n is at most 3\n    say n\n    add 1 to n', "1\n2\n3", [("1\n2", "while-edge"), ("2\n3\n4", "while-update"), ("1\n1\n1", "while-update")], "repeat",
           "n is 1, 2, 3 (at most 3 includes 3). At 4 the question is no and the loop stops."),
         O(['set n to 3', 'repeat while n is greater than 0', '    say n', '    subtract 1 from n'], "repeat",
           "Make n first. The loop line comes next, then its indented lines. Say n before taking 1 away.", q="Make a countdown that shows 3, 2, 1."),
         C("What happens if nothing inside repeat while changes what the question looks at?", "It repeats forever",
           [("It runs once", "while-update"), ("It stops after 10 times", "while-update")], "repeat", "The question stays yes forever, so the loop never ends.",
           code='set n to 1\nrepeat while n is at most 3\n    say n')),
    part("stop and skip", '''
`stop` leaves the loop early, and `skip` jumps straight to the next round:

```hum
set n to 0
repeat 10 times
    add 1 to n
    if n is 3
        skip
    if n is 6
        stop
    say n
```
''',
         P('set n to 0\nrepeat 5 times\n    add 1 to n\n    if n is 2\n        skip\n    say n', "1\n3\n4\n5", [("1\n2\n3\n4\n5", "stop-skip"), ("1", "stop-skip"), ("1\n3", "stop-skip")], "repeat",
           "At n = 2 the skip jumps to the next round, so 2 is not shown."),
         P('set n to 0\nrepeat 5 times\n    add 1 to n\n    if n is 3\n        stop\n    say n', "1\n2", [("1\n2\n4\n5", "stop-skip"), ("1\n2\n3", "stop-skip")], "repeat",
           "At n = 3 the stop ends the whole loop."),
         C("What is the difference between stop and skip?", "stop leaves the loop. skip goes to the next round.",
           [("They are the same", "stop-skip"), ("skip leaves the loop. stop goes to the next round.", "stop-skip")], "repeat",
           "stop = finish the loop now. skip = ignore the rest of this round.")),
], [
    P('repeat 2 times\n    say "Hi"\nsay "Bye"', "Hi\nHi\nBye", [("Hi\nBye\nHi\nBye", "loop-body"), ("Hi\nBye", "loop-body"), ("Hi\nHi\nBye\nBye", "loop-body")], "repeat",
      "Only the indented line repeats. Bye is not indented, so it runs once at the end."),
    T('set total to 0\nrepeat 4 times\n    add 5 to total\nsay total', "repeat", "5 added 4 times is 20."),
    F('set n to 0\nrepeat 3 times\n    ___ 1 to n\nsay n', ["add"], "repeat", "add 1 to n makes n 1, 2, 3.", wrong=[(r"^(plus|increase)$", "update-word")]),
    P('set n to 5\nrepeat while n is greater than 3\n    say n\n    subtract 1 from n', "5\n4", [("5\n4\n3", "while-edge"), ("4\n3", "while-update")], "repeat",
      "n = 5, then 4. At 3, 3 is not greater than 3, so the loop stops."),
    W("Write the line that repeats the lines under it 7 times", ["repeat 7 times"], "repeat", "repeat, the number, times.",
      wrong=[(r"^repeat 7$", "repeat-count"), (r"^(for|loop)\b", "repeat-count")]),
    B('repeat 3 times\nsay "Hey"', 2, "indent", "The lines that repeat must be indented by 4 spaces.", '    say "Hey"'),
    P('repeat 4 times\n    say "x"\n    stop', "x", [("x\nx\nx\nx", "stop-skip"), ("xx", "stop-skip")], "repeat", "stop leaves the loop in the very first round."),
    O(['set n to 1', 'repeat while n is at most 3', '    say "Round {n}"', '    add 1 to n'], "repeat", "n first, then the loop, then its two lines.",
      q="Make HL show Round 1, Round 2, Round 3."),
])


U7 = unit(7, "Lists", "Keep many values together and walk through them.", [
    part("Your first list", '''
A **list** holds many values in order. **Counting starts at 1**, like people count:

```hum
set colors to list of "red", "green", "blue"
say colors
say item 1 of colors
say how many items in colors
```
''',
         P('set c to list of "red", "green", "blue"\nsay item 2 of c', "green", [("red", "list-from-one"), ("blue", "list-from-one"), ("list of red, green, blue", "list-count")], "lists",
           "Counting starts at 1, so item 2 is the second one: green."),
         P('set c to list of "a", "b", "c", "d"\nsay how many items in c', "4", [("3", "list-count"), ("c", "list-from-one"), ("list of a, b, c, d", "list-count")], "lists",
           "how many items in c counts the items: 4."),
         W('Write a line that makes a list called pets with "cat" and "dog"', ['set pets to list of "cat", "dog"'], "lists", 'set pets to list of "cat", "dog".',
           wrong=[(r"^set pets to \[", "list-word"), (r'^set pets to "cat", "dog"$', "list-word")])),
    part("Change a list", '''
```hum
set colors to list of "red", "green", "blue"
add "pink" to colors
remove "green" from colors
change item 1 of colors to "crimson"
say colors
```
''',
         P('set n to list of 1, 2\nadd 3 to n\nsay n', "list of 1, 2, 3", [("list of 3, 1, 2", "list-end"), ("list of 1, 2", "update-not-run"), ("3", "list-end")], "lists",
           "add puts the new item at the end of the list."),
         P('set n to list of 5, 6, 7\nremove 6 from n\nsay n', "list of 5, 7", [("list of 5, 6, 7", "update-not-run"), ("list of 6", "other"), ("list of 5, 6", "other")], "lists",
           "remove 6 takes the item 6 out of the list."),
         T('set c to list of "a", "b"\nchange item 1 of c to "z"\nsay c', "lists", "Item 1 (a) is replaced by z.")),
    part("for each", '''
Go through every item with `for each`:

```hum
set colors to list of "red", "green", "blue"
for each color in colors
    say "I like {color}"
```

`color` is the current item. It changes in every round.
''',
         P('for each x in list of 1, 2, 3\n    say x * 10', "10\n20\n30", [("1\n2\n3", "foreach-item"), ("60", "foreach-item"), ("10", "foreach-item")], "foreach",
           "The indented line runs once for each item: 1 * 10, 2 * 10, 3 * 10."),
         O(['set fruits to list of "apple", "pear"', 'for each fruit in fruits', '    say "I like {fruit}"'], "foreach",
           "Make the list first, go through it with for each, and the indented line is what happens for every item.", q="Put the lines in order."),
         F('set names to list of "Ann", "Bo"\n___ each name in names\n    say "Hi {name}"', ["for"], "foreach", "for each name in names goes through the list.",
           wrong=[(r"^(foreach|loop|each|every)$", "foreach-word")])),
], [
    P('set c to list of "x", "y"\nsay item 1 of c', "x", [("y", "list-from-one"), ("list of x, y", "list-count"), ("1", "list-from-one")], "lists", "Item 1 is the first item."),
    P('set total to 0\nfor each v in list of 4, 5, 6\n    add v to total\nsay total', "15", [("6", "loop-body"), ("4\n5\n6", "foreach-item"), ("0", "update-not-run")], "foreach",
      "total grows: 4, then 9, then 15. say total runs once, after the loop."),
    T('set l to empty list\nadd "first" to l\nadd "second" to l\nsay l', "lists", "Two items were added to an empty list, in order."),
    B('set c to list of "red", "green"\nsay item 0 of c', 2, "lists", "Counting starts at 1, so there is no item 0.", 'say item 1 of c'),
    F('set c to list of 1, 2, 3\nsay ___ items in c', ["how many"], "lists", "how many items in c is the number of items.", wrong=[(r"^(count|length)$", "list-count")]),
    W('Write a line that adds "pink" to the list colors', ['add "pink" to colors'], "lists", 'add "pink" to colors.', ctx='set colors to list of "red"',
      wrong=[(r"^colors\.(add|append|push)", "list-word"), (r'^add colors', "list-word")]),
    C("Which number does counting start at in HL lists?", "1", [("0", "list-from-one"), ("2", "list-from-one")], "lists", "Counting starts at 1, like people count."),
    P('set a to list of 1, 2\nset b to a\nadd 3 to b\nsay a', "list of 1, 2", [("list of 1, 2, 3", "list-copy")], "lists", "b is a copy of a. Adding to b does not change a."),
])

U8 = unit(8, "Functions", "Give a set of steps a name and use it anywhere.", [
    part("Your own steps", '''
A **function** is a mini-program with a name. You write it once and use it as often as you like. `define` creates it, and `with` lists the values it needs:

```hum
define greet with name
    say "Hello, {name}!"

greet with "Sam"
greet with "Alex"
```
''',
         P('define greet with name\n    say "Hello, {name}!"\n\ngreet with "Sam"\ngreet with "Alex"', "Hello, Sam!\nHello, Alex!",
           [("Hello, Sam!", "func-call"), ("Hello, {name}!\nHello, {name}!", "braces-shown"), ("Hello, name!\nHello, name!", "braces-missing")], "func",
           "Each call runs the function once, with its own value."),
         F('___ shout with word\n    say uppercase of word\n\nshout with "hey"', ["define"], "func", "define makes a function.",
           wrong=[(r"^(def|function|func|fn|to|make)$", "func-define")], q="The program should show HEY."),
         P('define wave\n    say "Wave!"\n\nwave\nwave', "Wave!\nWave!", [("Wave!", "func-call"), ("wave\nwave", "func-call"), ("", "func-define")], "func",
           "define only teaches HL the steps. Each time you write wave, the steps run.")),
    part("Giving back", '''
`give back` sends an answer out of the function:

```hum
define double with n
    give back n * 2

say double with 21
set answer to double with 5
say "Ten is {answer}"
```

Use `and` between several values:

```hum
define add_numbers with a and b
    give back a + b

say add_numbers with 2 and 3
```
''',
         P('define double with n\n    give back n * 2\n\nsay double with 21', "42", [("n * 2", "func-giveback"), ("21", "func-giveback"), ("2", "func-giveback")], "func",
           "give back sends n * 2 = 42 out, and say shows it."),
         F('define square with n\n    ___ n * n\n\nsay square with 5', ["give back"], "func", "give back sends the answer out.",
           wrong=[(r"^(return|send|output|say)$", "func-giveback")]),
         T('define add_numbers with a and b\n    give back a + b\n\nsay add_numbers with 2 and 3\nsay add_numbers with 10 and 20', "func",
           "The first call gives back 5. The second gives back 30.")),
    part("Inside and outside", '''
Variables made inside a function stay inside it:

```hum-error
define make_secret
    set secret to 42

make_secret
say secret
```

To change a variable that lives **outside**, use `change` (`set` would make a new private one):

```hum
set total to 0
define add_to_total with n
    change total to total + n

add_to_total with 5
add_to_total with 10
say total
```
''',
         C("Where can you use a variable that was made inside a function?", "Only inside that function",
           [("Everywhere in the program", "scope-private"), ("Only after the program ends", "scope-private")], "scope",
           "The variable is private to the function. Outside it HL has never heard of it.", code="define make_secret\n    set secret to 42\n\nmake_secret"),
         B('set total to 0\ndefine add_to_total with n\n    set total to total + n\n\nadd_to_total with 5\nsay total', 3, "scope",
           "set makes a new private total inside the function. change updates the outside one.", "    change total to total + n", goal="5"),
         P('set total to 0\ndefine add_to_total with n\n    change total to total + n\n\nadd_to_total with 5\nadd_to_total with 10\nsay total', "15",
           [("0", "scope-change"), ("10", "scope-change"), ("5", "scope-change")], "scope", "change updates the outside total each time: 0 + 5 + 10 = 15.")),
], [
    P('define greet with name\n    say "Hi {name}"\n\ngreet with "Al"', "Hi Al", [("Hi name", "braces-missing"), ('greet with "Al"', "func-call")], "func", "The function says Hi and the value it was given."),
    P('define triple with n\n    give back n * 3\n\nset r to triple with 4\nsay "Result: {r}"', "Result: 12", [("Result: 4", "func-giveback"), ("Result: r", "braces-missing"),
                                                                                                    ("Result: triple", "func-giveback")], "func",
      "r keeps the answer that triple gave back: 12."),
    O(['define double with n', '    give back n * 2', 'say double with 4'], "func", "Define the function first. A call can only use a function that already exists.",
      q="Put the lines in order to show 8."),
    B('define double with n\n    give back n * 2\n\nsay double 5', 4, "func", "A call needs with before the values: double with 5.", "say double with 5"),
    C("What does give back do?", "Sends an answer out of the function", [("Shows the answer on the screen", "func-giveback"), ("Ends the program", "func-giveback")], "func",
      "give back hands the answer to the line that called the function."),
    F('define half with n\n    give back n / 2\n\nsay half ___ 10', ["with"], "func", "half with 10 calls the function.", wrong=[(r"^(of|from|on)$", "func-call")]),
    T('define add_one with n\n    give back n + 1\n\nsay add_one with (add_one with 1)', "func", "The inner call gives back 2. The outer call gives back 3."),
    W("Write the first line of a function called greet that needs one value called name", ["define greet with name"], "func", "define, the name, with, the value names.",
      wrong=[(r"^def greet", "func-define"), (r"^define greet\(", "func-define"), (r"^function greet", "func-define")]),
])

U9 = unit(9, "Put it together", "A small whole program, made from everything so far.", [
    part("A tip calculator", '''
Now you can read a whole program. Here is a tip calculator:

```hum
ask number "How much was the bill?" and save it as bill
ask number "What percent tip?" and save it as percent
set tip to bill * percent / 100
say "Tip: {tip}"
say "Total: {bill + tip}"
```

```input
80
15
```
''',
         T('ask number "Bill?" and save it as bill\nask number "Percent?" and save it as percent\nset tip to bill * percent / 100\nsay "Tip: {tip}"\nsay "Total: {bill + tip}"',
           "project", "80 * 15 / 100 = 12, and 80 + 12 = 92.", inputs=["80", "15"], q="The person types: 80, and then 15"),
         O(['ask number "Bill?" and save it as bill', 'ask number "Percent?" and save it as percent', 'set tip to bill * percent / 100', 'say "Tip: {tip}"'], "project",
           "Ask for both numbers first, then work out the tip, then show it.", inputs=["80", "15"], q="Put the lines in order. The person types 80 and then 15."),
         B('ask number "Bill?" and save it as bill\nask number "Percent?" and save it as percent\nset tip to bill * percent\nsay "Tip: {tip}"', 3, "project",
           "A percent needs / 100. 80 * 15 is 1200, but the tip is 12.", "set tip to bill * percent / 100", inputs=["80", "15"],
           goal="Bill? 80\nPercent? 15\nTip: 12", q="The tip should be 12.")),
    part("A grade checker", '''
Functions and lists together:

```hum
define grade_for with score
    if score is at least 90
        give back "A"
    otherwise if score is at least 75
        give back "B"
    otherwise
        give back "C"

for each score in list of 95, 80, 60
    say "{score} gets {grade_for with score}"
```
''',
         P('define grade_for with score\n    if score is at least 90\n        give back "A"\n    otherwise\n        give back "B"\n\nfor each s in list of 95, 60\n    say "{s} gets {grade_for with s}"', "95 gets A\n60 gets B",
           [("95 gets B\n60 gets B", "at-least"), ("95 gets A", "foreach-item"), ("A\nB", "braces-missing")], "project",
           "The loop calls the function for each score. 95 is at least 90, 60 is not."),
         F('define grade_for with score\n    if score is at least 90\n        give back "A"\n    otherwise if score is at least ___\n        give back "B"\n    otherwise\n        give back "C"\n\nsay grade_for with 80',
           ["75"], "project", "80 must reach the B line. Since it is not at least 90, HL checks at least 75 next.", q="grade_for with 80 should give back B."),
         B('define grade_for with score\n    if score is greater than 90\n        give back "A"\n    otherwise\n        give back "B"\n\nsay grade_for with 90', 2, "compare",
           "A score of exactly 90 should get A, so it must be at least 90, not greater than 90.", "    if score is at least 90", goal="A", q="90 should get an A.")),
    part("A guessing game", '''
A number-guessing game uses everything: a variable, a loop, `ask`, `if` and `otherwise if`. Here the secret is 7:

```hum
set secret to 7
set guess to 0

repeat while guess is not secret
    ask number "Guess a number from 1 to 10:" and save it as guess
    if guess is less than secret
        say "Too low"
    otherwise if guess is greater than secret
        say "Too high"

say "You got it!"
```

```input
3
9
7
```
''',
         T('set secret to 7\nset guess to 0\n\nrepeat while guess is not secret\n    ask number "Guess:" and save it as guess\n    if guess is less than secret\n        say "Too low"\n    otherwise if guess is greater than secret\n        say "Too high"\n\nsay "You got it!"',
           "project", "3 is too low, 9 is too high, 7 is right so the loop stops.", inputs=["3", "9", "7"], q="The person types: 3, then 9, then 7"),
         C("What makes the guessing loop stop?", "guess becomes equal to secret", [("The program asks only 3 times", "repeat-count"), ("The person types stop", "stop-skip")], "project",
           "repeat while guess is not secret goes on until the guess is right.",
           code='repeat while guess is not secret\n    ask number "Guess:" and save it as guess'),
         W("Write the line that shows You got it!", ['say "You got it!"'], "say", "say, then the text in quotes.", goal="You got it!")),
], [
    T('set total to 0\nfor each p in list of 3, 4, 5\n    add p to total\nsay "Total: {total}"', "project", "3 + 4 + 5 = 12.", ),
    P('set nums to list of 2, 4, 6\nset total to 0\nfor each n in nums\n    add n to total\nsay total / how many items in nums', "4",
      [("12", "project-plan"), ("6", "project-plan"), ("3", "project-plan")], "project", "The total is 12, there are 3 numbers, and 12 / 3 = 4."),
    O(['set names to list of "Ann", "Bo", "Cy"', 'for each name in names', '    say "Hello {name}"', 'say "Done"'], "project",
      "The list first, then the loop, then its indented line. Done is not indented, so it runs once at the end.", q="Put the lines in order."),
    B('set names to list of "Ann", "Bo"\nfor each name in names\nsay "Hi {name}"', 3, "indent", "The line that belongs to for each must be indented.", '    say "Hi {name}"'),
    W("Write a line that makes the variable total start at 0", ["set total to 0"], "vars", "set total to 0.", wrong=[(r"^total\s*=", "set-word")]),
    F('set lives to 3\nrepeat while lives is ___ 0\n    say "alive"\n    subtract 1 from lives', ["greater than"], "repeat", "3, 2, 1 are all greater than 0, so alive is shown 3 times.",
      wrong=[(r"^(more than|bigger than|over)$", "compare-word")], q="The program should show alive 3 times."),
    P('define double with n\n    give back n * 2\n\nset total to 0\nfor each v in list of 1, 2, 3\n    add (double with v) to total\nsay total', "12",
      [("6", "project-plan"), ("3", "project-plan"), ("0", "project-plan")], "project", "double gives 2, 4, 6. Their total is 12."),
    P('ask number "Age?" and save it as age\nif age is at least 18\n    say "Adult"\notherwise\n    say "Child"', "Age? 20\nAdult",
      [("Age? 20\nChild", "at-least"), ("Adult", "ask-shown")], "project", "20 is at least 18, so Adult.", inputs=["20"], q="The person types: 20"),
])

U10 = unit(10, "Finding mistakes", "Read the messages, find the bug, and step through a program.", [
    part("Read the message", '''
Everybody makes mistakes. When something is wrong, HL tells you **the line**, **what it thinks happened**, and often **a hint**:

```hum-error
set score to 1
change scroe to 2
```

Read the first line of the message first. It tells you where to look.
''',
         P('set score to 1\nchange scroe to 2', "Line 2: I don't know \"scroe\".", [("Line 1: I don't know \"scroe\".", "debug-line"), ("Line 2: score is too small.", "other"), ("It works and score is 2", "debug-typo")],
           "debug", "scroe is a typing mistake for score. HL points at line 2 and says it does not know the name.", error=True, q="What does HL say?"),
         P('set list to 5', "Line 1: \"list\" is a word HL already uses, so it can't be a name.", [("Line 1: 5 is not allowed.", "other"), ("It works.", "name-reserved")],
           "debug", "list is one of the words HL uses itself, so it cannot be a variable name.", error=True, q="What does HL say?"),
         P('set colors to list of "red", "green"\nsay item 5 of colors', "Line 2: You asked for item 5, but there are only 2 items.",
           [("Line 1: You asked for item 5, but there are only 2 items.", "debug-line"), ("It shows nothing.", "list-from-one")], "debug",
           "The list has only 2 items. HL points at the line that asked for item 5.", error=True, q="What does HL say?")),
    part("Find the bug", '''
A **bug** is a mistake in a program. To find one:

1. Read the message. It names the line.
2. Look at that line (and the one above it).
3. Check spelling, quotes and indentation.
4. If there is no message but the answer is wrong, follow the program by hand with some small numbers.
''',
         B('set price to 10\nsay "Price: {pirce}"', 2, "debug", "pirce is a typing mistake. The name is price.", 'say "Price: {price}"'),
         B('set n to 0\nrepeat 4 times\n    add 1 to n\nsay n', 2, "debug", "This program works, but it counts 4 times. To get 5 it must repeat 5 times.", "repeat 5 times", goal="5",
           q="The program should show 5."),
         B('say "Total: " + 5', 1, "types", "Text and numbers do not mix. Put the number in braces, or write it inside the text.", 'say "Total: {5}"')),
    part("Step through", '''
In the Playground press **Step through**. **Back** and **Next** walk the program one line at a time. The line that is running is marked, and the variables that just changed are highlighted.

You can also do it in the terminal: `hl debug myprogram.hum`.

Stepping is the best way to understand what a program really does. After each line, look at the variables.
''',
         K('set a to 2\nset b to a * 3\nadd 1 to b', "b", "7", [("6", "debug-step"), ("3", "debug-step"), ("2", "debug-step")], "debug",
           "a is 2. b is 2 * 3 = 6. Then add 1 to b makes 7."),
         K('set x to 10\nsubtract 4 from x\nchange x to x * 2', "x", "12", [("6", "debug-step"), ("20", "debug-step"), ("10", "debug-step")], "debug",
           "x is 10, then 6, then 6 * 2 = 12."),
         C("What does the Step through button do?", "Runs the program one line at a time and shows what changed",
           [("Makes the program faster", "debug-step"), ("Deletes the mistakes for you", "debug-step")], "debug",
           "You watch the program line by line, so you see exactly where it goes wrong.")),
], [
    P('say "Hi" +', "Line 1:", [("It shows Hi", "debug-line")], "debug", "x", error=True) if False else
    P('set n to 5\nchange m to 6', "Line 2: I don't know \"m\".", [("Line 1: I don't know \"m\".", "debug-line"), ("It works.", "debug-typo")], "debug",
      "m was never made with set, so change cannot find it.", error=True, q="What does HL say?"),
    B('set total to 1\nchange totl to 2\nsay total', 2, "debug", "totl is a typing mistake for total.", "change total to 2"),
    B('say "Hello"\nsay Bye', 2, "quotes", "Bye needs quotes: it is text.", 'say "Bye"'),
    B('set age to 20\nif age is at least 18\nsay "Adult"', 3, "indent", "Indent the line that belongs to the if.", '    say "Adult"'),
    K('set n to 1\nadd 2 to n\nadd 2 to n', "n", "5", [("3", "debug-step"), ("4", "debug-step"), ("1", "debug-step")], "debug", "1 + 2 + 2 = 5."),
    K('set a to 3\nset b to a\nchange a to 10', "b", "3", [("10", "debug-step"), ("13", "debug-step"), ("0", "debug-step")], "debug",
      "b took a copy of 3. Changing a later does not change b."),
    C("An answer is wrong but there is no error message. What is a good first step?", "Step through the program and watch the variables",
      [("Delete the whole program", "debug-step"), ("Run it again and hope", "debug-step")], "debug", "Watching each line shows exactly where the numbers go wrong."),
    C("What does the first line of an error message tell you?", "Which line to look at", [("Who wrote the program", "debug-line"), ("How long it took", "debug-line")], "debug",
      "It starts with Line N so you know where to look."),
])

UNITS = [U1, U2, U3, U4, U5, U6, U7, U8, U9, U10]


# =====================================================================================================
# What the web page gets (the page itself has no HumanLang inside: every answer below was worked out here, by running it)
# =====================================================================================================
_BLOCK = re.compile(r"```(hum|hum-error)\n(.*?)```(\s*```input\n(.*?)```)?", re.S)


def _expand(md):
    """Teach text: after every example, add what HL really prints (or says)."""
    def sub(m):
        kind, body, given = m.group(1), m.group(2), m.group(4)
        out, err = run(body, inputs=given.split("\n")[:-1] if given else ["Sam", "20", "20", "20"])
        text = (err if kind == "hum-error" else out).rstrip("\n")
        res = f"```{kind}\n{body}```\n"
        if given:
            res += f"\n```input\n{given}```\n"
        if text:
            res += f"\n```output\n{text}\n```\n"
        return res
    return _BLOCK.sub(sub, md)


def _ex(e, eid, highlight):
    d = dict(e)
    d["id"] = eid
    if e.get("code"):
        d["html"] = highlight(e["code"])
    if e["kind"] == "type":
        d["answer"] = run(e["code"], e["inputs"])[0].rstrip("\n")
    if e["kind"] == "write" and e.get("ctx"):
        d["ctx_html"] = highlight(e["ctx"])
    if e["kind"] == "bug":
        d["lines"] = e["code"].split("\n")
    if e["kind"] == "order":
        d["goal_out"] = run("\n".join(e["lines"]), e["inputs"])[0].rstrip("\n")
    d["wrong"] = [[w[0], w[1]] for w in e.get("wrong", [])]
    return d


def export(render_markdown, highlight):
    units = []
    for u in UNITS:
        n = u["n"]
        parts = []
        for pi, p in enumerate(u["parts"], 1):
            html_, _ = render_markdown(_expand(p["teach"]))
            parts.append({"title": p["title"], "teach": html_,
                          "ex": [_ex(e, f"u{n}p{pi}e{i}", highlight) for i, e in enumerate(p["ex"], 1)]})
        units.append({"n": n, "title": u["title"], "blurb": u["blurb"], "parts": parts,
                      "bank": [_ex(e, f"u{n}b{i}", highlight) for i, e in enumerate(u["bank"], 1)]})
    return {"units": units, "skills": SKILLS, "tags": {k: v[1] for k, v in TAGS.items()}, "tagSkill": {k: v[0] for k, v in TAGS.items()}}


def export_json(render_markdown, highlight):
    return json.dumps(export(render_markdown, highlight), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
