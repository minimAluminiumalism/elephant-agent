from __future__ import annotations

import unittest
from pathlib import Path


def load_tests(loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str) -> unittest.TestSuite:
    package_dir = Path(__file__).resolve().parent
    return loader.discover(str(package_dir), pattern="test_*.py", top_level_dir=str(package_dir.parents[3]))
