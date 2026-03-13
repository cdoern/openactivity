"""Structured error output for CLI."""

from __future__ import annotations

import json
import sys

from rich.console import Console

err_console = Console(stderr=True)


def print_error(error: str, message: str, hint: str, *, use_json: bool = False) -> None:
    """Print a structured error message to stderr.

    Args:
        error: Short error code (e.g., 'authentication_required').
        message: Human-readable explanation of what went wrong.
        hint: Actionable suggestion for the user.
        use_json: If True, output JSON error format.
    """
    if use_json:
        json.dump(
            {"error": error, "message": message, "hint": hint},
            sys.stderr,
            indent=2,
        )
        sys.stderr.write("\n")
    else:
        err_console.print(f"[bold red]Error:[/bold red] {message}")
        err_console.print(f"  {hint}")


def exit_with_error(
    error: str, message: str, hint: str, *, use_json: bool = False, code: int = 1
) -> None:
    """Print error and exit with given code."""
    print_error(error, message, hint, use_json=use_json)
    raise SystemExit(code)
