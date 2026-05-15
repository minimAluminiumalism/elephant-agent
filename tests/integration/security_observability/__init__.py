from __future__ import annotations

import importlib
import unittest


def load_tests(
    loader: unittest.TestLoader,
    standard_tests: unittest.TestSuite,
    pattern: str | None,
) -> unittest.TestSuite:
    suite = unittest.TestSuite()
    suite.addTests(standard_tests)
    module = importlib.import_module(".test_security_observability", __name__)
    suite.addTests(loader.loadTestsFromModule(module))
    return suite
