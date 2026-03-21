"""Chart generation using matplotlib."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt  # noqa: E402


def generate_bar_chart(
    labels: list[str],
    values: list[float],
    *,
    title: str = "",
    ylabel: str = "",
    output: str | Path = "chart.png",
) -> Path:
    """Generate a bar chart and save to file."""
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(range(len(labels)), values, color="#FC4C02")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    fig.tight_layout()

    path = Path(output)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def generate_line_chart(
    labels: list[str],
    values: list[float],
    *,
    title: str = "",
    ylabel: str = "",
    output: str | Path = "chart.png",
) -> Path:
    """Generate a line chart and save to file."""
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(range(len(labels)), values, color="#FC4C02", marker="o", markersize=3)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    fig.tight_layout()

    path = Path(output)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def generate_pie_chart(
    labels: list[str],
    values: list[float],
    *,
    title: str = "",
    output: str | Path = "chart.png",
) -> Path:
    """Generate a pie chart and save to file."""
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.pie(
        values,
        labels=labels,
        autopct="%1.1f%%",
        colors=plt.cm.Oranges([i / len(values) for i in range(len(values))]),
    )
    ax.set_title(title)
    fig.tight_layout()

    path = Path(output)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path
