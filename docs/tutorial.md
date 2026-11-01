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
Use a comparison such as "is", "is greater than" or "is at least".
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

## 11. Put it together

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

## 12. Where next

- The **Reference** lists every word HL understands, in one place.
- `hl format myfile.hum` tidies your spacing and indentation.
- Install the editor extension for coloured code and live error messages.
- Stuck? Read the error message slowly, then check the line it shows. Most mistakes are a typo or a missing indent.

Welcome to programming!
