"""The README banner must stay reproducible from the files in docs/banner/."""
import hashlib
import importlib.util
import struct
import xml.dom.minidom
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
BANNER = ROOT / "docs" / "banner"


@pytest.fixture(scope="module")
def generator():
    spec = importlib.util.spec_from_file_location("make_banner", BANNER / "make_banner.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_two_builds_draw_the_same_picture(generator):
    assert generator.build() == generator.build()


def test_the_drawing_is_well_formed_xml(generator):
    xml.dom.minidom.parseString(generator.build())


def test_the_sparks_need_students_to_float_above(generator):
    generator.HEADS.clear()
    with pytest.raises(RuntimeError):
        generator.place_sparks()


def test_banner_png_was_rendered_from_the_drawing_the_generator_makes_now(generator):
    recorded = (BANNER / "banner.sha256").read_text(encoding="utf-8").strip()
    current = hashlib.sha256(generator.build().encode("utf-8")).hexdigest()
    assert recorded == current, "the drawing changed since banner.png was rendered: run make_banner.py, then render_png.py"


def test_banner_png_is_the_size_github_expects():
    data = (BANNER / "banner.png").read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert struct.unpack(">II", data[16:24]) == (1280, 640)
    assert len(data) < 1_000_000                        # GitHub's limit for a social preview image


def test_each_font_ships_with_its_license():
    fonts = sorted((BANNER / "fonts").glob("*.ttf"))
    assert fonts
    for font in fonts:
        family = font.stem.split("-")[0]
        text = (BANNER / "fonts" / f"OFL-{family}.txt").read_text(encoding="utf-8")
        assert "SIL OPEN FONT LICENSE Version 1.1" in text


def test_the_readme_shows_the_banner():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "](docs/banner/banner.png)" in readme
