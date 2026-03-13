"""TOML configuration management for openactivity."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

import tomli_w

DEFAULT_CONFIG_DIR = Path.home() / ".config" / "openactivity"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.toml"

DEFAULT_CONFIG: dict[str, Any] = {
    "units": {"system": "metric"},
    "sync": {"detail": True},
}


def get_config_path(override: str | None = None) -> Path:
    """Return the config file path, using override if provided."""
    if override:
        return Path(override)
    return DEFAULT_CONFIG_FILE


def load_config(path: Path | None = None) -> dict[str, Any]:
    """Load configuration from TOML file, returning defaults if file doesn't exist."""
    config_path = path or DEFAULT_CONFIG_FILE
    if not config_path.exists():
        return DEFAULT_CONFIG.copy()
    with open(config_path, "rb") as f:
        user_config = tomllib.load(f)
    merged = DEFAULT_CONFIG.copy()
    for key, value in user_config.items():
        if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
            merged[key] = {**merged[key], **value}
        else:
            merged[key] = value
    return merged


def save_config(config: dict[str, Any], path: Path | None = None) -> None:
    """Save configuration to TOML file."""
    config_path = path or DEFAULT_CONFIG_FILE
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "wb") as f:
        tomli_w.dump(config, f)


def get_unit_system(config: dict[str, Any] | None = None) -> str:
    """Return the configured unit system ('metric' or 'imperial')."""
    if config is None:
        config = load_config()
    return config.get("units", {}).get("system", "metric")
