from __future__ import annotations

import unittest

import packages.state as state_exports


class StateExportsTest(unittest.TestCase):
    def test_state_root_exports_only_public_profile_contract(self) -> None:
        self.assertTrue(hasattr(state_exports, "ProfileLoader"))
        self.assertFalse(hasattr(state_exports, "resolve_runtime_state"))
        self.assertFalse(hasattr(state_exports, "build_canonical_profile_state"))


if __name__ == "__main__":
    unittest.main()
