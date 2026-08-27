import io
import json
import urllib.error
import urllib.request
from email.message import Message
from typing import Any, cast
from unittest.mock import patch

import pytest

from handler.notifiers.slack.client import API, SlackClient, SlackError


class _FakeResp:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "_FakeResp":
        return self

    def __exit__(self, *args: object) -> None:
        return None


class _Recorder:
    def __init__(self) -> None:
        self.requests: list[urllib.request.Request] = []
        self._queue: list[tuple[int, dict[str, Any]]] = []

    def enqueue(self, status: int, body: dict[str, Any]) -> None:
        self._queue.append((status, body))

    def __call__(self, req: urllib.request.Request, timeout: float | None = None) -> _FakeResp:
        self.requests.append(req)
        status, body = self._queue.pop(0)
        payload = json.dumps(body).encode()
        if status >= 400:
            raise urllib.error.HTTPError(
                req.full_url, status, "err", Message(), io.BytesIO(payload)
            )
        return _FakeResp(payload)


@pytest.fixture
def rec():
    recorder = _Recorder()
    with patch("urllib.request.urlopen", recorder):
        yield recorder


def sent(req: urllib.request.Request) -> dict[str, Any]:
    payload: dict[str, Any] = json.loads(cast(bytes, req.data))
    return payload


def test_bot_token_is_sent_as_bearer(rec):
    rec.enqueue(200, {"ok": True, "channel": "C1", "ts": "1.1"})
    SlackClient("xoxb-tok").post_message("C1", "hi", [])
    assert rec.requests[0].get_header("Authorization") == "Bearer xoxb-tok"
    assert rec.requests[0].full_url == f"{API}/chat.postMessage"
    assert rec.requests[0].method == "POST"


def test_ok_false_on_http_200_raises():
    # Slack reports almost every failure with a 200 and ok: false. Treating the
    # status as success would swallow them silently.
    rec = _Recorder()
    rec.enqueue(200, {"ok": False, "error": "channel_not_found"})
    with patch("urllib.request.urlopen", rec), pytest.raises(SlackError, match="channel_not_found"):
        SlackClient("t").post_message("C1", "hi", [])


def test_post_message_returns_channel_and_ts(rec):
    rec.enqueue(200, {"ok": True, "channel": "C123", "ts": "1503435956.000247"})
    assert SlackClient("t").post_message("C123", "hi", []) == ("C123", "1503435956.000247")


def test_post_message_sends_text_and_blocks(rec):
    rec.enqueue(200, {"ok": True, "channel": "C1", "ts": "1.1"})
    blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": "x"}}]
    SlackClient("t").post_message("C1", "fallback", blocks)
    body = sent(rec.requests[0])
    assert body["channel"] == "C1"
    # text is the notification and accessibility fallback; it always ships
    # alongside blocks rather than being replaced by them.
    assert body["text"] == "fallback"
    assert body["blocks"] == blocks


def test_post_message_threads_when_given_a_parent(rec):
    rec.enqueue(200, {"ok": True, "channel": "C1", "ts": "2.2"})
    SlackClient("t").post_message("C1", "reply", [], thread_ts="1.1")
    assert sent(rec.requests[0])["thread_ts"] == "1.1"


def test_post_message_omits_thread_ts_when_absent(rec):
    rec.enqueue(200, {"ok": True, "channel": "C1", "ts": "1.1"})
    SlackClient("t").post_message("C1", "top level", [])
    assert "thread_ts" not in sent(rec.requests[0])


def test_add_reaction_targets_channel_and_timestamp(rec):
    rec.enqueue(200, {"ok": True})
    SlackClient("t").add_reaction("C1", "1.1", "white_check_mark")
    assert rec.requests[0].full_url == f"{API}/reactions.add"
    body = sent(rec.requests[0])
    # reactions.add names the field "timestamp", not "ts".
    assert body == {"channel": "C1", "timestamp": "1.1", "name": "white_check_mark"}


def test_add_reaction_tolerates_a_repeat(rec):
    # A retried close must not fail just because the mark is already there.
    rec.enqueue(200, {"ok": False, "error": "already_reacted"})
    SlackClient("t").add_reaction("C1", "1.1", "white_check_mark")


def test_add_reaction_reraises_other_errors(rec):
    rec.enqueue(200, {"ok": False, "error": "message_not_found"})
    with pytest.raises(SlackError, match="message_not_found"):
        SlackClient("t").add_reaction("C1", "1.1", "white_check_mark")


def test_error_carries_the_slack_error_code(rec):
    rec.enqueue(200, {"ok": False, "error": "channel_not_found"})
    with pytest.raises(SlackError) as exc:
        SlackClient("t").post_message("C1", "x", [])
    assert exc.value.slack_error == "channel_not_found"


def test_rate_limit_is_reported_as_such(rec):
    rec.enqueue(429, {"ok": False, "error": "ratelimited"})
    with pytest.raises(SlackError, match="rate limited") as exc:
        SlackClient("t").post_message("C1", "hi", [])
    assert exc.value.status == 429


def test_other_http_errors_keep_status(rec):
    rec.enqueue(500, {"ok": False, "error": "server_error"})
    with pytest.raises(SlackError, match="500") as exc:
        SlackClient("t").post_message("C1", "hi", [])
    assert exc.value.status == 500


def test_network_error_raises():
    def boom(req, timeout=None):
        raise urllib.error.URLError("unreachable")

    with patch("urllib.request.urlopen", boom), pytest.raises(SlackError, match="network error"):
        SlackClient("t").post_message("C1", "hi", [])
