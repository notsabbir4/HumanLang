# HumanLang Tutorial

HumanLang (HL) is a programming language that reads like plain English. You don't need to know
anything about programming to start. This tutorial takes about an hour, and every example in it
really runs.

**Two ways to follow along**

- **In your browser:** open the Playground on this website and paste the examples in.
- **On your computer:** install HL, save an example in a file ending in `.hum`, and run it with
  `hl run myfile.hum`. Typing `hl` on its own opens an interactive prompt where you can try one line
  at a time.

Each grey box below is a program. The box under it, labelled output, is what it prints.

## 1. Say hello

```hum
say "Hello, world!"
```

```output
Hello, world!
```

`say` shows something on the screen. The words in quotes are called **text**.

A program is a list of instructions. HL runs them from top to bottom, one line at a time.

```hum
say "Hello!"
say "My name is HumanLang."
say "Nice to meet you."
```

```output
Hello!
My name is HumanLang.
Nice to meet you.
```

You can leave notes for yourself. A line that starts with `note:` is ignored by the computer:

```hum
note: this line does nothing, it is only for people
say "Notes are free"
```

```output
Notes are free
```

## 2. Remember things

A **variable** is a name for a value, like a label on a box. `set` makes one:

```hum
set name to "Sam"
set age to 20
say name
say age
```

```output
Sam
20
```

Use `add`, `subtract` and `change` to update a variable that already exists:

```hum
set score to 10
add 5 to score
subtract 2 from score
say score
change score to score * 2
say score
```

```output
13
26
```

**Why both `set` and `change`?** They catch typing mistakes. If you misspell a name when you
`change` it, HL tells you instead of quietly making a new variable:

```hum-error
set score to 1
change scroe to 2
```

```output
Line 2: I don't know "scroe".
    change scroe to 2
Did you mean "score"? To make a new variable, use: set scroe to ...
```

**Rules for names**

- Use letters, digits and `_`, with no spaces: `total_price`, `age2`. A name can't start with a digit.
- Names are case-sensitive, so `Name` and `name` are different.
- Letters from any language work.
- A few words are taken by HL itself (like `list`, `to`, `item`), and you'll get a friendly message if you try them:

```hum-error
set list to 5
```

```output
Line 1: "list" is a word HL already uses, so it can't be a name.
    set list to 5
Pick another name, for example "my_list".
```

## 3. Text and numbers

Put a value inside text by wrapping it in `{ }`. HL fills it in:

```hum
set name to "Sam"
set age to 20
say "Hi {name}, next year you will be {age + 1}."
```

```output
Hi Sam, next year you will be 21.
```

Anything can go inside the braces, including a calculation. To show a quote or a brace itself, put a
backslash in front of it:

```hum
say "She said \"hello\""
say "Use \{braces\} like this"
```

```output
She said "hello"
Use {braces} like this
```

Numbers work like a calculator. You can write symbols or words, whichever you find easier to read:

```hum
say 2 + 3
say 10 - 4
say 6 * 7
say 20 / 8
say 17 mod 5
say 2 plus 3 times 4
say (2 plus 3) times 4
say 2 to the power of 10
```

```output
5
6
42
2.5
2
14
20
1024
```

`mod` is the remainder after dividing: 17 mod 5 is 2. Multiplication happens before addition, just
like in maths class. Use brackets to change the order.

You can join two pieces of text with `+`:

```hum
set first to "Human"
set second to "Lang"
say first + second
say length of "Human"
say uppercase of "hello"
say lowercase of "HELLO"
```

```output
HumanLang
5
HELLO
hello
```

**HL never guesses.** Text and numbers are different kinds of things, and HL won't quietly mix them.
That prevents a whole family of confusing bugs:

```hum-error
say "5" + 1
```

```output
Line 1: You tried to add a number to text.
    say "5" + 1
Use number of "5" to turn text into a number, or build text with braces, like "Total: {x}".
```

If you really do want to treat text as a number, say so:

```hum
say number of "5" + 1
say text of 42 + "!"
```

```output
6
42!
```

## 4. Ask questions

`ask` waits for the person running the program to type something, and saves it:

```hum
ask "What is your name?" and save it as name
say "Nice to meet you, {name}!"
```

```input
Sam
```

```output
What is your name? Sam
Nice to meet you, Sam!
```

What the person types is **text**. When you want a number, use `ask number`. It also keeps asking
until the answer really is a number:

```hum
ask number "How old are you?" and save it as age
say "In 10 years you will be {age + 10}."
```

```input
twenty
20
```

```output
How old are you? twenty
"twenty" isn't a number. Please type a number.
How old are you? 20
In 10 years you will be 30.
```

## 5. Make decisions

`if` runs its lines only when something is true. The lines that belong to it are **indented by 4 spaces**:

