"""Make sim/ and each testbench's own directory importable.

cocotb loads test_module by name from PYTHONPATH, so every directory holding a
testbench needs to be on it before runner.test() fires.
"""

import os
import sys
from pathlib import Path

SIM_DIR = Path(__file__).resolve().parent


def pytest_configure(config):
    paths = [str(SIM_DIR)]
    for child in SIM_DIR.rglob("test_*.py"):
        paths.append(str(child.parent))

    for p in paths:
        if p not in sys.path:
            sys.path.insert(0, p)

    existing = os.environ.get("PYTHONPATH", "")
    merged = os.pathsep.join(dict.fromkeys([*paths, *existing.split(os.pathsep)]))
    os.environ["PYTHONPATH"] = merged.strip(os.pathsep)
