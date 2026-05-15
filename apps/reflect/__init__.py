"""Feature-composable reflect agent system.

A reflect agent exercises one or more *features* (atomic capabilities) selected
by the trigger that created the job or by the operator via CLI flags.
"""

from .runner import run_reflect_agent

__all__ = ["run_reflect_agent"]
