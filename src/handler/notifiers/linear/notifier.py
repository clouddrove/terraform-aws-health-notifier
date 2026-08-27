from __future__ import annotations

from ... import logging as structured_log
from ...config import Config
from ...events import HealthEvent
from . import format as lin_format
from . import resolve
from .client import LinearClient

_RESOLVE_COMMENT = "AWS Health event resolved. Closing."


class LinearNotifier:
    def __init__(self, client: LinearClient, team_key: str, done_state: str, label: str) -> None:
        self._client = client
        self._team_key = team_key
        self._done_state = done_state
        self._label = label

    def open(self, ev: HealthEvent, cfg: Config) -> str:
        team = resolve.team_id(self._client, self._team_key)
        labels = [resolve.label_id(self._client, team, self._label)] if self._label else []
        issue = self._client.create_issue(
            team,
            lin_format.summary(ev),
            lin_format.body(ev),
            lin_format.priority_value(cfg, ev),
            labels,
        )
        # The ref stored in DynamoDB is the UUID that issueUpdate needs, which
        # is unreadable in a log. Emit the identifier and URL alongside it so
        # an operator can find the ticket.
        structured_log.emit(
            "linear-issue",
            ev.event_arn,
            ref=issue["id"],
            identifier=issue.get("identifier"),
            url=issue.get("url"),
        )
        return str(issue["id"])

    def close(self, ref: str, cfg: Config) -> None:
        team = resolve.team_id(self._client, self._team_key)
        state = resolve.done_state_id(self._client, team, self._done_state)
        self._client.add_comment(ref, _RESOLVE_COMMENT)
        self._client.set_state(ref, state)
