import logging
from typing import Any

import pytest

from handler.events import HealthEvent
from handler.notifiers.slack.client import SlackError
from handler.notifiers.slack.notifier import SlackNotifier
from tests.python.conftest import make_config

CFG = make_config(
    notifiers=["slack"],
    slack_channel="C123",
    priority_map={"AWS_EC2_INSTANCE_RETIREMENT_SCHEDULED": "High"},
)
EV = HealthEvent(
    "arn:abc",
    "AWS_EC2_INSTANCE_RETIREMENT_SCHEDULED",
    "open",
    "1",
    "us-east-1",
    ["i-0abc"],
    "d",
    "s",
    "e",
)


class _Client:
    def __init__(self, reaction_error: Exception | None = None) -> None:
        self.posts: list[dict[str, Any]] = []
        self.reactions: list[dict[str, Any]] = []
        self._reaction_error = reaction_error

    def post_message(self, channel, text, blocks, thread_ts=None):
        self.posts.append(
            {"channel": channel, "text": text, "blocks": blocks, "thread_ts": thread_ts}
        )
        return channel, "1503435956.000247"

    def add_reaction(self, channel, ts, name):
        if self._reaction_error:
            raise self._reaction_error
        self.reactions.append({"channel": channel, "ts": ts, "name": name})


def notifier(c: _Client) -> SlackNotifier:
    return SlackNotifier(c, "C123")  # type: ignore[arg-type]


def test_open_returns_channel_and_ts_as_the_ref() -> None:
    # chat.update needs both, so both have to survive in DynamoDB.
    assert notifier(_Client()).open(EV, CFG) == "C123:1503435956.000247"


def test_open_posts_to_the_configured_channel_at_top_level() -> None:
    c = _Client()
    notifier(c).open(EV, CFG)
    assert c.posts[0]["channel"] == "C123"
    assert c.posts[0]["thread_ts"] is None
    assert c.posts[0]["text"].startswith("[AWS Health]")


def test_close_replies_in_thread_then_marks_the_original() -> None:
    c = _Client()
    notifier(c).close("C123:1503435956.000247", CFG)
    assert c.posts[0]["thread_ts"] == "1503435956.000247"
    # A reaction, not chat.update: close() has no event to rebuild blocks from,
    # so an update would wipe the original message's detail.
    assert c.reactions[0] == {
        "channel": "C123",
        "ts": "1503435956.000247",
        "name": "white_check_mark",
    }


def test_close_survives_a_failed_reaction(caplog) -> None:
    # The threaded reply is the durable signal. Raising here would leave the
    # sink unmarked in DynamoDB, so the next delivery would post the reply
    # again; the mark is cosmetic and must not cause that.
    c = _Client(reaction_error=SlackError("reactions.add -> message_not_found"))
    with caplog.at_level(logging.INFO):
        notifier(c).close("C123:1503435956.000247", CFG)
    assert c.posts[0]["thread_ts"] == "1503435956.000247"
    assert "message_not_found" in caplog.text


def test_close_propagates_a_failed_reply() -> None:
    class _Broken(_Client):
        def post_message(self, *a, **k):
            raise SlackError("chat.postMessage -> channel_not_found")

    with pytest.raises(SlackError):
        notifier(_Broken()).close("C123:1.1", CFG)


def test_close_rejects_a_malformed_ref() -> None:
    with pytest.raises(ValueError, match="ref"):
        notifier(_Client()).close("no-separator", CFG)


def test_close_uses_the_channel_from_the_ref_not_the_config() -> None:
    # The channel may have been reconfigured since the message was posted.
    c = _Client()
    SlackNotifier(c, "C-new").close("C-old:1.1", CFG)  # type: ignore[arg-type]
    assert c.posts[0]["channel"] == "C-old"
    assert c.reactions[0]["channel"] == "C-old"
