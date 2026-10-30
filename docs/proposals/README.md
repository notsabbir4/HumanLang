# Language proposals (HLPs)

HumanLang stays small on purpose, so changes to the *language itself* (new phrases, new keywords,
changed meanings) go through a short written proposal. Bug fixes, error messages, docs and tooling don't need one.

## Process

1. **Look first.** Search the existing proposals and the roadmap. If a beginner already asked for it, add your voice there.
2. **Open a "Language proposal" issue**, or copy `TEMPLATE.md` to `NNNN-short-name.md` and open a pull request.
3. **Discuss.** Maintainers and the community ask: does it help beginners? Is there exactly one way to read it?
   Does it clash with the words people already use as names?
4. **Decide.** Each proposal ends as *Accepted*, *Rejected* (with reasons, kept for the record) or *Postponed*.
5. **Build.** An accepted proposal is done when it has code, tests, a friendly error for its likely mistake,
   and docs (the code blocks in `docs/` are run by the tests).

## What makes a proposal strong

- It starts from a **real stumble**: "3 of 5 beginners typed `else` here". Evidence beats taste.
- It shows the **smallest** change that fixes the stumble.
- It lists the **ambiguities** and how each is resolved.
- It says what happens to programs that exist today (see `docs/versioning.md`).
