from __future__ import annotations

import unittest

import packages.state as state_exports
from packages.state import resolve_runtime_state


class StateExportsTest(unittest.TestCase):
    def test_resolve_runtime_state_is_available_from_public_exports(self) -> None:
        self.assertTrue(hasattr(state_exports, "resolve_runtime_state"))
        self.assertIs(resolve_runtime_state, state_exports.resolve_runtime_state)


if __name__ == "__main__":
    unittest.main()
