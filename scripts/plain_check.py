#!/usr/bin/env python3
"""Mechanical checks for a draft explanation. It flags problems and never rewrites.

It can see: a first sentence that is long or opens with filler; abbreviations that are
never expanded; number ranges after a verb of change ("adds 0.08 to 0.11") and number
pairs in brackets; code names (backticks, file names, snake_case, calls); sentences longer
than the ASD-STE100 limits (25 words, 20 in a numbered step); paragraphs of more than six
sentences; passive voice and perfect tenses (heuristics); three or more "If ..." branches;
labels coined in the chat that are never defined; total length. It never checks the
vocabulary: ASD-STE100's word list is not part of this skill.

It cannot see whether the explanation is understandable. A clean report is the floor,
not the goal; SKILL.md holds the judgment part.

Usage:  plain_check.py draft.md [--known SNR,dBFS] [--coined "old system"] [--allow-code]
        cat draft.md | plain_check.py -
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

DEFAULT_KNOWN = {
    "AI", "DNA", "CEO", "OK", "PDF", "URL", "USA", "UK", "EU", "FAQ", "AM", "PM",
    "PST", "PDT", "UTC", "ID", "IDs", "TV", "GPS", "MIT",
    "NOT", "NOTE", "TODO", "NEVER", "ALL", "ONLY", "DO", "IMPORTANT", "WARNING",    # capitals used for emphasis
}
FILLER = re.compile(
    r"^\W*(?:(?:great|good|excellent) question|sure|certainly|of course|absolutely|let me|"
    r"let's|i'll|i will|to understand|before we|first,? (?:let|we))\b",
    re.I,
)
NUM = r"[+\-−]?\d[\d,]*(?:\.\d+)?%?"
CHANGE_VERB = r"(?:adds?|raises?|lowers?|improves?|reduces?|increases?|decreases?|drops?|gains?|costs?|changes?|moves?|shifts?|boosts?|cuts?|lifts?)"
BARE_RANGE = re.compile(rf"\b{CHANGE_VERB}\s+(?:(?:by|about|roughly|only)\s+)?{NUM}\s*(?:to|-|–|and)\s*{NUM}", re.I)
NUMBER_PAIR = re.compile(rf"\(\s*{NUM}\s+for\s+[^,()]{{1,40}},\s*{NUM}\s+for\s+[^()]{{1,40}}\)")
ABBREVIATION = re.compile(
    r"\b(?:[A-Z]{2,}[a-z]?\d*|[a-z]{1,2}[A-Z]{2,}|[A-Z][a-z][A-Z][A-Za-z]*|F\d+(?:\.\d+)?)\b"
)
FILENAME = re.compile(r"\b[\w\-]+\.(?:py|md|json|ipynb|csv|txt|yaml|yml|sh|cfg|toml|ini|pkl|npz|zip)\b")
SNAKE = re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b")
CALL = re.compile(r"\b[a-z_][\w.]*\(\)")
BACKTICK = re.compile(r"`[^`\n]+`")
URL = re.compile(r"https?://\S+")
IRREGULAR = (r"built|made|done|given|taken|shown|known|seen|written|chosen|found|held|kept|left|lost|sent|drawn|broken|"
             r"spoken|driven|hidden|thrown|grown|begun|bought|brought|caught|taught|thought|told|sold|paid|laid|said")
NOT_PARTICIPLE = r"indeed|speed|need|feed|seed|bleed|breed|proceed|exceed|succeed|hundred|naked|wicked|sacred|kindred"
PARTICIPLE = rf"(?!(?:{NOT_PARTICIPLE})\b)(?:\w{{3,}}ed|{IRREGULAR})"
ADVERB = r"(?:(?:\w+ly|not|also|already|always|never|just|only)\s+)?"
PASSIVE = re.compile(rf"\b(?:is|are|was|were|be|been|being)\s+{ADVERB}{PARTICIPLE}\b", re.I)
PERFECT = re.compile(rf"\b(?:has|have|had)\s+{ADVERB}(?:been|{PARTICIPLE})\b", re.I)
DEFINITION_CUE = re.compile(
    r"^\W{0,3}(?:stands for|is short for|means|is the|is a|is an|are the|are a|is called|refers to|"
    r"[,—:–-]\s*(?:the|a|an|which)\b|\()",
    re.I,
)


@dataclass
class Flag:
    check: str
    line: int
    excerpt: str
    advice: str


def blank_out(text: str, pattern: re.Pattern) -> str:
    """Replace each match with spaces of the same length, so line numbers and offsets stay valid."""
    return pattern.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), text)


def strip_fences(text: str) -> str:
    return re.sub(r"```.*?```", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def to_prose(s: str) -> str:
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    s = re.sub(r"`([^`]+)`", r"\1", s)
    s = re.sub(r"[*_]{1,3}([^*_\n]+)[*_]{1,3}", r"\1", s)
    s = re.sub(r"^[ \t]{0,3}(?:#{1,6}|>)[ \t]*", "", s, flags=re.M)
    s = re.sub(r"^[ \t]*(?:[-*+]|\d+[.)])[ \t]+", "", s, flags=re.M)
    return s


def split_sentences(s: str) -> list[str]:
    parts = re.split(r"(?:(?<=[.!?])|(?<=[.!?][\"')\]”]))\s+(?=[A-Z0-9\"'(\[“])", s.strip())
    return [p.strip() for p in parts if p.strip()]


def sentences(s: str) -> list[str]:
    return [p for p in split_sentences(s) if len(p.split()) > 2]


def blocks(text: str):
    """Yield (first line number, kind, raw text) for each paragraph, list item, table or heading."""
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        if not lines[i].strip():
            i += 1
            continue
        start = i
        if lines[i].lstrip().startswith("|"):
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                i += 1
            yield start + 1, "table", "\n".join(lines[start:i])
        elif re.match(r"\s{0,3}#{1,6}\s", lines[i]):
            yield start + 1, "heading", lines[i]
            i += 1
        elif re.match(r"\s*(?:[-*+]|\d+[.)])\s+", lines[i]):
            i += 1
            while i < len(lines) and lines[i].strip() and not re.match(r"\s*(?:[-*+]|\d+[.)])\s+", lines[i]):
                i += 1
            yield start + 1, "item", "\n".join(lines[start:i])
        else:
            while i < len(lines) and lines[i].strip() and not lines[i].lstrip().startswith("|") \
                    and not re.match(r"\s*(?:[-*+]|\d+[.)])\s+", lines[i]):
                i += 1
            yield start + 1, "paragraph", "\n".join(lines[start:i])


def check_first_sentence(text: str, max_words: int) -> list[Flag]:
    for line, kind, raw in blocks(strip_fences(text)):
        if kind in ("heading", "table"):
            continue
        first = (split_sentences(to_prose(raw)) or [to_prose(raw).strip()])[0]
        out = []
        if FILLER.match(first):
            out.append(Flag("first-sentence", line, first[:70], "open with the answer, not with filler or a promise of one"))
        if len(first.split()) > max_words:
            out.append(Flag("first-sentence", line, first[:70] + " ...",
                            f"the first sentence has {len(first.split())} words; make it a short plain answer"))
        return out
    return []


def check_abbreviations(text: str, known: set[str]) -> list[Flag]:
    scan = blank_out(blank_out(blank_out(text, URL), BACKTICK), FILENAME)
    seen, flags = set(), []
    for m in ABBREVIATION.finditer(scan):
        tok = m.group(0)
        if tok in known or tok in seen:
            continue
        seen.add(tok)
        before = scan[max(0, m.start() - 100):m.start()]
        after = scan[m.end():m.end() + 100]
        if re.search(r"\b(?:table|figure|fig|section|appendix|step|part|model|task)\s*$", before, re.I):
            continue                                         # "Table A1", "Task 5"
        if before.rstrip().endswith("(") and after.lstrip().startswith(")") and len(re.findall(r"[A-Za-z]+", before)) >= 2:
            continue                                         # words (ABBR)
        paren = re.match(r"\s*\(([^()]{4,80})\)", after)
        if paren and len(re.findall(r"[A-Za-z]+", paren.group(1))) >= 2:
            continue                                         # ABBR (words)
        if DEFINITION_CUE.match(after) or re.search(r"(?:called|known as|short for|the term|the abbreviation)\s*[\"“']?$", before, re.I):
            continue
        flags.append(Flag("abbreviation", line_of(text, m.start()), tok,
                          f"{tok} is never expanded; write the full words first, or add it to --known if the reader knows it"))
    return flags


def check_bare_ranges(text: str) -> list[Flag]:
    scan = strip_fences(text)
    flags = [Flag("bare-range", line_of(scan, m.start()), m.group(0),
                  "say what changes, from what to what, for which item") for m in BARE_RANGE.finditer(scan)]
    flags += [Flag("number-pair", line_of(scan, m.start()), m.group(0),
                   "numbers in brackets do not say what they count; use a short table with a header, or name the count in words")
              for m in NUMBER_PAIR.finditer(scan)]
    return flags


def check_code_names(text: str) -> list[Flag]:
    scan = text                                            # fences included: code in the answer is code
    seen, flags = set(), []
    for label, pattern in (("backticks", BACKTICK), ("file name", FILENAME), ("snake_case", SNAKE), ("call", CALL)):
        for m in pattern.finditer(scan):
            tok = m.group(0)
            if tok.strip("`") in seen:
                continue
            seen.add(tok.strip("`"))
            flags.append(Flag("code-name", line_of(scan, m.start()), tok,
                              f"{label}: use plain words unless the reader asked about the code"))
    if "```" in text:
        flags.append(Flag("code-name", line_of(text, text.index("```")), "```", "a code block: only if the reader asked for code"))
    return flags


def check_lengths(text: str, max_sentence: int, max_paragraph: int, max_step: int = 20, max_para_sentences: int = 6) -> list[Flag]:
    """ASD-STE100 limits: 25 words in a description, 20 in a step, six sentences in a paragraph."""
    flags = []
    for line, kind, raw in blocks(strip_fences(text)):
        if kind in ("heading", "table"):
            continue
        step = kind == "item" and re.match(r"\s*\d+[.)]\s", raw) is not None
        limit = max_step if step else max_sentence
        prose = to_prose(raw)
        sents = sentences(prose)
        n = len(prose.split())
        if n > max_paragraph:
            flags.append(Flag("long-paragraph", line, prose[:60] + " ...", f"{n} words; split it or cut it"))
        elif kind == "paragraph" and len(sents) > max_para_sentences:
            flags.append(Flag("long-paragraph", line, prose[:60] + " ...",
                              f"{len(sents)} sentences; ASD-STE100 allows {max_para_sentences}"))
        for s in sents:
            k = len(s.split())
            if k > limit:
                flags.append(Flag("long-sentence", line, s[:60] + " ...",
                                  f"{k} words; the limit is {limit} for {'a step' if step else 'a description'}"))
    return flags


def check_voice_and_tense(text: str) -> list[Flag]:
    """Heuristic ASD-STE100 checks: passive voice and perfect tenses. Progressive tenses are not checked."""
    scan = to_prose(blank_out(blank_out(strip_fences(text), BACKTICK), FILENAME))     # code is not prose
    flags = []
    for check, pattern, advice in (
            ("passive", PASSIVE, "possible passive voice; say who or what acts, unless that is unknown"),
            ("perfect-tense", PERFECT, "perfect tense; use the simple past or the simple present")):
        for m in pattern.finditer(scan):
            flags.append(Flag(check, line_of(scan, m.start()), m.group(0), advice))
    return flags


def check_branches(text: str) -> list[Flag]:
    scan = to_prose(strip_fences(text))
    ifs = [s for s in re.split(r"(?<=[.!?])\s+", scan) if re.match(r"\W*If\b", s)]
    if len(ifs) >= 3:
        return [Flag("several-options", line_of(scan, scan.find(ifs[0])), ifs[0][:60],
                     f"{len(ifs)} sentences start with 'If'; recommend one action instead")]
    return []


def check_coined(text: str, labels: list[str]) -> list[Flag]:
    flags = []
    for label in labels:
        m = re.search(r"(?<!\w)" + re.escape(label), text, re.I)
        if not m:
            continue
        after = text[m.end():m.end() + 160]
        if not DEFINITION_CUE.match(after.lstrip(" \"'*_`)")) and not re.search(r"\b(?:means|is called|stands for)\b", after, re.I):
            flags.append(Flag("coined-label", line_of(text, m.start()), label,
                              "a label coined in the chat is used without its everyday meaning"))
    return flags


def run(text: str, known=(), coined=(), allow_code=False, max_first=30, max_sentence=25, max_paragraph=90, max_words=250,
        max_step=20, max_para_sentences=6):
    known_all = DEFAULT_KNOWN | set(known)
    flags = []
    flags += check_first_sentence(text, max_first)
    flags += check_abbreviations(strip_fences(text), known_all)
    flags += check_bare_ranges(text)
    if not allow_code:
        flags += check_code_names(text)
    flags += check_lengths(text, max_sentence, max_paragraph, max_step, max_para_sentences)
    flags += check_voice_and_tense(text)
    flags += check_branches(text)
    if coined:
        flags += check_coined(text, list(coined))
    words = len(to_prose(strip_fences(text)).split())
    if words > max_words:
        flags.append(Flag("long-answer", 1, f"{words} words", f"over {max_words} words; answer only what was asked"))
    flags.sort(key=lambda f: (f.line, f.check))
    return flags, words


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Mechanical checks for a draft explanation.")
    ap.add_argument("path", help="draft file, or - for standard input")
    ap.add_argument("--known", default="", help="comma-separated abbreviations the reader already knows")
    ap.add_argument("--coined", default="", help="semicolon-separated labels coined in the chat")
    ap.add_argument("--allow-code", action="store_true", help="the reader asked about code: do not flag code names")
    ap.add_argument("--no-learned", action="store_true", help="do not watch for the labels that confused the reader in earlier examples")
    ap.add_argument("--max-sentence", type=int, default=25, help="words in a descriptive sentence (ASD-STE100: 25)")
    ap.add_argument("--max-step", type=int, default=20, help="words in a numbered step (ASD-STE100: 20)")
    ap.add_argument("--max-para-sentences", type=int, default=6, help="sentences in a paragraph (ASD-STE100: 6)")
    ap.add_argument("--max-paragraph", type=int, default=90, help="words in a paragraph")
    ap.add_argument("--max-words", type=int, default=250, help="words in the whole answer")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    text = sys.stdin.read() if args.path == "-" else Path(args.path).read_text(encoding="utf-8")
    split = lambda s, sep=",": [x.strip() for x in s.split(sep) if x.strip()]
    coined = split(args.coined, ";")
    if not args.no_learned:
        try:
            import examples_lib                              # labels that confused the reader before
            coined += examples_lib.learned_labels()
        except Exception:
            pass
    flags, words = run(text, split(args.known), coined, args.allow_code,
                       max_sentence=args.max_sentence, max_paragraph=args.max_paragraph, max_words=args.max_words,
                       max_step=args.max_step, max_para_sentences=args.max_para_sentences)
    name = "stdin" if args.path == "-" else args.path.rsplit("/", 1)[-1]
    if args.json:
        print(json.dumps({"file": name, "words": words, "flags": [asdict(f) for f in flags]}, indent=2))
        return 0
    if not flags:
        print(f"CLEAN — {name} ({words} words)")
        return 0
    print(f"plain_check: {name} — {words} words, {len(flags)} flags")
    for f in flags:
        print(f"  line {f.line:<3} [{f.check}] {f.excerpt!r}: {f.advice}")
    counts = {}
    for f in flags:
        counts[f.check] = counts.get(f.check, 0) + 1
    print("  " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
