"""File output utilities with overwrite protection."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

console = Console(stderr=True)


def check_overwrite(path: str | Path, *, force: bool = False) -> Path:
    """Check if a file exists and handle overwrite protection.

    Args:
        path: Output file path.
        force: If True, overwrite without prompting.

    Returns:
        Resolved Path object.

    Raises:
        typer.Abort: If user declines overwrite.
    """
    p = Path(path)
    if p.exists() and not force:
        overwrite = typer.confirm(f"File '{p}' already exists. Overwrite?")
        if not overwrite:
            raise typer.Abort()
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def write_file(path: str | Path, content: str, *, force: bool = False) -> Path:
    """Write content to a file with overwrite protection."""
    p = check_overwrite(path, force=force)
    p.write_text(content)
    console.print(f"[green]✓[/green] Written to {p}")
    return p
