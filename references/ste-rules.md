# ASD-STE100 in this skill

ASD-STE100 is Simplified Technical English. The AeroSpace and Defence Industries Association of Europe (ASD) publishes it as a specification with two parts: a set of writing rules and a dictionary of about 900 approved words. This skill applies the writing rules and ignores the dictionary, so every word is allowed. Define each technical term where it first appears.

The table summarizes the published description of the standard (Wikipedia, "Simplified Technical English", read on 2026-10-05). Issue 9, of January 2025, has 53 writing rules. The exact wording of each rule is in the specification at asd-ste100.org. The checker, `scripts/plain_check.py`, tests only the rows marked in the last column.

| Rule | Limit or form | Checked |
|---|---|---|
| Sentence length | At most 20 words in an instruction (a numbered step) and 25 words in a description | yes |
| Paragraph length | At most six sentences, on one topic | yes, the six sentences |
| One instruction per sentence | Write one instruction in each sentence | no |
| Active voice | Use the passive voice in descriptions only, and only when the actor is unknown | yes, as a heuristic |
| Simple verb forms | Infinitive, imperative, simple present, simple past and simple future. No complex verb constructions built with auxiliary verbs | perfect tenses only, as a heuristic |
| Noun clusters | At most three words in a multi-word noun | no |
| Complete sentences | Do not drop the subject, the verb or the articles to save words | no |

The checker tests no rule about words. Progressive tenses ("is running") are not checked, because a pattern match cannot tell them from adjectives such as "is interesting".