```hum
set age to 20
if age is at least 18
    say "You are an adult."
```

```output
You are an adult.
```

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

```output
Teenager
```

**Comparing things**

| You write | It means |
|---|---|
| `a is b` | equal |
| `a is not b` | not equal |
| `a is less than b` | smaller |
| `a is greater than b` | bigger |
| `a is at least b` | bigger or equal |
| `a is at most b` | smaller or equal |
| `text contains "x"` | the text has this inside it |
| `list contains x` | the list has this item |

Combine questions with `and`, `or` and `not`:

```hum
set age to 30
set has_ticket to yes
if age is at least 18 and has_ticket
    say "Welcome in!"
if not has_ticket or age is less than 18
    say "Sorry, no entry."
say "hello" contains "ell"
```

```output
Welcome in!
yes
```

The answer to a question is `yes` or `no`. An `if` needs one of those, and tells you when it gets something else:

```hum-error
set age to 5
if age
    say "hi"
```

```output
Line 2: I expected yes or no here, but got a number.
    if age
Use a comparison such as "is", "is greater than" or "is at least". To ask whether a number is anything but zero, write: if x is not 0
```

## 6. Repeat things

Computers are good at doing the same thing many times.

```hum
repeat 3 times
    say "Hip hip hooray!"
```

```output
Hip hip hooray!
Hip hip hooray!
Hip hip hooray!
```

`repeat while` keeps going as long as a question stays `yes`:

```hum
set count to 1
repeat while count is at most 5
    say "Count: {count}"
    add 1 to count
```

```output
Count: 1
Count: 2
Count: 3
Count: 4
Count: 5
```

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

```output
1
2
4
5
```

## 7. Lists

A **list** holds many values in order. Counting starts at 1, like people count:

```hum
set colors to list of "red", "green", "blue"
say colors
say item 1 of colors
say how many items in colors
add "pink" to colors
remove "green" from colors
change item 1 of colors to "crimson"
say colors
```

```output
list of red, green, blue
red
3
list of crimson, blue, pink
```

Go through every item with `for each`:

```hum
set colors to list of "red", "green", "blue"
for each color in colors
    say "I like {color}"
```

```output
I like red
I like green
I like blue
```

It works on text too, letter by letter:

```hum
for each letter in "HL"
    say letter
```

```output
H
L
```

More things lists can do:

```hum
set numbers to list of 5, 3, 9, 1
say sorted of numbers
say reversed of numbers
say numbers contains 9
set nothing_yet to empty list
add "first" to nothing_yet
say nothing_yet
```

```output
list of 1, 3, 5, 9
list of 1, 9, 3, 5
yes
list of first
```

Asking for an item that isn't there gives a clear message:

```hum-error
set colors to list of "red", "green"
say item 5 of colors
```

```output
Line 2: You asked for item 5, but there are only 2 items.
    say item 5 of colors
Item numbers start at 1.
```

A list is **copied** when you put it in another variable, so changing the copy never changes the original:

```hum
set a to list of 1, 2
set b to a
add 3 to b
say a
say b
```

```output
list of 1, 2
list of 1, 2, 3
```

**Lists inside lists.** A list can hold lists, and you can change something deep inside in one line:

```hum
set scores to list of (list of 90, 80), (list of 70)
add 85 to item 2 of scores
change item 1 of item 1 of scores to 95
say scores
say item 2 of item 1 of scores
```

```output
list of (list of 95, 80), (list of 70, 85)
80
```

**Records.** When one thing has several named parts, don't use several lists that must stay in step.
Use a **record**. Each part is a **field**:

```hum
set person to record with name "Ann" and age 30
say field name of person
change field age of person to 31
set field email of person to "ann@example.com"
say person
```

```output
Ann
record with name Ann and age 31 and email ann@example.com
```

`change field` only works on a field that exists, so a typo gets caught. `set field` makes a new one:

```hum-error
set person to record with name "Ann" and age 30
change field agee of person to 31
```

```output
Line 2: "person" has no field called "agee".
    change field agee of person to 31
Did you mean "age"?  To add a new field, write: set field agee of person to ...
```

Records and lists go together well. Here is a class of students, sorted by score:

```hum
set students to list of (record with name "Zoe" and score 71), (record with name "Ana" and score 92)
add (record with name "Ben" and score 85) to students
for each student in reversed of (sorted of students by field score)
    say "{field name of student}: {field score of student}"
```

```output
Ana: 92
Ben: 85
Zoe: 71
```

## 8. Functions

A **function** is a mini-program with a name. You write it once and use it as often as you like.
`define` creates it, `with` lists the values it needs, and `give back` sends an answer out.

```hum
define greet with name
    say "Hello, {name}!"

greet with "Sam"
greet with "Alex"
```

