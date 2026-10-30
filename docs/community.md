# Growing the community

A practical guide for whoever runs the project's spaces. Keep it small and welcoming; beginners are the point.

## Where people gather

| Place | Use |
|---|---|
| GitHub **Issues** | bugs, beginner feedback, proposals (forms are in `.github/ISSUE_TEMPLATE`) |
| GitHub **Discussions** | questions, "show your program", ideas. Turn it on in the repository settings |
| Chat (Discord or similar) | quick help and friendly chat. Start with a few rooms only |

Suggested chat rooms: `#welcome`, `#help` (any question is fine), `#show-your-programs`, `#ideas`, `#contributors`.

**Welcome message** (pin it):
> Welcome to HumanLang! No question is too small. When you ask for help, paste your program and the full error
> message. We are all learning. Be kind (see the Code of Conduct), and tell us about anything confusing: that is
> how HL gets better.

## The feedback loop (this is what makes the language good)

1. Every confusing moment becomes a **Beginner feedback** issue (label `beginner-feedback`).
2. Once a month, count the labels. Anything reported by 3 or more different people is a candidate for:
   a better error message, a hint (`humanlang/hints.py`), a tutorial fix, or, rarely, a language proposal.
3. Fix the error message first. Change the language only if no message can fix the confusion.
4. Tell the reporter what changed. Closing the loop is what keeps people reporting.

## Making contributing easy

- Keep 5-10 issues labelled `good first issue`: typo fixes, new tutorial challenges, new hints for words from other
  languages, translations of the docs, new example programs.
- Review pull requests within a few days, and thank people by name in the changelog.
- New contributors can start with `CONTRIBUTING.md`, which has the three commands needed to run all the checks.

## Things to try

- A **program of the month** from the "show your programs" room.
- A short classroom pack: the tutorial, 10 exercises and the beginner-test sheet, for teachers.
- Translated tutorials. HL names can already be written in any language; only the keywords are English.
