"""Public inventory of the shared runtime contract surface.

Keep this list stable so module teams can agree on the names they are building
against without reaching into implementation details.
"""

CONTRACT_SURFACES = (
    "PersonalModel",
    "State",
    "Episode",
    "Loop",
    "Step",
    "Record",
    "Grounding",
    "MemoryEntry",
    "ReflectionProposal",
    "SemanticIndexEntry",
    "Observation",
    "Fact",
    "OpenQuestion",
    "GenerationProviderConfig",
    "ActiveProviderSelection",
)
