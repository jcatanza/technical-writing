---
name: technical-writing
description: Write technical explanations (code, statistics, machine learning, systems) that a smart non-specialist can follow the first time, and learn from every correction the reader makes. Use it when you explain, summarize or rewrite technical material for a reader who is not an expert in it; when the reader asks what a word means or asks for plain English; when the reader says a passage is unclear, confusing, obtuse, jargon or hard to follow; and when the reader accepts your correction of such a passage, which you must then record as an example. The rules in short are to answer first, give a tiny worked example before the names, define every term, say what every number counts, recommend one action, and follow the ASD-STE100 writing rules without its word list.
---

# Technical writing

This skill makes technical explanations followable on the first read, and it improves each time the reader flags a passage.
The reader is smart, is not a specialist, and reads slowly, so every extra word costs them.
The rules come from the reader's own corrections. Those are stored as pairs and summarized in `references/examples-digest.md`.

## Before you explain anything

Read `references/examples-digest.md`. If the file is missing, run `python3 ~/.claude/skills/technical-writing/scripts/build_digest.py` first.
Its first section ranks the ways earlier answers failed this reader. Check your draft against the top three.

## The procedure

1. **Answer first.** Make the first sentence the answer, in plain words. If the reader asked what a word means, the first sentence is its everyday meaning.
2. **Give a tiny example before the names.** Use one small case with real numbers and say what each number counts. Use a table only for three or more items, and give each column a header that says what it counts.
3. **Define every non-everyday word where it first appears.** Do not use abbreviations, file or function names, line numbers or labels you coined in this conversation, unless the reader asked about code. If a word is yours, say so and use the everyday word. When a term has a standard definition, give it after the example of step 2, by its standard parts and their numbers. Show a simpler restatement of the term, such as an invented noun, only after that. Do not define a term with another one the reader has not met.
4. **Say what every number counts and what it is compared with.** Write "raises sensor A's accuracy from 0.412 to 0.497", never "adds 0.09 to 0.12".
5. **Recommend one action.** Leave out the cases that do not apply.
6. **Write to the ASD-STE100 rules, but do not restrict the vocabulary.** ASD-STE100 is Simplified Technical English. Take its writing rules: 25 words at most in a sentence and 20 in a numbered step, one topic per sentence and one instruction per step, six sentences at most in a paragraph, the active voice, simple tenses, noun clusters of three words at most, and no dropped articles or subjects. Do not take its word list. Use any word the reader needs, and define it where it first appears (step 3). `references/ste-rules.md` has the details.
7. **Keep it short.** Answer only what was asked. If the question could mean two things, ask which one. Prefer numbered steps when the reader must act.
8. **Check before sending.** Reread the draft as someone who has not seen this conversation. For a document, or when the reader has already flagged this topic, also run `python3 ~/.claude/skills/technical-writing/scripts/plain_check.py draft.md --known <abbreviations the reader knows>` and fix what it flags. Treat its flags as hints, because it cannot tell whether a text is clear (see Limits).

## When the reader flags a passage

The reader may call something unclear, confusing, obtuse or jargon, or ask "what do you mean by X". Then:

1. **Keep the flagged excerpt.** Write the passage the reader reacted to, verbatim and no longer than needed, to a temporary file. If the reader quoted it, use the quote.
2. **Own it in one line, then fix that exact sentence** from scratch, with a concrete case (procedure steps 1 to 7). Do not answer a nearby question. When you define one word, check that the definition does not bring in a second undefined word.
3. **Wait for the reader's verdict.** The correction counts as accepted when the reader says so ("got it", "yes", "excellent", "that makes sense") or builds on it, with a follow-up question about its content or the next task. If the reader flags it again, fix it again and keep the failed text as an attempt.
4. **Record the pair once it is accepted.** Write the accepted correction, verbatim, to a second temporary file, then run:

   ```
   python3 ~/.claude/skills/technical-writing/scripts/add_example.py \
     --flagged flagged.txt --accepted accepted.txt \
     --complaint "<the core of the reader's words>" --lesson "<one line: what the correction did differently>" \
     --tags <tag,tag> --signal "<explicit: their words, or implicit: what they did>" \
     [--attempt first_fix.txt] [--known SNR,dBFS] [--coined-flagged "label one;label two"] [--source "<project, date>"]
   ```

   Write the core of the complaint: what was unclear and what the reader asked for. Leave out venting, jokes and anger. The script also strips obvious venting, such as feeling words and emphatic sentences that say nothing about the passage, and shows what it removed. Pass `--keep-wording` to store the words as written. The pair goes to `examples-local/`, which git ignores, so the reader's real excerpts stay on this machine. Add `--public` only after the reader confirms that the pair holds no course, client or personal material. The script then refuses a pair that holds an email address, a home folder path, a link or a term from `private-terms.txt`. Pick every tag from `TAGS` in `scripts/examples_lib.py` that applies. Then run `python3 -m pytest -q` from the skill folder (it needs pytest; `pip install -r requirements-dev.txt`).
5. **Tell the reader in one line** that the pair was added, with its number and tags. Do not commit; the reader decides when. If the tests fail because the checker now flags a correction the reader accepted, say so and ask before changing the checker.
6. **Propose a rule, never add one silently,** when a tag has no matching procedure step or one tag has recurred three or more times. Say so in one sentence and offer a one-line rule.

## Limits

The checker finds mechanical faults only, and its passive-voice and tense checks are heuristics. On the first reader's own history it flagged the answers they complained about almost as often as the ones they did not, so a clean report is not evidence of clarity. Undefined words and abstract openings, the faults the reader flags most, need your judgment and the examples.
