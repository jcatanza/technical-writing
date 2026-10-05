import os
import subprocess
import sys
from pathlib import Path

import pytest

import examples_lib as ex

EXAMPLES = ex.load_examples()
LABEL = lambda e: f"{e.id:03d}-{e.slug}"


def test_the_bank_holds_the_seed_pairs():
    assert len(EXAMPLES) >= 11


@pytest.mark.parametrize("e", EXAMPLES, ids=LABEL)
def test_flagged_text_still_gets_its_recorded_flags(e):
    got = ex.checker_view(e.flagged, e.meta["known"], e.meta["coined_flagged"])
    assert set(e.meta["expect_flagged"]) <= set(got)


@pytest.mark.parametrize("e", EXAMPLES, ids=LABEL)
def test_accepted_text_raises_no_new_flags(e):
    got = ex.checker_view(e.accepted, e.meta["known"], e.meta["coined_accepted"])
    assert set(got) <= set(e.meta["allowed_accepted"]), \
        "a correction the reader accepted is now flagged: fix the checker, or run build_digest.py --refresh if the change is intended"


def test_every_example_is_complete_and_numbered_in_increasing_order():
    keys = ("id", "date", "source", "complaint", "lesson", "tags", "signal", "known", "coined_flagged",
            "coined_accepted", "expect_flagged", "allowed_accepted")
    for e in EXAMPLES:
        assert all(k in e.meta for k in keys), e.id
        assert e.meta["tags"] and e.meta["lesson"] and e.flagged and e.accepted
        assert e.meta["id"] == e.id
    ids = [e.id for e in EXAMPLES]
    assert ids == sorted(set(ids))                  # a removed pair leaves a gap, which is fine


def test_the_digest_lists_every_example(tmp_path):
    text = ex.write_digest(None, tmp_path / "digest.md").read_text(encoding="utf-8")
    assert "## What failed most often" in text
    assert all(f"{e.id:03d}" in text for e in EXAMPLES)


def test_the_digest_builder_runs_from_the_command_line():
    script = Path(ex.__file__).with_name("build_digest.py")
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    assert subprocess.run([sys.executable, str(script)], capture_output=True, env=env).returncode == 0
    assert subprocess.run([sys.executable, str(script), "--check"], capture_output=True, env=env).returncode == 0


def test_real_pairs_and_the_generated_digest_stay_out_of_git():
    ignored = (ex.ROOT / ".gitignore").read_text(encoding="utf-8").split()
    assert {"examples-local/", "references/examples-digest.md", "private-terms.txt"} <= set(ignored)


def test_the_shared_bank_is_numbered_before_the_local_bank_adds_to_it():
    shared = [e.id for e in ex.load_examples(ex.PUBLIC)]
    assert shared == sorted(set(shared)) and len(shared) >= 11


def test_learned_labels_have_two_or_more_words():
    labels = ex.learned_labels()
    assert "old system" in labels and "weighted total" in labels
    assert all(len(label.split()) >= 2 for label in labels)
