from __future__ import annotations

from ... import logging as structured_log
from ...config import Config
from ...events import HealthEvent
from . import format as slack_format
from .client import SlackClient, SlackError

_RESOLVED_TEXT = "AWS Health event resolved."
_RESOLVED_REACTION = "white_check_mark"


class SlackNotifier:
    """Posts AWS Health events to a Slack channel.

    Slack is an alerting sink rather than a tracker: there is no assignee or
    status field. Dedup and auto-close still work because handler state is keyed
    per sink, so a redelivery never reposts.
    """

    def __init__(self, client: SlackClient, channel: str) -> None:
        self._client = client
        self._channel = channel

    def open(self, ev: HealthEvent, cfg: Config) -> str:
        # chat.update needs the channel as well as the timestamp, so the ref
        # carries both. ts is the only durable handle Slack gives a message.
        channel, ts = self._client.post_message(
            self._channel, slack_format.fallback(ev), slack_format.blocks(ev, cfg)
        )
        return f"{channel}:{ts}"

    def close(self, ref: str, cfg: Config) -> None:
        channel, ts = self._split(ref)

        # The threaded reply goes first because it is the durable signal, and it
        # is what makes close() safe to retry: if it fails, nothing has been
        # recorded and the whole close runs again.
        self._client.post_message(channel, _RESOLVED_TEXT, [], thread_ts=ts)

        # Marking the original is cosmetic, so a failure here is logged rather
        # than raised. Raising would leave the sink unmarked in DynamoDB and the
        # next delivery would post the reply a second time.
        try:
            self._client.add_reaction(channel, ts, _RESOLVED_REACTION)
        except SlackError as exc:
            structured_log.emit("slack-reaction-failed", ref, reason=str(exc))

    @staticmethod
    def _split(ref: str) -> tuple[str, str]:
        channel, sep, ts = ref.partition(":")
        if not sep or not channel or not ts:
            raise ValueError(f"malformed slack ref {ref!r}, expected '<channel>:<ts>'")
        return channel, ts
