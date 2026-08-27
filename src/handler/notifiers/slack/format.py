from __future__ import annotations

from typing import Any

from ...config import Config
from ...enrichment import tags as tag_util
from ...events import HealthEvent
from .. import priority
from ..ticket import summary

__all__ = ["blocks", "fallback"]

# Slack rejects blocks that exceed these, so long event descriptions and event
# type codes have to be trimmed rather than passed through.
_HEADER_MAX = 150
_TEXT_MAX = 3000

# Slack fetches this itself, so it has to stay publicly reachable. The
# account-id form is used rather than github.com/clouddrove.png because the id
# survives an org rename.
_LOGO_URL = "https://avatars.githubusercontent.com/u/45422299?s=64"

# Slack has no priority field. An emoji carries the severity at a glance while
# the field keeps the name the other sinks use.
_EMOJI = {
    "urgent": ":rotating_light:",
    "high": ":large_orange_diamond:",
    "medium": ":large_yellow_circle:",
    "low": ":white_circle:",
}


def _clip(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def fallback(ev: HealthEvent) -> str:
    """Plain-text notification body, shared with the ticket sinks."""
    return summary(ev)


def _field(label: str, value: str) -> dict[str, Any]:
    return {"type": "mrkdwn", "text": f"*{label}*\n{value or '-'}"}


def _body(ev: HealthEvent, cfg: Config, heading: str) -> list[dict[str, Any]]:
    level = priority.resolve(cfg, ev)
    emoji = _EMOJI.get(level.strip().lower(), ":white_circle:")

    out: list[dict[str, Any]] = [
        {
            "type": "header",
            # A header only accepts plain_text, never mrkdwn.
            "text": {
                "type": "plain_text",
                "text": _clip(f"{heading}{ev.event_type_code}", _HEADER_MAX),
            },
        },
        {
            "type": "section",
            "fields": [
                _field("Account", ev.account),
                _field("Region", ev.region),
                _field("Priority", f"{emoji} {level}"),
                _field("Status", ev.status_code),
                _field("Instances", ", ".join(ev.entities)),
                _field("Window", f"{ev.start_time} -> {ev.end_time}"),
            ],
        },
    ]

    tagged = {iid: pairs for iid, pairs in ev.instance_tags.items() if pairs}
    if tagged:
        lines = [f"*{iid}*: {tag_util.format_pairs(pairs)}" for iid, pairs in tagged.items()]
        out.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": _clip("\n".join(lines), _TEXT_MAX)},
            }
        )

    out.append(
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": _clip(ev.description or "-", _TEXT_MAX)},
        }
    )
    out.append(
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": _clip(ev.event_arn, _TEXT_MAX)}],
        }
    )
    out.append(_footer(ev))
    return out


def _footer(ev: HealthEvent) -> dict[str, Any]:
    """Branded footer, in the shape Slack integrations conventionally use:
    a small logo followed by source, scope, and origin."""
    return {
        "type": "context",
        "elements": [
            {
                "type": "image",
                "image_url": _LOGO_URL,
                "alt_text": "CloudDrove",
            },
            {
                "type": "mrkdwn",
                "text": f"*CloudDrove* AWS Health Notifier  |  {ev.account}/{ev.region}",
            },
        ],
    }


def blocks(ev: HealthEvent, cfg: Config) -> list[dict[str, Any]]:
    return _body(ev, cfg, "AWS Health: ")
