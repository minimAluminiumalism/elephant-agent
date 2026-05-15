"""Context unit test package."""

from __future__ import annotations

import unittest

from . import test_context_runtime


def load_tests(
    loader: unittest.TestLoader,
    tests: unittest.TestSuite,
    pattern: str | None,
) -> unittest.TestSuite:
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromModule(test_context_runtime))
    return suite
