import re
from pathlib import Path

import examples_lib as ex

ROOT = Path(ex.__file__).resolve().parent.parent
TEXT = (ROOT / "SKILL.md").read_text(encoding="utf-8")


def header():
    lines = TEXT.split("\n")
    assert lines[0] == "---"
    end = lines.index("---", 1)
    fields = {}
    for line in lines[1:end]:
        key, _, value = line.partition(": ")
        fields[key] = value
    return fields


def test_the_header_has_exactly_a_name_and_a_description():
    fields = header()
    assert set(fields) == {"name", "description"}
    assert fields["name"] == "technical-writing"
    assert 0 < len(fields["description"]) <= 1024


def test_the_description_is_safe_for_strict_header_parsers():
    description = header()["description"]
    assert ": " not in description                  # a colon and a space starts a mapping in strict YAML
    assert not description.startswith(("'", '"'))   # quotes would show up literally in simple parsers


def test_every_path_the_instructions_name_exists():
    named = set(re.findall(r"(?:scripts|references|examples)/[\w./-]+", TEXT))
    assert named, "SKILL.md names no files"
    generated = {"references/examples-digest.md", "examples-local", "examples-local/"}   # built or created on first use
    for rel in named - generated:
        base = rel.split("NNN")[0] if "NNN" in rel else rel
        assert (ROOT / base.rstrip("/")).exists(), rel


def test_the_repository_carries_the_mit_license():
    text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert text.startswith("MIT License") and "Permission is hereby granted, free of charge" in text


def test_the_tag_list_the_instructions_point_to_exists():
    assert "TAGS" in TEXT and ex.TAGS
