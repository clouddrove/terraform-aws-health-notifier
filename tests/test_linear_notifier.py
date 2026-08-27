from typing import Any

import pytest

from handler.events import HealthEvent
from handler.notifiers.linear import resolve
from handler.notifiers.linear.notifier import LinearNotifier
from tests.conftest import make_config

CFG = make_config(
    notifiers=["linear"],
    linear_team_key="OPS",
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
    def __init__(self) -> None:
        self.created: dict[str, Any] = {}
        self.comments: list[tuple[str, str]] = []
        self.states: list[tuple[str, str]] = []

    def teams(self) -> list[dict[str, Any]]:
        return [{"id": "t1", "key": "OPS"}]

    def completed_states(self, team_id: str) -> list[dict[str, Any]]:
        return [{"id": "s1", "name": "Done", "position": 1.0}]

    def find_label(self, name: str) -> str | None:
        return "l1"

    def create_label(self, name: str, team_id: str) -> str:
        return "l-new"

    def create_issue(
        self, team_id: str, title: str, description: str, priority: int, label_ids: list[str]
    ) -> dict[str, Any]:
        self.created = {
            "team_id": team_id,
            "title": title,
            "description": description,
            "priority": priority,
            "label_ids": label_ids,
        }
        return {"id": "uuid-1", "identifier": "OPS-7", "url": "https://linear.app/i/OPS-7"}

    def add_comment(self, issue_id: str, body: str) -> None:
        self.comments.append((issue_id, body))

    def set_state(self, issue_id: str, state_id: str) -> None:
        self.states.append((issue_id, state_id))


@pytest.fixture(autouse=True)
def _clear_cache():
    resolve.reset_cache()
    yield
    resolve.reset_cache()


def notifier(client: _Client, label: str = "aws-health") -> LinearNotifier:
    return LinearNotifier(client, "OPS", "", label)  # type: ignore[arg-type]


def test_open_returns_the_issue_uuid_not_the_identifier() -> None:
    # issueUpdate is addressed by UUID, so that is what has to survive in
    # DynamoDB for close() to work.
    c = _Client()
    assert notifier(c).open(EV, CFG) == "uuid-1"


def test_open_sends_team_priority_and_label() -> None:
    c = _Client()
    notifier(c).open(EV, CFG)
    assert c.created["team_id"] == "t1"
    assert c.created["priority"] == 2
    assert c.created["label_ids"] == ["l1"]
    assert c.created["title"].startswith("[AWS Health]")


def test_open_without_a_configured_label_sends_none() -> None:
    c = _Client()
    notifier(c, label="").open(EV, CFG)
    assert c.created["label_ids"] == []


def test_open_logs_the_human_readable_identifier(caplog) -> None:
    c = _Client()
    with caplog.at_level("INFO"):
        notifier(c).open(EV, CFG)
    assert "OPS-7" in caplog.text
    assert "https://linear.app/i/OPS-7" in caplog.text


def test_close_comments_then_moves_to_the_completed_state() -> None:
    c = _Client()
    notifier(c).close("uuid-1", CFG)
    assert c.comments == [("uuid-1", "AWS Health event resolved. Closing.")]
    assert c.states == [("uuid-1", "s1")]
