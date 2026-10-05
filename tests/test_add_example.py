import json
import subprocess
import sys
from pathlib import Path

import examples_lib as ex

SCRIPT = Path(ex.__file__).with_name("add_example.py")


def add(tmp, flagged, accepted, *extra):
    (tmp / "f.txt").write_text(flagged)
    (tmp / "a.txt").write_text(accepted)
    cmd = [sys.executable, str(SCRIPT), "--flagged", str(tmp / "f.txt"), "--accepted", str(tmp / "a.txt"),
           "--complaint", "unclear", "--lesson", "Say what it counts.", "--tags", "bare-number",
           "--signal", "explicit: got it", "--root", str(tmp / "examples"), "--digest", str(tmp / "digest.md"), *extra]
    return subprocess.run(cmd, capture_output=True, text=True)


def test_a_pair_is_stored_and_the_digest_rebuilt(tmp_path):
    out = add(tmp_path, "Smoothing adds 0.09 to 0.12.", "Applying smoothing raises mean accuracy from 0.412 to 0.497.")
    assert out.returncode == 0, out.stderr
    folder = tmp_path / "examples" / "001-say-what-it-counts"
    assert (folder / "flagged.txt").exists() and (folder / "accepted.txt").exists()
    meta = json.loads((folder / "meta.json").read_text())
    assert meta["tags"] == ["bare-number"] and "bare-range" in meta["expect_flagged"]
    assert meta["allowed_accepted"] == []
    assert "Say what it counts." in (tmp_path / "digest.md").read_text()
    assert "not committed" in out.stdout


def test_ids_increase_and_duplicates_are_refused(tmp_path):
    assert add(tmp_path, "First flagged text here.", "First fixed text here.").returncode == 0
    second = add(tmp_path, "Second flagged text here.", "Second fixed text here.", "--slug", "second")
    assert second.returncode == 0 and (tmp_path / "examples" / "002-second").exists()
    dup = add(tmp_path, "first   FLAGGED text here.", "Another fix.")
    assert dup.returncode == 2 and "duplicate" in dup.stderr


def test_identical_texts_are_refused(tmp_path):
    assert add(tmp_path, "Same text.", "Same text.").returncode == 2


def test_a_pair_without_a_tag_is_refused(tmp_path):
    out = add(tmp_path, "Flagged text.", "Fixed text.", "--tags", " , ")
    assert out.returncode == 2 and "tag" in out.stderr


def test_a_custom_root_never_overwrites_the_real_digest(tmp_path):
    before = ex.DIGEST.read_text(encoding="utf-8") if ex.DIGEST.exists() else None     # a fresh clone has none
    (tmp_path / "f.txt").write_text("Some flagged text here.")
    (tmp_path / "a.txt").write_text("Some fixed text here.")
    out = subprocess.run([sys.executable, str(SCRIPT), "--flagged", str(tmp_path / "f.txt"), "--accepted", str(tmp_path / "a.txt"),
                          "--complaint", "c", "--lesson", "l", "--tags", "bare-number", "--signal", "s",
                          "--root", str(tmp_path / "examples")], capture_output=True, text=True)
    assert out.returncode == 0
    assert (ex.DIGEST.read_text(encoding="utf-8") if ex.DIGEST.exists() else None) == before
    assert (tmp_path / "examples-digest.md").exists()


def test_a_failed_first_fix_is_kept(tmp_path):
    (tmp_path / "att.txt").write_text("A first fix that failed.")
    out = add(tmp_path, "Flagged text.", "Accepted fix.", "--attempt", str(tmp_path / "att.txt"))
    assert out.returncode == 0
    assert (tmp_path / "examples" / "001-say-what-it-counts" / "attempt-1.txt").exists()
    assert "Failed first fix" in (tmp_path / "digest.md").read_text()


def test_an_unknown_tag_gets_a_note(tmp_path):
    out = add(tmp_path, "Flagged.", "Fixed.", "--tags", "brand-new-failure")
    assert out.returncode == 0 and "brand-new-failure" in out.stdout


def test_a_new_pair_goes_to_the_local_bank_unless_it_is_made_public(tmp_path):
    import add_example
    assert add_example.bank_for(False, None) == ex.LOCAL
    assert add_example.bank_for(True, None) == ex.PUBLIC
    assert add_example.bank_for(True, str(tmp_path)) == tmp_path


