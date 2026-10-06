"""Render banner.svg to banner.png (1280 x 640 pixels) with headless Google Chrome or Chromium.

Run make_banner.py first. This script also records the SHA-256 checksum of the drawing in banner.sha256. A test compares
that checksum with the drawing that make_banner.py writes now, so it fails when the drawing changes and the PNG is not
rendered again.

Chrome runs with its sandbox on. If Chrome refuses to start because you are root or inside a container, set the
environment variable BANNER_NO_SANDBOX=1 and run the script again."""
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SVG, PNG, CHECKSUM = HERE / "banner.svg", HERE / "banner.png", HERE / "banner.sha256"
BROWSERS = ("google-chrome", "chromium", "chromium-browser", "chrome")


def main():
    if not SVG.exists():
        sys.exit("banner.svg is missing. Run make_banner.py first.")
    browser = next((path for path in map(shutil.which, BROWSERS) if path), None)
    if browser is None:
        sys.exit("This script needs Google Chrome or Chromium on the PATH.")
    flags = ["--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1", "--window-size=1280,640"]
    if os.environ.get("BANNER_NO_SANDBOX"):
        flags.append("--no-sandbox")
    # Remove the old files first, so that a failed render cannot leave an old picture next to a new checksum.
    PNG.unlink(missing_ok=True)
    CHECKSUM.unlink(missing_ok=True)
    try:
        subprocess.run([browser, *flags, f"--screenshot={PNG}", SVG.as_uri()], check=True, capture_output=True)
    except subprocess.CalledProcessError as error:
        sys.exit(f"Chrome failed with exit code {error.returncode}:\n{error.stderr.decode(errors='replace')}")
    if not PNG.exists() or PNG.stat().st_size == 0:
        sys.exit("Chrome ran but wrote no banner.png.")
    CHECKSUM.write_text(hashlib.sha256(SVG.read_bytes()).hexdigest() + "\n", encoding="utf-8")
    print("wrote", PNG, "and", CHECKSUM)


if __name__ == "__main__":
    main()
