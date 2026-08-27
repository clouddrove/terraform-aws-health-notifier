from __future__ import annotations

from ...config import Config
from ...events import HealthEvent
from .. import priority
from ..ticket import markdown_body, summary

__all__ = ["body", "priority_value", "summary"]

# Linear stores priority as an Int rather than a named value. 0 means "no
# priority", which is also the safe landing spot for a name we do not map.
_PRIORITY = {"urgent": 1, "high": 2, "medium": 3, "low": 4}
_NO_PRIORITY = 0


def body(ev: HealthEvent) -> str:
    return markdown_body(ev)


def priority_value(cfg: Config, ev: HealthEvent) -> int:
    return _PRIORITY.get(priority.resolve(cfg, ev).strip().lower(), _NO_PRIORITY)
