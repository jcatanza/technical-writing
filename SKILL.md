---
name: technical-writing
description: Write technical explanations (code, statistics, machine learning, systems) that a smart non-specialist can follow the first time, and learn from every correction the reader makes. Use it when you explain, summarize or rewrite technical material for a reader who is not an expert in it; when the reader asks what a word means or asks for plain English; when the reader says a passage is unclear, confusing, obtuse, jargon or hard to follow; when the reader writes explain followed by a quoted passage; and when the reader writes accept, rewrite or drop about such a passage, where accept means you must record the pair as an example. The rules in short are to answer first, give a tiny worked example before the names, define every term, say what every number counts, recommend one action, and follow the ASD-STE100 writing rules without its word list.
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
6. **Write to the ASD-STE100 rules, but do not restrict the vocabulary.** ASD-STE100 is Simplified Technical English. Take its writing rules: 25 words at most in a sentence and 20 in a numbered step, one topic per sentence and one instruction per step, six sentences at most in a paragraph, the active voice, simple tenses, noun clusters of three words at most, and no dropped articles or subjects. Do not take its word list. Use any word the reader needs, and define it where it first appears (step 3). Treat the limits as ceilings and not as targets: vary the sentence length below them, mixing sentences of 4 to 10 words with sentences of 15 to 25, so that the text does not read as monotone. `references/ste-rules.md` has the details.
7. **Keep it short.** Answer only what was asked. If the question could mean two things, ask which one. Prefer numbered steps when the reader must act.
8. **Check before sending.** Reread the draft as someone who has not seen this conversation. For a document, or when the reader has already flagged this topic, also run `python3 ~/.claude/skills/technical-writing/scripts/plain_check.py draft.md --known <abbreviations the reader knows>` and fix what it flags. Treat its flags as hints, because it cannot tell whether a text is clear (see Limits).

## When the reader flags a passage

The reader flags a passage with `explain "xxx"`, where xxx is the text that needs a rewrite or a clarification. Four words work as commands: `explain`, `accept`, `rewrite` and `drop`. A command counts at the start of a message, at the start of a line, and in a comma-separated list of commands that opens the message, such as `accept 1, accept 2`. The same words inside a sentence are ordinary words. A plain "what do you mean by X" or "this is unclear" also counts as a flag. Then:

1. **Keep the passage.** Write xxx, verbatim and no longer than needed, to a temporary file. It is the negative example.
2. **Own it in one line, then answer from scratch in two parts.** First give an explanation in chat, with a concrete case (procedure steps 1 to 7). Then give replacement wording for the passage itself. Do not answer a nearby question. When you define one word, check that the definition does not bring in a second undefined word. When the reader flags several passages in one message, number them [1], [2] and answer all of them at once.
3. **Wait for the reader's word.** `accept N` closes passage N. A bare `accept` closes the only open passage; when several are open, ask which one. `rewrite N: <instructions>` asks for a revision. `drop N` abandons the passage. If words that are not another command follow `accept N`, treat the message as a `rewrite`. Any other reply leaves the passage open. A "got it" or a follow-up question does not close it.
4. **After `rewrite`, revise and wait again.** Keep every failed version, and keep the reader's instructions with the version they rejected. Repeat until `accept` or `drop`.
5. **Remind the reader.** While a passage is open, end each reply with one line that names it. If the chat ends first, write the open passages into whatever notes carry over to the next chat. After `drop`, record nothing.
6. **Record the pair after `accept`.** The last version before `accept` is the positive example: the explanation and the replacement wording. Write it, verbatim, to a second temporary file. Write each failed version to its own file, and end it with a line "Reader's instructions: ..." that holds the rewrite instructions the reader gave. Then run:

   ```
   python3 ~/.claude/skills/technical-writing/scripts/add_example.py \
     --flagged flagged.txt --accepted accepted.txt \
     --complaint "<the core of the reader's words>" --lesson "<one line: what the correction did differently>" \
     --tags <tag,tag> --signal "explicit: accept N" \
     [--attempt first_fix.txt --attempt second_fix.txt] [--known SNR,dBFS] [--coined-flagged "label one;label two"] [--source "<project, date>"]
   ```

   Write the core of the complaint: what was unclear and what the reader asked for. Leave out venting, jokes and anger. The script also strips obvious venting, such as feeling words and emphatic sentences that say nothing about the passage, and shows what it removed. Pass `--keep-wording` to store the words as written. The pair goes to `examples-local/`, which git ignores, so the reader's real excerpts stay on this machine. Add `--public` only after the reader confirms that the pair holds no course, client or personal material. The script then refuses a pair that holds an email address, a home folder path, a link or a term from `private-terms.txt`. Pick every tag from `TAGS` in `scripts/examples_lib.py` that applies. Then run `python3 -m pytest -q` from the skill folder (it needs pytest; `pip install -r requirements-dev.txt`).
7. **Tell the reader in one line** that the pair was added, with its number and tags. Do not commit, and do not change the document; the reader decides when with a "go". If the tests fail because the checker now flags a correction the reader accepted, say so and ask before changing the checker.
8. **Propose a rule, never add one silently,** when a tag has no matching procedure step or one tag has recurred three or more times. Say so in one sentence and offer a one-line rule.

## Other writing skills

This skill judges whether a non-specialist can follow a text. The prose-voice-editor skill judges the voice and structure of essays and articles. For an essay, use both. For a technical report or documentation, use this skill in full and take only the structure checks (opening, signposts, the W questions) from the voice editor. The ceiling rule in the ASD-STE100 step of the procedure settles the one conflict: this skill's limits cap the sentence length, and the voice editor's call for varied rhythm is met below that cap.

## Limits

The checker finds mechanical faults only, and its passive-voice and tense checks are heuristics. On the first reader's own history it flagged the answers they complained about almost as often as the ones they did not, so a clean report is not evidence of clarity. Undefined words and abstract openings, the faults the reader flags most, need your judgment and the examples.
