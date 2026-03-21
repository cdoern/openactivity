"""Rich table output formatting."""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.table import Table

console = Console()
err_console = Console(stderr=True)


def render_table(
    columns: list[tuple[str, str]],
    rows: list[dict[str, Any]],
    title: str | None = None,
    footer: str | None = None,
) -> None:
    """Render a Rich table to stdout.

    Args:
        columns: List of (key, header_label) tuples.
        rows: List of dicts where keys match column keys.
        title: Optional table title.
        footer: Optional footer text printed after table.
    """
    table = Table(title=title, show_header=True, header_style="bold")
    for _key, label in columns:
        table.add_column(label)

    for row in rows:
        table.add_row(*[str(row.get(key, "")) for key, _ in columns])

    console.print(table)
    if footer:
        console.print(footer)
