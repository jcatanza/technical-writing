#!/usr/bin/env python3
"""Record a passage the reader flagged as hard to follow and the correction the reader accepted.

Run it once the reader has accepted the correction. It writes NNN-slug/ under examples-local/ (which git
ignores, so the reader's real pairs stay on this machine) or, with --public, under examples/ (which git
tracks). It notes what the checker makes of both texts and rebuilds references/examples-digest.md. It never commits.

    add_example.py --flagged flagged.txt --accepted accepted.txt \\
        --complaint "what the reader said" --lesson "what the correction did differently" \\
        --tags undefined-term,coined-label --signal "explicit: 'got it'" \\
        [--attempt first_fix.txt] [--known SNR,dBFS] [--coined-flagged "old system"] [--coined-accepted "old system"]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import examples_lib as ex


def read(path: str) -> str:
    return sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")


def split(s: str, sep: str = ",") -> list[str]:
    return [x.strip() for x in s.split(sep) if x.strip()]


def bank_for(public: bool, root) -> Path:
    """Where a new pair goes: the folder given with --root, else examples/ with --public, else examples-local/."""
    if root:
        return Path(root)
    return ex.PUBLIC if public else ex.LOCAL


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--flagged", required=True, help="file holding the flagged excerpt, verbatim ('-' for standard input)")
    ap.add_argument("--accepted", required=True, help="file holding the accepted correction, verbatim")
    ap.add_argument("--attempt", action="append", default=[], help="file holding a first fix that failed (repeatable)")
    ap.add_argument("--complaint", required=True, help="the part of the reader's words that says what was wrong; leave out venting")
    ap.add_argument("--keep-wording", action="store_true", help="store a complaint even though it shows signs of venting")
    ap.add_argument("--lesson", required=True, help="one line: what the correction did differently")
    ap.add_argument("--tags", required=True, help="comma-separated failure types; see TAGS in examples_lib.py")
    ap.add_argument("--signal", required=True, help="how the acceptance showed, such as \"explicit: 'got it'\" or 'implicit: asked a follow-up'")
    ap.add_argument("--source", default="", help="where it happened, such as a project and date")
    ap.add_argument("--known", default="", help="comma-separated abbreviations the reader already knew")
    ap.add_argument("--coined-flagged", default="", help="semicolon-separated labels coined in the flagged text")
    ap.add_argument("--coined-accepted", default="", help="semicolon-separated labels coined in the correction")
    ap.add_argument("--slug", default=None)
    ap.add_argument("--public", action="store_true",
                    help="store the pair in examples/, which git tracks; use it only after checking that the pair holds no private material")
    ap.add_argument("--allow-matches", action="store_true",
                    help="with --public, store the pair even though the privacy scan found something")
    ap.add_argument("--root", default=None, help="examples folder (the tests use a temporary one)")
    ap.add_argument("--digest", default=None, help="digest path (the tests use a temporary one)")
    ap.add_argument("--no-digest", action="store_true")
    args = ap.parse_args(argv)

    root = bank_for(args.public, args.root)
    also = [] if args.root else [b for b in ex.BANKS if b != root]
    tags = split(args.tags)
    vent = ex.venting_markers(args.complaint)
    if vent and not args.keep_wording:
        print("not added: the complaint shows signs of venting: " + ", ".join(repr(v) for v in vent), file=sys.stderr)
        print("  keep only the words that say what was wrong, or pass --keep-wording if the words carry real guidance", file=sys.stderr)
        return 2
    flagged, accepted = read(args.flagged), read(args.accepted)          # read once: standard input can be read only once
    attempts = [read(a) for a in args.attempt]
    if args.public and not args.allow_matches:
        matches = ex.privacy_matches([flagged, accepted, args.complaint, args.source, *attempts])
        if matches:
            print("not added: the privacy scan found text that should not go into the shared bank:", file=sys.stderr)
            for m in matches:
                print(f"  {m}", file=sys.stderr)
            print("  rewrite the pair without it, or pass --allow-matches after you check each match", file=sys.stderr)
            return 2
    try:
        added = ex.write_example(
            root, flagged, accepted,
            complaint=args.complaint, lesson=args.lesson, tags=tags, signal=args.signal, source=args.source,
            known=split(args.known), coined_flagged=split(args.coined_flagged, ";"),
            coined_accepted=split(args.coined_accepted, ";"), attempts=attempts, slug=args.slug,
            also_check=also)
    except ValueError as err:
        print(f"not added: {err}", file=sys.stderr)
        return 2
    if not args.no_digest:
        digest = Path(args.digest) if args.digest else (Path(args.root).parent / "examples-digest.md" if args.root else ex.DIGEST)
        ex.write_digest(root if args.root else None, digest)
    print(f"added {added.id:03d}-{added.slug}")
    print(f"  checker on the flagged excerpt: {added.meta['expect_flagged'] or 'no flags'}")
    print(f"  checker on the accepted correction: {added.meta['allowed_accepted'] or 'no flags'}")
    for t in tags:
        if t not in ex.TAGS:
            print(f"  note: the tag '{t}' has no description in TAGS (examples_lib.py); add one if it will recur")
    where = "a custom folder" if args.root else "examples/ (tracked by git)" if args.public else "examples-local/ (stays on this machine)"
    print(f"  stored in {where}")
    print("  not committed: run the tests, then commit when the reader asks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