def test_ids_and_duplicates_are_checked_across_banks(tmp_path):
    shared, local = tmp_path / "shared", tmp_path / "local"
    ex.write_example(shared, "Flagged one.", "Fixed one.", complaint="c", lesson="l", tags=["bare-number"], signal="s")
    second = ex.write_example(local, "Flagged two.", "Fixed two.", complaint="c", lesson="l", tags=["bare-number"],
                              signal="s", also_check=[shared])
    assert second.id == 2
    try:
        ex.write_example(local, "flagged   ONE.", "Another.", complaint="c", lesson="l", tags=["bare-number"],
                         signal="s", also_check=[shared])
    except ValueError as err:
        assert "duplicate" in str(err)
    else:
        raise AssertionError("a duplicate across banks was accepted")


def test_venting_is_detected():
    assert ex.venting_markers("This is so hard to understand!!! I am so frustrated.") == ["!!!", "frustrat"]
    assert ex.venting_markers("What is a group??") == ["??"]
    assert ex.venting_markers("This sentence does not make sense.") == []


def test_cleaning_strips_the_venting_and_keeps_the_core():
    cleaned, removed = ex.clean_complaint("This is so hard to understand!!! I am so frustrated. Please give a simple example.")
    assert cleaned == "This is so hard to understand. Please give a simple example."
    assert removed == ["I am so frustrated."]
    assert ex.clean_complaint("what is a group??") == ("what is a group?", [])
    cleaned, removed = ex.clean_complaint("Please explain the table. This is not a game!!!")
    assert cleaned == "Please explain the table." and removed == ["This is not a game!!!"]
    assert ex.clean_complaint("Please explain this table!!!") == ("Please explain this table.", [])
    assert ex.clean_complaint("THIS IS SO HARD TO UNDERSTAND!!! Define the term.") == ("This is so hard to understand. Define the term.", [])
    assert ex.clean_complaint("It is very unclear!") == ("It is very unclear.", [])
    cleaned, removed = ex.clean_complaint("It is so frustrating when you do this!!!")
    assert cleaned == ex.DEFAULT_COMPLAINT and removed


def test_a_complaint_that_vents_is_stored_cleaned_and_the_removal_is_reported(tmp_path):
    out = add(tmp_path, "Flagged text.", "Fixed text.", "--complaint", "So hard to understand!!! I am so annoyed.")
    assert out.returncode == 0 and "removed from the complaint" in out.stdout
    meta = json.loads(next((tmp_path / "examples").glob("*/meta.json")).read_text())
    assert meta["complaint"] == "So hard to understand."


def test_keep_wording_stores_the_complaint_as_written(tmp_path):
    out = add(tmp_path, "Flagged text.", "Fixed text.", "--complaint", "So hard to understand!!!", "--keep-wording")
    assert out.returncode == 0
    meta = json.loads(next((tmp_path / "examples").glob("*/meta.json")).read_text())
    assert meta["complaint"] == "So hard to understand!!!"


def test_no_stored_complaint_vents():
    for e in ex.load_examples(ex.PUBLIC):
        assert ex.venting_markers(e.meta["complaint"]) == [], (e.id, e.meta["complaint"][:60])


def test_the_privacy_scan_finds_emails_paths_links_and_listed_terms(tmp_path):
    terms = tmp_path / "private-terms.txt"
    terms.write_text("# comment\nsecret project\n")
    found = ex.privacy_matches(["Mail me at a.b@example.org", "see /home/someone/file", "https://example.org/x",
                                "The Secret Project failed"], terms_file=terms)
    kinds = " ".join(found)
    assert "email address" in kinds and "home folder path" in kinds and "a link" in kinds and "private term: secret project" in kinds
    assert ex.privacy_matches(["A neutral sentence about sensors."], terms_file=terms) == []


def test_a_public_pair_with_private_text_is_refused_unless_allowed(tmp_path):
    out = add(tmp_path, "See /home/someone/notes for the flagged text.", "A fixed text.", "--public")
    assert out.returncode == 2 and "privacy scan" in out.stderr and "home folder path" in out.stderr
    assert not (ex.PUBLIC / "012-say-what-it-counts").exists()


def test_only_labels_of_two_or_more_words_are_learned(tmp_path):
    root = tmp_path / "examples"
    ex.write_example(root, "The old system stops it.", "The existing model stops it.", complaint="c", lesson="l",
                     tags=["coined-label"], signal="s", coined_flagged=["old system", "Support"])
    assert ex.learned_labels(root) == ["old system"]


def test_refresh_recomputes_what_the_checker_says(tmp_path):
    root = tmp_path / "examples"
    e = ex.write_example(root, "Smoothing adds 0.09 to 0.12.", "It raises accuracy from 0.1 to 0.2.", complaint="c", lesson="l",
                         tags=["bare-number"], signal="s")
    path = e.path / "meta.json"
    meta = json.loads(path.read_text())
    meta["expect_flagged"] = []
    path.write_text(json.dumps(meta))
    assert ex.refresh_expectations(root) == 1
    assert "bare-range" in json.loads(path.read_text())["expect_flagged"]
