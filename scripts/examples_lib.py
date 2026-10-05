"""The example bank: passages the reader flagged as hard to follow, the corrections the reader
accepted, and what the checker makes of each.

An example is a folder, examples/NNN-slug/, holding flagged.txt, accepted.txt, optional
attempt-1.txt (a first fix that failed) and meta.json. references/examples-digest.md is built
from the bank by build_digest.py and is never edited by hand.
"""
from __future__ import annotations

import datetime
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import plain_check as pc

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "examples"              # tracked by git: seed pairs with neutral subject matter
LOCAL = ROOT / "examples-local"         # ignored by git: the reader's real pairs stay on this machine
BANKS = (PUBLIC, LOCAL)
DIGEST = ROOT / "references" / "examples-digest.md"     # generated and ignored by git
PRIVATE_TERMS = ROOT / "private-terms.txt"             # optional, ignored by git: words that must never reach examples/

TAGS = {
    "bare-number": "a number or range with no stated quantity or baseline",
    "undefined-term": "a word the reader has not met, used without its everyday meaning",
    "coined-label": "a label coined in the conversation and written as if it were standard",
    "abstract-first": "an idea or structure described in the abstract before any concrete case",
    "unlabeled-items": "list or table entries whose meaning is not stated",
    "several-actions": "several conditional actions where one recommended action was needed",
    "dense-structure": "too many ideas, sections or clauses at once",
    "code-name": "file, function or variable names where plain words were needed",
    "throat-clearing": "announcing or restating a claim instead of making it",
    "wrong-target": "answered a nearby question, not the sentence the reader flagged",
}


@dataclass
class Example:
    id: int
    slug: str
    path: Path
    meta: dict
    flagged: str
    accepted: str
    attempts: list = field(default_factory=list)


def slugify(text: str, limit: int = 40) -> str:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return "-".join(words)[:limit].strip("-") or "example"


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _folders(root: Path):
    return sorted(p for p in Path(root).glob("[0-9][0-9][0-9]-*") if p.is_dir())


def load_examples(root=None) -> list[Example]:
    """Every example in both banks, or only those under `root` when one is given."""
    out = []
    for bank in (BANKS if root is None else (Path(root),)):
        for d in _folders(bank):
            meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
            attempts = [a.read_text(encoding="utf-8").strip() for a in sorted(d.glob("attempt-*.txt"))]
            out.append(Example(int(d.name[:3]), d.name[4:], d, meta,
                               (d / "flagged.txt").read_text(encoding="utf-8").strip(),
                               (d / "accepted.txt").read_text(encoding="utf-8").strip(), attempts))
    return sorted(out, key=lambda e: e.id)


def next_id(root=None, also=()) -> int:
    """The next free number across the banks involved, so that ids stay unique."""
    banks = BANKS if root is None else (Path(root), *map(Path, also))
    return max((int(p.name[:3]) for b in banks for p in _folders(b)), default=0) + 1


def checker_view(text: str, known=(), coined=()) -> list[str]:
    """The checks that flag this text, ignoring the length note."""
    flags, _ = pc.run(text, known=list(known), coined=list(coined))
    return sorted({f.check for f in flags if f.check != "long-answer"})