```output
Hello, Sam!
Hello, Alex!
```

```hum
define double with n
    give back n * 2

say double with 21
set answer to double with 5
say "Ten is {answer}"
```

```output
42
Ten is 10
```

Use `and` between several values. If one call sits inside another, put brackets around the inner one:

```hum
define add_numbers with a and b
    give back a + b

say add_numbers with 2 and 3
say add_numbers with 1 and (add_numbers with 2 and 3)
```

```output
5
6
```

A function can call itself. Here is the factorial of a number (5 factorial is 5 × 4 × 3 × 2 × 1):

```hum
define factorial with n
    if n is at most 1
        give back 1
    give back n * factorial with (n - 1)

say factorial with 5
say factorial with 10
```

```output
120
3628800
```

Variables made inside a function stay inside it:

```hum-error
define make_secret
    set secret to 42

make_secret
say secret
```

```output
Line 5: I don't know "secret".
    say secret
Create it first with: set secret to ...
```

The last line failed because `secret` only exists inside `make_secret`, so out here HL has never
heard of it. (A function that needs no values is used just by writing its name, like `make_secret`.)

**Changing a variable from inside a function.** `set` always makes a *new* variable. So inside a function,
`set total to ...` makes a private `total` and leaves the outside one alone. To update the outside one, use `change`:

```hum
set total to 0
define add_to_total with n
    change total to total + n

add_to_total with 5
add_to_total with 10
say total
```

```output
15
```

If you write `set` there by mistake, the program still runs, but HL prints a **Heads up** to tell you.

**A call takes everything after `with`.** `double with 2 + 1` means `double with (2 + 1)`, which is 6.
To calculate after the call, put the call in brackets: `(double with 2) + 1` is 5. HL prints a heads-up when you write
a calculation after `with` without brackets, so you always say which one you mean.

```hum
define double with n
    give back n * 2

say double with (2 + 1)
say (double with 2) + 1
```

```output
6
5
```

## 9. When things go wrong

Everyone makes mistakes, including professionals, and HL's job is to help you fix yours. An error
message tells you **what** went wrong, **where** (the line number and the line), and often **how to fix it**:

```hum-error
say "Total: " + 5
```

```output
Line 1: You tried to add a number to text.
    say "Total: " + 5
Use number of "5" to turn text into a number, or build text with braces, like "Total: {x}".
```

```hum-error
sya "hello"
```

```output
Line 1: I don't understand "sya" at the start of a line.
    sya "hello"
Did you mean "say"?
```

Read the first line, then look at the line it shows. Most mistakes are typos.

When the mistake happens inside a function, the message also lists the calls that led to it, innermost first, so you can see which call sent the bad value:

```text
Line 2: I can only multiply numbers, but this has text and a number.
    give back w * h
To turn text into a number, use: number of "5"
This happened inside "area", which was called from:
  line 4, inside "report"
  line 6
```

**Catching errors yourself.** Sometimes you expect something might fail, like dividing by a number a
person typed. Put it in `try`, and write what to do `if that fails`. The message is saved in a
variable called `problem`:

```hum
try
    say 10 / 0
if that fails
    say "Oops: {problem}"
say "The program keeps going."
```

```output
Oops: You can't divide by zero.
The program keeps going.
```

Besides `problem` you also get `problem_line` (the line it happened on) and `problem_kind`. The kind is `"fail"` when
your own program raised the error with `fail with` (see below), and `"error"` when HumanLang found a mistake, which is
usually a bug in your program. Telling them apart means a real bug never hides behind a friendly message:

```hum
define pick with n
    if n is 0
        fail with "zero is not allowed"
    give back item n of list of "a", "b"

for each n in list of 1, 0, 5
    try
        say pick with n
    if that fails
        if problem_kind is "fail"
            say "refused: {problem}"
        otherwise
            say "BUG on line {problem_line}: {problem}"
```

```output
a
refused: zero is not allowed
BUG on line 4: You asked for item 5, but there are only 2 items.
```

**Making your own errors.** Your program can report a problem itself with `fail with`. A function can use it to
refuse bad input, and whoever called the function catches it with `try`:

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

```output
5
Oops: I can't divide 1 by nothing.
```

If nothing catches it, the program stops and shows your message as the error. To end a program on purpose,
write `stop the program` (it works inside functions and loops too):

```hum
say "Checking..."
set age to 15
if age is less than 18
    say "Sorry, adults only."
    stop the program
say "Welcome in!"
```

```output
Checking...
Sorry, adults only.
```

To check what kind of thing a value is, ask: `x is a number`, `x is a text`, `x is a list`, `x is a record`.

```hum
set things to list of 5, "five", list of 5
for each thing in things
    if thing is a number
        say "number"
    otherwise if thing is a text
        say "text"
    otherwise
        say "something else"
```

