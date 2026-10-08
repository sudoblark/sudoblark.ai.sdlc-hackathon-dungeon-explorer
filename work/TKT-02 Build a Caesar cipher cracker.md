---
status: backlog
---
## Description

A Caesar cipher tool that also breaks the cipher. It encrypts and decrypts a message by shifting each letter a fixed number of places, with ROT13 as the shift everyone knows. Then it cracks a message without the key: it tries all 26 shifts and scores each one against how often letters appear in English, so the most English-looking result wins. That's frequency analysis, the technique that broke substitution ciphers centuries before computers.

## Agent instructions

1. Find a published table of English letter frequencies, and record the source in this ticket. Show it to the person before planning.
2. Ask the person which language, test runner and linter to use, and what to call the project's folder. Wait for their answers.
3. Propose a commit plan, and the post-commit tests that prove the finished project works, as rows in the tables below. Commits go in landing order. The first commit sets up the folder with its test runner and linter, and each later commit adds one behaviour with its tests. Wait for the person's sign-off, then propose `docs(work): plan TKT-02 (TKT-02)` for them to commit.
4. Work the plan one row at a time.

## Commit plan

| # | Commit message | What it covers | Status |
| --- | --- | --- | --- |

## Post-commit testing

| # | Check | How | Status |
| --- | --- | --- | --- |

## Acceptance criteria

- [ ] The source for the letter frequencies is recorded in this ticket
- [ ] The person signed off the language, the tooling and the folder name
- [ ] The person signed off the commit plan
- [ ] Decrypting with the shift used to encrypt gives the message back
- [ ] Case, spaces and punctuation come through unchanged
- [ ] ROT13 applied twice gives the message back
- [ ] Given a sentence or two of ciphertext, the cracker finds the shift and shows the message, with the next best guesses and their scores

## Stretch goals

Once every acceptance criterion is met, a team with time to spare can add these to the plan as new commits:

- The Vigenère cipher, where a keyword sets a different shift for each letter
- Cracking Vigenère: find the key length, then crack each letter of the key as its own Caesar shift
- Encrypting, decrypting and cracking whole text files
