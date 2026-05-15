from __future__ import annotations

import argparse
from pathlib import Path

from .learning_worker_runtime import DEFAULT_WORKER_IDLE_SECONDS, run_learning_worker


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m apps.learning_worker_command",
        description="Run the detached Elephant Agent background learning worker.",
    )
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--idle-seconds", type=float, default=DEFAULT_WORKER_IDLE_SECONDS)
    parser.add_argument("--once", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return run_learning_worker(
        state_dir=Path(args.state_dir),
        idle_seconds=max(1.0, float(args.idle_seconds)),
        once=bool(args.once),
    )


if __name__ == "__main__":
    raise SystemExit(main())
