import json
import subprocess
import sys
from pathlib import Path

import plain_check as pc

SCRIPT = Path(pc.__file__)


def checks(text, **kw):
    flags, _ = pc.run(text, **kw)
    return {f.check for f in flags}


def test_filler_and_long_first_sentences():
    assert "first-sentence" in checks("Great question. The filter removes duplicate readings.")
    assert "first-sentence" in checks("Let me explain how readings are removed in the code.")
    assert "first-sentence" in checks(" ".join(["word"] * 35) + ".")
    assert "first-sentence" not in checks("The filter removes duplicate readings.")


def test_first_sentence_ignores_code_fences_and_list_markers():
    assert "first-sentence" not in checks("```\nGreat question\n```\n\nThe filter removes duplicate readings.")
    assert "first-sentence" in checks("1. Great question. The filter removes duplicate readings.")


def test_capitals_used_for_emphasis_are_not_abbreviations():
    assert "abbreviation" not in checks("This is NOT optional. NOTE the order.")


def test_a_coined_label_is_not_matched_inside_a_longer_word():
    assert "coined-label" not in checks("The bold systems differ.", coined=["old system"])
    assert "coined-label" in checks("The old system stops it.", coined=["old system"])


def test_abbreviations_must_be_expanded_or_known():
    assert "abbreviation" in checks("SNR drops at night.")
    assert "abbreviation" in checks("The dBFS reading rises.")
    assert "abbreviation" in checks("PhD students read it.")
    assert "abbreviation" in checks("F1 is 0.5.")
    assert "abbreviation" not in checks("Signal-to-noise ratio (SNR) drops at night.")
    assert "abbreviation" not in checks("SNR (signal-to-noise ratio) drops at night.")
    assert "abbreviation" not in checks("SNR stands for signal-to-noise ratio.")
    assert "abbreviation" not in checks("SNR drops at night.", known=["SNR"])
    assert "abbreviation" not in checks("AI is useful.")
    assert "abbreviation" not in checks("See Table A1 and Task 5.")


def test_number_ranges_and_pairs_need_a_baseline():
    assert "bare-range" in checks("Smoothing adds 0.09 to 0.12 here.")
    assert "bare-range" not in checks("It raises sensor A from 0.412 to 0.497.")
    assert "number-pair" in checks("Readings inside the range (1,722 for sensor A, 1,855 for sensor B) match.")


def test_code_names_are_flagged_unless_allowed():
    for text in ("Open `report.py`.", "The row_codes list.", "See report.py.", "Call match().", "Use `x`."):
        assert "code-name" in checks(text), text
    assert "code-name" not in checks("The list of true labels.")
    assert "code-name" not in checks("See report.py.", allow_code=True)


def test_long_sentences_and_paragraphs():
    assert "long-sentence" in checks("Short one here. " + " ".join(["word"] * 35) + ".")
    assert "long-paragraph" in checks(" ".join(["Short sentence here."] * 35))
    assert "long-paragraph" not in checks("Short sentence here.\n\n" * 3)


def test_description_and_step_length_limits():
    twenty_six = " ".join(["word"] * 26) + "."
    twenty_two = " ".join(["word"] * 22) + "."
    assert "long-sentence" in checks("Intro here. " + twenty_six)
    assert "long-sentence" not in checks("Intro here. " + twenty_two)
    assert "long-sentence" in checks("1. " + twenty_two)             # a numbered step may have 20 words
    assert "long-sentence" not in checks("- " + twenty_two)          # a bullet is not a numbered step


def test_more_than_six_sentences_make_a_long_paragraph():
    assert "long-paragraph" in checks(" ".join(["This is short."] * 7))
    assert "long-paragraph" not in checks(" ".join(["This is short."] * 6))


def test_passive_voice_and_perfect_tense_are_flagged():
    assert "passive" in checks("The file is saved by the script.")
    assert "passive" in checks("The readings were sent to the logger.")
    assert "passive" not in checks("The script saves the file.")
    assert "passive" not in checks("The valve is open and the speed is indeed high.")
    assert "perfect-tense" in checks("The script has saved the file.")
    assert "perfect-tense" in checks("It had been done.")
    assert "perfect-tense" not in checks("Each folder has `flagged.txt` and saved.txt.")      # file names are not verbs
    assert "perfect-tense" not in checks("The script saves the file.")


def test_a_period_inside_closing_quotes_ends_the_sentence():
    text = ('Intro sentence here. Every row needs a "true answer." For a correct alert the true answer is the zone number, '
            "such as zero for the north bed and one for the south bed.")
    assert "long-sentence" not in checks(text)


def test_three_if_sentences_mean_several_options():
    assert "several-options" in checks("If a, do x. If b, do y. If c, do z.")
    assert "several-options" not in checks("If a, do x. Otherwise do y.")


def test_coined_labels_need_a_definition_at_first_use():
    assert "coined-label" in checks("The weighted total is 9 here.", coined=["weighted total"])
    assert "coined-label" not in checks("The weighted total is the sum of the weights.", coined=["weighted total"])
    assert "coined-label" not in checks('"Old system" means the model already in use.', coined=["old system"])
    assert "coined-label" not in checks("No such words here.", coined=["weighted total"])


def test_tables_and_code_fences_are_not_prose():
    table = "| a | b |\n|---|---|\n| " + " ".join(["word"] * 40) + " | x |\n"
    assert "long-sentence" not in checks("Answer.\n\n" + table)
    assert "abbreviation" not in checks("Answer.\n\n```\nNMS = 1\n```\n")


def test_long_answers_get_a_note():
    assert "long-answer" in checks("Short sentence here. " * 90)
    assert "long-answer" not in checks("Short sentence here. " * 30)


def test_command_line(tmp_path):
    bad = tmp_path / "bad.md"
    bad.write_text("SNR adds 0.09 to 0.12.\n")
    out = subprocess.run([sys.executable, str(SCRIPT), str(bad), "--no-learned"], capture_output=True, text=True)
    assert out.returncode == 0 and "bare-range" in out.stdout and "abbreviation" in out.stdout
    good = tmp_path / "good.md"
    good.write_text("The filter removes duplicate readings.\n")
    out = subprocess.run([sys.executable, str(SCRIPT), str(good), "--no-learned"], capture_output=True, text=True)
    assert out.stdout.startswith("CLEAN")
    js = subprocess.run([sys.executable, str(SCRIPT), "-", "--json", "--no-learned"], input="SNR drops at night.\n",
                        capture_output=True, text=True)
    assert json.loads(js.stdout)["flags"][0]["check"] == "abbreviation"
