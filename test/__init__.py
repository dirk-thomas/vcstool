import os
from pathlib import Path
import sys

# -- SETUP PYTHON SEARCH PATH:
HERE = Path(__file__).parent.resolve()
TOPDIR = Path(HERE/"..").resolve()
sys.path.insert(0, str(TOPDIR))

# -- SETUP PYTHON SEARCH PATH: For subprocess(es)
os.environ['PYTHONPATH'] = str(TOPDIR)