```output
number
text
something else
```

**Two helpful commands**

- `hl check myfile.hum` looks for mistakes without running the program.
- `hl run --trace myfile.hum` prints each line right before it runs, so you can watch your program think.

## 10. Extra tools: modules

Some features are switched on with `use`, to keep things simple until you need them.

| Module | What you get |
|---|---|
| `math` | `square root of`, `absolute value of`, `round of`, `floor of`, `ceiling of`, `sum of`, `largest of`, `smallest of` |
| `text` | `split`, `join`, `replace`, `trim of`, `first 3 letters of`, `last 3 letters of`, `letters 2 to 4 of`, `find` |
| `random` | `random item from` a list (`random number from 1 to 10` works without `use`) |
| `dates` | `the date today`, `the time now` |
| `files` | `read file`, `write ... to file`, `add ... to file`, `file exists` |

```hum
use math
set prices to list of 2.5, 4, 10.25
say "Total: {sum of prices}"
say "Most expensive: {largest of prices}"
say "Square root of 144: {square root of 144}"
say "2.5 rounds to {round of 2.5}"
```

```output
Total: 16.75
Most expensive: 10.25
Square root of 144: 12
2.5 rounds to 3
```

**Money and decimals.** Numbers are exact, so shop arithmetic comes out the way you would do it on paper.
`round of X to 2 places` rounds (0.5 rounds up), and `text of X to 2 places` makes text with exactly two decimals, so `12.5` prints as `12.50`:

```hum
use math
say 0.1 + 0.2 is 0.3
set price to 19.99
set total to price * 3
say "Total: {text of total to 2 places}"
say "With 7.5% tax: {text of (total * 1.075) to 2 places}"
say "Per person (3 people): {round of (total / 3) to 2 places}"
say "Whole euros: {total divided evenly by 1}"
```

```output
yes
Total: 59.97
With 7.5% tax: 64.47
Per person (3 people): 19.99
Whole euros: 59
```

`A divided evenly by B` gives only the whole part of a division, and works on numbers of any size.

```hum
use text
set words to split "one,two,three" by ","
say words
say join words by " + "
say replace "cat" by "dog" in "the cat sat"
say "[{trim of "   padded   "}]"
```

```output
list of one, two, three
one + two + three
the dog sat
[padded]
```

To take a piece of text, or to find where something is:

```hum
use text
set word to "banana"
say first 3 letters of word
say last 2 letters of word
say letters 2 to 4 of word
say find "nan" in word
say find "z" in word
```

```output
ban
na
ana
3
0
```

`find` gives the position (counting from 1), or `0` when the text isn't there. The same phrases work on lists:
`first 2 items of colors`.

```hum
use files
write "Hello from HL" to file "note.txt"
say read file "note.txt"
```

```output
Hello from HL
```

`write` replaces the whole file. `add ... to file` puts text at the end instead, and makes the file if it isn't
there yet. `file exists` lets you check first:

```hum
use files
write "one\n" to file "log.txt"
add "two\n" to file "log.txt"
say read file "log.txt"
say file exists "log.txt"
say file exists "nothing-here.txt"
```

```output
one
two

yes
no
```

Random numbers and dates change every time, so their output will be different on your computer:

```hum-random
use random
use dates
say "Today is {the date today} and the time is {the time now}."
say "Lucky colour: {random item from list of "red", "green", "blue"}"
say "Dice roll: {random number from 1 to 6}"
```

## 11. Files, spreadsheets and bigger programs

**Reading a spreadsheet.** A CSV file is a table saved as text. `read csv` turns it into a list of records, one per row, named by the first line (`use files` first). Every value is text, so use `number of` to calculate:

```hum-fragment
use files
set rows to read csv "sales.csv"
set total to 0
for each row in rows
    add (number of (field units of row)) * (number of (field price of row)) to total
say "Total: {text of total to 2 places}"
```

`write csv rows to file "copy.csv"` saves a list of records (or a list of lists) back, adding quotes where a value needs them. If a file is messy, `read csv "sales.csv" as rows` gives every line as a plain list and lets you decide what to do with the odd ones.

**Splitting a program into files.** When a program gets long, move parts to other files and bring them in with `use` and the file name in quotes, at the top:

```hum-fragment
use "money.hum"
use "lib/report.hum"
say price_text with 12.5
```

Everything the files make (functions and variables) can be used everywhere. Each file is read once, and names are looked up from the folder of the file that says `use`. If two files make a function with the same name, the later one wins and HL prints a heads-up that says where the other one is, so rename one. When a mistake is inside a file, the error says which file and line.

**Stopping a runaway program.** A program that never ends can be stopped with Ctrl+C (HL says which line it was on), or you can give it a limit: `hl run --time-limit 10 myfile.hum`. A text or list that keeps growing, or a program that prints without end, is stopped by HL with a message that names the line.

