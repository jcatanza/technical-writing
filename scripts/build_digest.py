#!/usr/bin/env python3
"""Rebuild references/examples-digest.md from examples/ and examples-local/.

    build_digest.py              rewrite the digest
    build_digest.py --check      exit 1 if the digest on disk is out of date
    build_digest.py --refresh    first recompute what the checker says about every example
                                 (use after an intentional change to plain_check.py)
"""
from __future__ import annotations

import argparse
import sys

import examples_lib as ex


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args(argv)
    if args.refresh:
        print(f"refreshed {ex.refresh_expectations()} examples")
    text = ex.build_digest()
    if args.check:
        current = ex.DIGEST.read_text(encoding="utf-8") if ex.DIGEST.exists() else ""
        if current != text:
            print("references/examples-digest.md is out of date: run scripts/build_digest.py", file=sys.stderr)
            return 1
        print("digest is current")
        return 0
    path = ex.write_digest()
    print(f"wrote {path} ({len(ex.load_examples())} pairs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
