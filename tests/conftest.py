import sys
from pathlib import Path

sys.dont_write_bytecode = True                      # leave no __pycache__ folders behind
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
