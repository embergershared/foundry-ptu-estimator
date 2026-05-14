"""Debug-only load generator: invoke `run_once` in a loop on a fixed interval.

Not part of the production contract — the deployed Container Apps Job runs
`python -m tpu_est run-once` exactly once per replica and exits. Use this
script only for local load testing against a development Foundry deployment.

Usage (PowerShell, with .env loaded by VS Code's launch profile):
    python scripts/loop_run_once.py --interval 10 --iterations 0

Flags:
    --interval     Seconds between the START of each call (default: 10).
                   The next call fires `interval` seconds after the previous
                   one began, so a slow call shortens the gap to zero rather
                   than stacking — same behavior as a fixed-rate scheduler.
    --iterations   Number of calls to make. 0 = run forever until Ctrl+C
                   (default: 0).
"""

from __future__ import annotations

import argparse
import sys
import time

from tpu_est.cli import run_once
from tpu_est.config import ConfigError, load_config


def main(argv: list[str] | None = None) -> int:
    """Parse args, load config once, then loop run_once at a fixed interval."""
    parser = argparse.ArgumentParser(
        prog="loop_run_once",
        description="Debug load generator that calls run_once in a loop.",
    )
    parser.add_argument("--interval", type=float, default=10.0)
    parser.add_argument("--iterations", type=int, default=0)
    args = parser.parse_args(argv)

    try:
        config = load_config()
    except ConfigError as error:
        print(f"config error: {error}", file=sys.stderr)
        return 2

    iteration = 0
    failures = 0
    try:
        while args.iterations == 0 or iteration < args.iterations:
            iteration += 1
            started_at = time.monotonic()
            print(f"\n=== iteration {iteration} ===", file=sys.stderr, flush=True)
            exit_code = run_once(config)
            if exit_code != 0:
                failures += 1
            elapsed = time.monotonic() - started_at
            sleep_for = max(0.0, args.interval - elapsed)
            if args.iterations == 0 or iteration < args.iterations:
                time.sleep(sleep_for)
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)

    print(
        f"\nloop done: iterations={iteration} failures={failures}",
        file=sys.stderr,
    )
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