## 12. Put it together

A tip calculator:

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

```output
How much was the bill? 80
What percent tip? 15
Tip: 12
Total: 92
```

A grade checker with a function:

```hum
define grade_for with score
    if score is at least 90
        give back "A"
    otherwise if score is at least 75
        give back "B"
    otherwise if score is at least 50
        give back "C"
    otherwise
        give back "Try again"

for each score in list of 95, 80, 60, 20
    say "{score} gets {grade_for with score}"
```

```output
95 gets A
80 gets B
60 gets C
20 gets Try again
```

And a number-guessing game. It uses everything you've learned. Type this into a file called
`guess.hum` and run it (the secret number is random, so the output isn't shown here):

```hum-fragment
set secret to random number from 1 to 10
set guess to 0

repeat while guess is not secret
    ask number "Guess a number from 1 to 10:" and save it as guess
    if guess is less than secret
        say "Too low"
    otherwise if guess is greater than secret
        say "Too high"

say "You got it!"
```

**Challenges**

1. Change the game so the player has only 3 guesses.
2. Make a program that asks for 3 names, puts them in a list, and says hello to each one.
3. Write a function `is_even` that gives back `yes` when a number is even (hint: `mod`).

## 13. Design: pages, buttons and drawings

So far HumanLang has *said* things. It can also *show* things: a page with buttons and text, a drawing of a football,
even a little pixel-art person. You describe what you want, in words, and HumanLang draws it.

Where do you see it? In the **Playground** a **Preview** tab appears and follows what you type. In **VS Code** the
Run button opens a preview beside your code. On your computer, `hl run myfile.hum` opens the page in your browser, and
`hl build myfile.hum` saves it as a web page (`myfile.html`) that you can put on any website.

### Your first page

```hum-page
show a page titled "My first page"
    put a heading "Hello!"
    put a text "This is my page."
    put a button "Click me"
```

`show a page titled "..."` starts a page. Everything **indented below it** is on the page. Each `put a ...` line puts one
thing on it: a `heading`, a `text`, a `button`, an `input` (a box to type in), and more. The words to show go in quotes.
(The button does not do anything yet. This chapter is only about how things *look*.)

### Making things look good: `with`

After a thing, write `with` and then what it should look like. Join several with commas.

```hum-page
show a page titled "Colours" with background light yellow
    put a heading "Colourful!" with colour dark blue
    put a text "Big and bold" with size big, bold
    put a button "Go" with background green, colour white, rounded, padding 12
```

- **Colours** can be names (`red`, `dark blue`, `sky blue`, `light gray`, `hot pink`, ...) or a code like `"#ff8800"`.
  Put `dark`, `light` or `pale` in front of most colours to change them.
- **Sizes** are `tiny`, `small`, `normal`, `big`, `huge`, or a number of pixels.
- Other things you can say: `bold`, `italic`, `underlined`, `align right`, `font serif`, `border 2`,
  `border colour red`, `rounded`, `shadow`, `padding 10`, `width 200`, `height 100`.

If you ask for something a thing can't have, HL tells you what it *can* have.

### Boxes and rows: where things go

A **box** holds things and stacks them from top to bottom. A **row** puts them side by side. They can go inside each other.
`space between` sets the gap, and `columns 3` makes a grid.

```hum-page
show a page titled "Layout" with background light gray
    put a box with background white, padding 16, rounded 12, shadow, space between 10
        put a heading "Sign in"
        put an input with hint "Your name"
        put a row with space between 8
            put a button "OK" with background blue, colour white
            put a button "Cancel"
```

### Loops build pages

Pages are made by a real program, so everything you know works inside them: `for each`, `repeat`, `if`, variables and
functions. Here is the look of a calculator, with 16 keys made by one loop:

```hum-page
set keys to list of "7", "8", "9", "+", "4", "5", "6", "-", "1", "2", "3", "*", "0", ".", "=", "/"

show a page titled "Calculator" with background light gray, centered
    put a box with background white, padding 16, rounded 14, shadow, space between 10
        put a text "0" with size huge, align right, background black, colour white, padding 10, width full
        put a box with columns 4, space between 8
            for each key in keys
                put a button key with rounded 8, size big
```

### Drawings: shapes at a spot

Inside a `drawing`, you place shapes at a spot: `at 150, 100` means 150 across and 100 down from the top left corner.
You can draw a `circle` (with a `radius`), an `oval`, a `rectangle`, a `square`, a `triangle` (with `width` and `height`),
a `line` (`from 0, 0 to 100, 50`), a `polygon` (`from` and then corners joined by `to`), and a `text` placed at a spot.
Shapes are drawn in the order you write them, so later ones are on top.

```hum-page
show a page titled "Football"
    put a drawing with width 300, height 300, background sky blue, rounded 12
        put a rectangle at 0, 220 with width 300 and height 80 and colour green
        put a circle at 150, 130 with radius 70 and colour white and border colour black and border 4
        put a polygon from 150, 95 to 180, 117 to 168, 152 to 132, 152 to 120, 117 with colour black
        put a text "GOAL!" at 100, 20 with size big, bold, colour white
```

### Pixel art

Pixel art is a picture made of little squares. First say which letter is which colour with `where`, then draw the picture
with one line of letters for each row of squares. A `.` (or a space) is a see-through square.

```hum-page
show a page titled "Pixel hero" with background light blue
    put pixel art at 10, 10 with pixel size 14
        where "h" is brown, "s" is skin, "e" is black, "b" is blue, "p" is dark gray
        "...hhhh..."
        "..hhhhhh.."
        "..ssssss.."
        "..sesses.."
        "..ssssss.."
        "...ssss..."
        "..bbbbbb.."
        ".bbbbbbbb."
        ".sbbbbbbs."
        ".sbbbbbbs."
        "..pp..pp.."
        "..pp..pp.."
```

Every row must be the same length, and every letter needs a colour. HL checks both and tells you which line is wrong.

### Reuse a drawing with a function

A function can put things on the page, so you can draw something once and use it again and again:

```hum-page
define ball with x and y
    put a circle at x, y with radius 14 and colour white and border 3 and border colour black

show a page titled "Three balls"
    put a drawing with width 240, height 60, background green, rounded 10
        ball with 40 and 30
        ball with 120 and 30
        ball with 200 and 30
```

**Challenges**

1. Make a page with your name as a heading and a box with three buttons in a row.
2. Draw a house: a square for the walls, a triangle for the roof, and a rectangle for the door.
3. Draw your own pixel-art face, 8 squares wide.
4. Use `repeat` or `for each` to draw ten circles in a row.


## 14. Games: sprites, keys and a game loop

HL can make 2D arcade games: shooters, mazes, platformers, ladder climbers. A game is made of a few simple pieces:

1. **Sprites**: small pictures made of squares (like the pixel art in chapter 13).
2. **Maps**: a grid of tiles, for walls, floors and coins.
3. **A game**: the screen size, and the parts that say what happens: when the game starts, on every frame, when a key is pressed.

A game "frame" is one picture. The computer draws about 60 of them every second, and your `every frame` part runs once
for each one. That is how things move: change a number a little, draw again, and the picture moves.

Here is the smallest game that moves something. Use the arrow keys.

```hum-game
make a sprite called ship
    where "g" is lightgreen and "d" is darkgreen
    "....g...."
    "...ggg..."
    ".ggggggg."
    "ggggggggg"
    "gdgdgdgdg"

set x to 140

play a game titled "My first game" with size 320 by 240 and background black
    every frame
        if key "left" is down
            change x to x - 3
        if key "right" is down
            change x to x + 3
        draw the sprite ship at x, 200
```

Run it in the Playground (the Preview tab shows the game, click it first so it hears your keys), or save it as
`ship.hum` and type `hl run ship.hum`: the game opens in your browser.

Four things to remember:

- **Sprites** are made like pixel art: a `where` line says what each letter is, then one text per row. A dot means
  "nothing". `with pixel size 4` makes every square 4 dots wide (4 is the default).
- **`draw the sprite ship at x, y`** puts a sprite on the screen. `x` is across, `y` is down from the top left.
- **Use `change`, not `set`,** to change a number you made before the game. (`set` inside a game part makes a new
  little variable that is forgotten when the part ends.)
- **Keys** are written in quotes: `"left"`, `"right"`, `"up"`, `"down"`, `"space"`, `"enter"`, `"a"` to `"z"`, `"0"` to `"9"`.

### The parts of a game

```hum-game
set score to 0

play a game titled "Parts" with size 200 by 120 and background navy
    when the game starts
        change score to 100
    every frame
        put a text "Score {score}" at 8, 8 with colour white
    every 2 seconds
        add 1 to score
    when the key "space" is pressed
        add 10 to score
        play the sound "coin"
```

| Part | When it runs |
|---|---|
| `when the game starts` | once, before the first picture |
| `every frame` | about 60 times a second |
| `every 2 seconds` | every 2 seconds (any number) |
| `when the key "space" is pressed` | once each time the key goes down |
| `when the mouse is clicked` | each click on the game (`mouse x` and `mouse y` say where) |

Inside a part you can use everything from the other chapters: `if`, `repeat`, lists, your own functions. A function can
`draw` too, if a game part calls it. `put a text`, `put a circle`, `put a rectangle` and the other shapes from chapter 13
work in a game as well: they are drawn in the frame. Text always stays on the screen (good for a score); sprites and
shapes move when the camera moves.

### Animation and turning

A sprite can have several **frames**, like a flip book. Write all the rows, one frame after another, and say how many:

```hum-game
make a sprite called walker with 2 frames
    where "o" is orange
    ".oo."
    "oooo"
    "o..o"
    ".oo."
    "oooo"
    ".oo."

set x to 10

play a game titled "Walk" with size 160 by 80 and background black
    every frame
        change x to x + 1
        if x is greater than 150
            change x to 0
        set pose to 1 + (frame number divided evenly by 10) mod 2
        draw the sprite walker at x, 30 frame pose
```

`frame number` counts the pictures so far. `divided evenly by` rounds down, so `pose` flips between 1 and 2 every ten
pictures. To turn a sprite around, add `facing left` (always) or `facing left when goes_left` (only when a yes/no
variable says so).

### Maps: walls, floors and coins

A **map** is a grid of tiles. It works like a sprite, but each letter is one tile, and a tile can be a colour or a
sprite you made before. `tile size` says how many dots wide each tile is.

```hum-game
make a sprite called coin
    where "y" is yellow
    "...yy..."
    "..yyyy.."
    ".yyyyyy."
    ".yyyyyy."
    ".yyyyyy."
    ".yyyyyy."
    "..yyyy.."
    "...yy..."

make a map called level with tile size 16
    where "#" is blue and "c" is the sprite coin
    "##########"
    "#c..c..c.#"
    "#........#"
    "##########"

set px to 20
set score to 0

play a game titled "Coins" with size 160 by 64 and background black
    every frame
        if key "right" is down
            change px to px + 2
        if key "left" is down
            change px to px - 2
        draw the map level
        put a circle at px, 24 with radius 6 and colour red
        if tile at px, 24 of level is "c"
            change tile at px, 24 of level to "."
            add 1 to score
            play the sound "coin"
        put a text "Coins {score}" at 6, 4 with size small and colour white
```

- `tile at x, y of level` is the letter on the map at that spot of the screen (it is empty text outside the map).
- `tile in column 3, row 2 of level` is the same by tile number (the first column and row are number 1).
- `change tile at x, y of level to "."` and `change tile in column 3, row 2 of level to "."` change one tile.
  The new letter must be in the map's `where` line (a dot is always allowed).
- `how many columns in level` and `how many rows in level` tell the size.

### Hitting things, the camera and sound

- `the sprite ship at x, y touches the sprite alien at a, b` is `yes` when the two pictures overlap.
- `move the camera to 100, 0` slides the view, so a level can be much wider than the screen. Text stays put.
- `play the sound "coin"` plays a short sound. Sounds: `jump`, `coin`, `hit`, `shoot`, `explosion`, `powerup`, `win`,
  `lose`, `beep`, `blip`, `step`.
- `stop the game` ends the game (the last picture stays).
- `game time` is the seconds since the game began.

### Sharing a game

`hl build mygame.hum` saves the whole game as one web page, `mygame.html`. Put that file on any website or send it to
a friend: it opens in any browser. It needs the internet when it starts, to load the part that runs HL in the browser. Want it to work with no internet at all? Type `hl build mygame.hum --offline`: the page carries everything it needs (a bigger file, around 18 MB).

The **Games** page on the website has four full arcade games: Planet Defenders, Maze Muncher, Crate Climber and Sky Runner.
Press **Inspect** on one to read its code with every part explained (the code is also in the `games` folder). Change a number,
run it, and see what happens: that is the fastest way to learn.

### Try it

1. Add a second sprite and make it drop from the top of the screen, one pixel more every frame. Use
   `the sprite ... touches the sprite ...` to catch it with your ship.
2. Add `play the sound "hit"` when it lands.
3. Make the game end with `stop the game` after 10 catches.

## 15. Calculating and remembering

### Formulas from text

`calculate` works out a formula written as text. It understands brackets and the order of operations (times before plus),
so a calculator can take whatever the person types.

```hum
say calculate "2 * (3 + 4)"
say calculate "2 + 3 * 4"
say calculate "10 / 4"
say calculate "sqrt(16) + 2^3"
say calculate "50% * 80"
```

```output
14
14
2.5
12
40
```

It knows `+ - * /`, brackets, powers (`^`), percent (`50%`), `!` (factorial), `pi`, and functions such as `sqrt`, `abs`, `round`,
`floor`, `ceiling`, `min`, `max`, `sin`, `cos`, `tan` (in degrees) and `log`. It can only do maths, so it is safe to use on
anything a person types. A formula that makes no sense is an error you can catch:

```hum
try
    say calculate "2 +"
if that fails
    say "That is not a formula."
```

```output
That is not a formula.
```

### Remembering between runs

`remember` saves something so it is still there the next time the program runs. `recall` brings it back, and `forget` throws it away.
On your computer it is saved in a `.hl-memory` folder next to your program. On a web page it is saved in the browser.

```hum
set visits to recall visits
if visits is nothing
    set visits to 0
add 1 to visits
remember visits
say "You have been here {visits} time(s)."
```

```output
You have been here 1 time(s).
```

Run it again on your computer and it says 2, then 3. You can remember numbers, text, yes/no, lists and records. To save something under
another name, say `remember score as "high score"` and `recall "high score"`. Games use this for real high scores.

## 16. Pages that react: buttons and text boxes

A page can do things when it is used. Give each text box a name with `called`, then say what happens `when the button "..." is clicked`.
Inside, `the number in amount` is what the person typed in the box (use `the text in amount` for words).

```hum-page
set total to 0

show a page titled "Adder"
    put a heading "Adder"
    put an input called amount with hint "A number"
    put a button "Add"
    put a text "Total: {total}"

when the button "Add" is clicked
    change total to total + the number in amount
```

How it works: the program runs once and shows the page. Each click runs the matching `when` part, and then the page's own lines
run **again** with the new values, so the page always shows the latest. That means a page can show a list that grows, with a
`for each` loop inside it. Remember to use `change`, not `set`, to update a variable that was made earlier.

(On this website the example above is only a picture. Open the Playground, paste it in and press Run, and the button works.)

Other things you can listen for: `when the input amount changes` runs every time the person types in that box.

Try making a unit converter (centimetres to inches), a to-do list that keeps its items with `remember`, or a calculator whose buttons
add characters to a text and whose `=` button runs `calculate`. In the Playground press **Post to Community** to share it.

## 17. Better games

### Physics for platformers

A **body** runs, jumps and falls for you and lands on the solid tiles of a map. You only say what the person pressed.

```hum-game
make a sprite called hero
    where "g" is green
    "gggg"
    "gggg"
    "gggg"
    "gggg"

make a map called level with tile size 16
    where "#" is blue
    "..........................."
    "..........................."
    "..........................."
    "..........................."
    "..........................."
    "..........................."
    "...........###............."
    "..........................."
    "###########################"

make a body called hero at 20, 40 with size 8 by 8

play a game titled "Physics" with size 200 by 144 and background black
    every frame
        make the body hero stop
        if key "left" is down
            make the body hero run left
        if key "right" is down
            make the body hero run right
        if key "up" is down
            make the body hero jump
        update the body hero on the map level with solid "#"
        draw the map level
        draw the sprite hero at the body hero
```

- `make a body called NAME at X, Y with size W by H` (optional: `gravity`, `speed`, `jump` numbers).
- `make the body NAME run left`, `run right`, `stop`, `jump` (only from the ground), `bounce` (jump in mid-air).
- `update the body NAME on the map LEVEL with solid "#" and "B"` moves it one step. Tiles with those letters are solid.
- `the x of the body NAME`, `the y of the body NAME`, `the body NAME is on the ground`, `the body NAME is falling`.
- `move the body NAME to X, Y` puts it somewhere new (for starting over).
- `draw the sprite hero at the body hero` draws it and turns it the way it runs.

### Your own pictures, sounds and music

Put picture files (png, jpg, gif, webp) and sound files (wav, mp3, ogg, m4a) in the same folder as your program, then use them by name.
In the Playground, open the **Files** tab and add them there.

```
draw the picture "face.png" at 10, 20 with size 32 by 32
play the sound "boom.wav"
play the music "theme.mp3"
stop the music
```

There are also five built-in tunes, no file needed: `play the music "adventure"`, `"chill"`, `"chase"`, and two for boss fights, `"boss"` and `"doom"`.

### Phones and offline

On a phone or tablet a game shows buttons on the screen for the keys it uses (arrows, A for space, B for enter). Nothing to add.
`hl build mygame.hum --offline` saves a page that works with no internet; it works for live pages too.

## 18. Finding mistakes: step through

Type `hl debug myprogram.hum` to go through a program one line at a time. For each line you see what it does in plain words
and which variables changed. Press Enter for the next line, `c` to run to the end, `v` to see every variable, `q` to quit.
In the Playground press **Step through**: Back and Next walk the program, the current line is marked, and the variables that
just changed are highlighted.

## 19. Where next

- The **Reference** lists every word HL understands, in one place.
- `hl format myfile.hum` tidies your spacing and indentation.
- Install the editor extension for coloured code, live error messages and a page preview.
- Share what you made: press **Post to Community** in the Playground.
- Stuck? Read the error message slowly, then check the line it shows. Most mistakes are a typo or a missing indent.

Welcome to programming!
