from __future__ import annotations

import argparse
import sys

from easy_scsmodmanager import __app_name__, __version__
from easy_scsmodmanager.cli import scan as scan_cmd


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="easy-scsmodmanager",
        description=f"{__app_name__} - mod and profile manager for ETS2/ATS",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command")
    scan_cmd.add_parser(subparsers)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        # No subcommand -> launch the GUI (Phase 0 behaviour).
        from easy_scsmodmanager.app import run as run_app

        return run_app(sys.argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
