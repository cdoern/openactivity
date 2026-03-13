"""JSON output helper."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from typing import Any


def _default_serializer(obj: Any) -> Any:
    """Handle non-serializable types."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def print_json(data: Any) -> None:
    """Serialize data as JSON and print to stdout."""
    json.dump(data, sys.stdout, indent=2, default=_default_serializer)
    sys.stdout.write("\n")
