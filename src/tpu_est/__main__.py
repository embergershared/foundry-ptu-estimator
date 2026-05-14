"""Module entrypoint: `python -m tpu_est run-once`."""

from __future__ import annotations

import argparse
import sys

from tpu_est.cli import run_once
from tpu_est.config import ConfigError, load_config


def main(argv: list[str] | None = None) -> int:
    """Parse the command line, load configuration, and run the requested command."""
    parser = argparse.ArgumentParser(prog="tpu_est")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("run-once", help="Build a prompt, send it to Foundry, log telemetry, exit.")
    parser.parse_args(argv)
    try:
        config = load_config()
    except ConfigError as error:
        print(f"config error: {error}", file=sys.stderr)
        return 2
    return run_once(config)


if __name__ == "__main__":
    sys.exit(main())
