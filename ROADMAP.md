# Roadmap

This list is driven by **what beginners get stuck on**, not by what other languages have. The order will
change as feedback arrives. Open an issue (or a proposal, see `docs/proposals/`) to argue for something.

## Likely next (needs beginner feedback to confirm)

- **Counting loops.** Today you count with `repeat while` and a variable. A phrase such as
  `for each n from 1 to 10` would be shorter. (Open question: wording.)
- **Records.** Grouping facts about one thing, like a person with a name and an age. Today you need two lists.
- **Lines of a file**, so programs can read data without `split`.
- **Better playground:** save programs, a link to every tutorial example, step-by-step run.

## Under discussion, undecided

- Accept `else`, `print`, `true`/`false` as alternative spellings? Today HL points to `otherwise`, `say`,
  `yes`/`no` instead. We will decide after the beginner tests in `tests/BEGINNER_TESTING.md`.
- `return` instead of `give back`; 1-based vs 0-based lists (currently 1-based).
- A warning when a variable is created but never used.

## Not planned

- Speed competition with C, C++ or Java. HL is for learning and small tools.
- Free-form English. Each sentence pattern has one meaning.
- Classes and inheritance. Records first, if anything.

## Done

See `CHANGELOG.md`.
