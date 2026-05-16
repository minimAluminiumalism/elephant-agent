from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.contracts import ProcedureLibrary, ProcedureRecord, ProcedureStep


class CanonicalBundleContractsTest(unittest.TestCase):
    def test_procedure_library_requires_unique_procedures_and_steps(self) -> None:
        library = ProcedureLibrary(
            profile_id="profile-1",
            procedures=(
                ProcedureRecord(
                    procedure_id="procedure-1",
                    title="Recover activity state",
                    summary="Rebuild the user's active thread from durable evidence.",
                    status="draft",
                    steps=(
                        ProcedureStep(
                            step_id="step-1",
                            title="Load evidence",
                            instruction="Load recent durable evidence for the active work thread.",
                        ),
                    ),
                ),
            ),
        )

        self.assertEqual(library.profile_id, "profile-1")
        self.assertEqual(library.procedures[0].steps[0].step_id, "step-1")

        with self.assertRaises(ValueError):
            ProcedureRecord(
                procedure_id="procedure-2",
                title="Bad procedure",
                summary="Contains duplicate steps.",
                status="draft",
                steps=(
                    ProcedureStep(step_id="step-1", title="One", instruction="Do one thing."),
                    ProcedureStep(step_id="step-1", title="Two", instruction="Do two things."),
                ),
            )

        with self.assertRaises(ValueError):
            ProcedureLibrary(
                profile_id="profile-1",
                procedures=(
                    ProcedureRecord(
                        procedure_id="procedure-1",
                        title="One",
                        summary="First.",
                        status="draft",
                    ),
                    ProcedureRecord(
                        procedure_id="procedure-1",
                        title="Two",
                        summary="Second.",
                        status="draft",
                    ),
                ),
            )


if __name__ == "__main__":
    unittest.main()
