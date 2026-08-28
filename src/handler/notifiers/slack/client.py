from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from ..base import NotifierError

API = "https://slack.com/api"


class SlackError(NotifierError):
    def __init__(
        self, message: str, status: int | None = None, slack_error: str | None = None
    ) -> None:
        super().__init__(message, status)
        self.slack_error = slack_error


class SlackClient:
    def __init__(self, bot_token: str, api_url: str = API) -> None:
        self._base = api_url.rstrip("/")
        self._token = bot_token

    def _call(self, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(f"{self._base}/{method}", data=data, method="POST")
        req.add_header("Authorization", f"Bearer {self._token}")
        req.add_header("Content-Type", "application/json; charset=utf-8")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310
                raw = resp.read()
        except urllib.error.HTTPError as exc:
            raise self._http_error(method, exc) from exc
        except urllib.error.URLError as exc:
            raise SlackError(f"{method} -> network error: {exc.reason}") from exc

        body: dict[str, Any] = json.loads(raw) if raw else {}
        # Slack answers almost every failure with HTTP 200 and ok: false, so the
        # body decides success, not the status code.
        if not body.get("ok"):
            err = str(body.get("error", "unknown"))
            raise SlackError(f"{method} -> {err}", slack_error=err)
        return body

    def _http_error(self, method: str, exc: urllib.error.HTTPError) -> SlackError:
        raw = exc.read().decode()
        if exc.code == 429:
            return SlackError(
                f"{method} -> rate limited: {raw}", status=429, slack_error="ratelimited"
            )
        return SlackError(f"{method} -> {exc.code}: {raw}", status=exc.code)

    def post_message(
        self,
        channel: str,
        text: str,
        blocks: list[dict[str, Any]],
        thread_ts: str | None = None,
    ) -> tuple[str, str]:
        """Post a message and return its (channel, ts)."""
        # text ships alongside blocks rather than being replaced by them: it is
        # what notifications and screen readers use.
        payload: dict[str, Any] = {"channel": channel, "text": text, "blocks": blocks}
        if thread_ts:
            payload["thread_ts"] = thread_ts
        body = self._call("chat.postMessage", payload)
        return str(body["channel"]), str(body["ts"])

    def add_reaction(self, channel: str, ts: str, name: str) -> None:
        """React to a message. A repeat reaction is treated as success.

        Marking the original resolved with a reaction rather than chat.update
        keeps the event detail intact: close() has only the ref, not the event,
        so it could not rebuild the blocks an update would overwrite.
        """
        try:
            self._call("reactions.add", {"channel": channel, "timestamp": ts, "name": name})
        except SlackError as exc:
            if exc.slack_error != "already_reacted":
                raise
