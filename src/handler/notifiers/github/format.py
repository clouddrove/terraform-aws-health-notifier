from __future__ import annotations

from ...config import Config
from ...events import HealthEvent
from .. import priority
from ..ticket import markdown_body, summary

__all__ = ["body", "priority_label", "summary"]


def body(ev: HealthEvent) -> str:
    return markdown_body(ev)


def priority_label(cfg: Config, ev: HealthEvent) -> str:
    return f"priority:{priority.resolve(cfg, ev).lower()}"
