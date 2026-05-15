"""Background learning agents — shim that delegates to apps.reflect."""

from apps.reflect.runner import ReflectResult, run_reflect_agent


def run_background_learning_agent(runtime, job):
    """Backward-compatible entry point. Delegates to the reflect system."""
    result = run_reflect_agent(runtime, job)
    # Return a duck-typed object matching the old BackgroundLearningAgentResult shape
    return result


__all__ = ["run_background_learning_agent"]