def write_example(root, flagged, accepted, *, complaint, lesson, tags, signal, source="", known=(),
                  coined_flagged=(), coined_accepted=(), attempts=(), slug=None, today=None, also_check=()) -> Example:
    """Store a pair under `root`. `also_check` lists other banks whose ids and duplicates must be respected."""
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    if not flagged.strip() or not accepted.strip():
        raise ValueError("both the flagged excerpt and the accepted correction are required")
    if norm(flagged) == norm(accepted):
        raise ValueError("the flagged excerpt and the correction are identical")
    if not list(tags):
        raise ValueError("at least one tag is required; see TAGS in examples_lib.py")
    for ex in [e for bank in (root, *map(Path, also_check)) for e in load_examples(bank)]:
        if norm(ex.flagged) == norm(flagged):
            raise ValueError(f"duplicate of example {ex.id:03d} ({ex.slug})")
    n = next_id(root, also=also_check)
    d = root / f"{n:03d}-{slugify(slug or lesson or complaint)}"
    d.mkdir()
    (d / "flagged.txt").write_text(flagged.strip() + "\n", encoding="utf-8")
    (d / "accepted.txt").write_text(accepted.strip() + "\n", encoding="utf-8")
    for i, a in enumerate(attempts, 1):
        (d / f"attempt-{i}.txt").write_text(a.strip() + "\n", encoding="utf-8")
    meta = {
        "id": n,
        "date": (today or datetime.date.today()).isoformat(),
        "source": source,
        "complaint": complaint.strip(),
        "lesson": lesson.strip(),
        "tags": sorted(set(tags)),
        "signal": signal,
        "known": sorted(set(known)),
        "coined_flagged": list(coined_flagged),
        "coined_accepted": list(coined_accepted),
        "expect_flagged": checker_view(flagged, known, coined_flagged),
        "allowed_accepted": checker_view(accepted, known, coined_accepted),
    }
    (d / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return Example(n, d.name[4:], d, meta, flagged.strip(), accepted.strip(), [a.strip() for a in attempts])


PRIVATE_PATTERNS = (
    ("an email address", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")),
    ("a home folder path", re.compile(r"(?:/home/|/Users/|[A-Za-z]:\\Users\\)\w+")),
    ("a link", re.compile(r"https?://\S+")),
)


def privacy_matches(texts, terms_file=PRIVATE_TERMS) -> list[str]:
    """What in these texts should keep a pair out of the shared bank: emails, home paths, links, and any term
    listed (one per line, # for comments) in private-terms.txt."""
    blob = "\n".join(texts)
    found = [f"{label}: {m.group(0)}" for label, pattern in PRIVATE_PATTERNS for m in pattern.finditer(blob)]
    if Path(terms_file).exists():
        for line in Path(terms_file).read_text(encoding="utf-8").splitlines():
            term = line.split("#", 1)[0].strip()
            if term and re.search(r"(?<!\w)" + re.escape(term), blob, re.I):
                found.append(f"private term: {term}")
    return found


def refresh_expectations(root=None) -> int:
    """Recompute what the checker says about every example, after an intentional change to the checker."""
    changed = 0
    for ex in load_examples(root):
        m = ex.meta
        new = {"expect_flagged": checker_view(ex.flagged, m["known"], m["coined_flagged"]),
               "allowed_accepted": checker_view(ex.accepted, m["known"], m["coined_accepted"])}
        if any(m.get(k) != v for k, v in new.items()):
            m.update(new)
            (ex.path / "meta.json").write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            changed += 1
    return changed


def learned_labels(root=None) -> list[str]:
    """Labels of two or more words that confused the reader before; the checker watches for them."""
    seen, out = set(), []
    for ex in load_examples(root):
        for label in ex.meta.get("coined_flagged", []):
            if len(label.split()) >= 2 and label.lower() not in seen:
                seen.add(label.lower())
                out.append(label)
    return out


def _clip(text: str, n: int) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= n else text[:n].rsplit(" ", 1)[0] + " ..."


def build_digest(root=None, recent: int = 12) -> str:
    exs = load_examples(root)
    counts: dict[str, list[Example]] = {}
    for ex in exs:
        for t in ex.meta["tags"]:
            counts.setdefault(t, []).append(ex)
    out = ["# Examples digest",
           "",
           "Built by `scripts/build_digest.py` from `examples/` and `examples-local/`. Do not edit by hand.",
           f"{len(exs)} pairs. Full texts are in `NNN-slug/` folders under those two banks.",
           "",
           "## What failed most often",
           ""]
    for tag, items in sorted(counts.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        newest = items[-1]
        out.append(f"- **{tag}** ({len(items)}): {TAGS.get(tag, '(no description yet)')}. "
                   f"Newest fix, {newest.id:03d}: {newest.meta['lesson']}")
    out += ["", "## Pairs, newest first", ""]
    for k, ex in enumerate(reversed(exs)):
        m = ex.meta
        if k >= recent:
            out.append(f"- {ex.id:03d} [{', '.join(m['tags'])}] {m['lesson']}")
            continue
        out += [f"### {ex.id:03d} [{', '.join(m['tags'])}] {m['date']}",
                f"Reader said: {_clip(m['complaint'], 240)}",
                f"Flagged: {_clip(ex.flagged, 320)}"]
        for a in ex.attempts:
            out.append(f"Failed first fix: {_clip(a, 200)}")
        out += [f"Accepted: {_clip(ex.accepted, 420)}",
                f"Lesson: {m['lesson']}",
                f"Acceptance: {m['signal']}",
                ""]
    return "\n".join(out).rstrip() + "\n"


def write_digest(root=None, path: Path = DIGEST) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_digest(root), encoding="utf-8")
    return path
