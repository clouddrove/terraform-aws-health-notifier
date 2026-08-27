from typing import Any

import pytest

from handler.notifiers.linear import resolve
from handler.notifiers.linear.client import LinearError


class _Client:
    def __init__(
        self,
        teams: list[dict[str, Any]] | None = None,
        states: list[dict[str, Any]] | None = None,
        label: str | None = None,
    ) -> None:
        self._teams = teams if teams is not None else [{"id": "t1", "key": "OPS"}]
        self._states = (
            states if states is not None else [{"id": "s1", "name": "Done", "position": 2.0}]
        )
        self._label = label
        self.team_calls = 0
        self.state_calls = 0
        self.find_calls = 0
        self.created_labels: list[tuple[str, str]] = []

    def teams(self) -> list[dict[str, Any]]:
        self.team_calls += 1
        return self._teams

    def completed_states(self, team_id: str) -> list[dict[str, Any]]:
        self.state_calls += 1
        return self._states

    def find_label(self, name: str) -> str | None:
        self.find_calls += 1
        return self._label

    def create_label(self, name: str, team_id: str) -> str:
        self.created_labels.append((name, team_id))
        return "new-label"


@pytest.fixture(autouse=True)
def _clear_cache():
    resolve.reset_cache()
    yield
    resolve.reset_cache()


def test_team_id_matches_key() -> None:
    assert resolve.team_id(_Client(), "OPS") == "t1"


def test_team_id_is_case_insensitive() -> None:
    assert resolve.team_id(_Client(), "ops") == "t1"


def test_team_id_unknown_key_raises_with_available_keys() -> None:
    with pytest.raises(LinearError, match="OPS"):
        resolve.team_id(_Client(), "NOPE")


def test_team_id_is_cached_across_notifier_instances() -> None:
    # build_all() runs inside lambda_handler, so notifier objects are rebuilt
    # every invocation. The cache only pays off if it lives at module scope.
    c = _Client()
    resolve.team_id(c, "OPS")
    resolve.team_id(c, "OPS")
    assert c.team_calls == 1


def test_done_state_prefers_lowest_position() -> None:
    c = _Client(
        states=[
            {"id": "s2", "name": "Duplicate", "position": 9.0},
            {"id": "s1", "name": "Done", "position": 2.0},
        ]
    )
    assert resolve.done_state_id(c, "t1", "") == "s1"


def test_done_state_matches_configured_name() -> None:
    c = _Client(
        states=[
            {"id": "s1", "name": "Done", "position": 2.0},
            {"id": "s2", "name": "Shipped", "position": 9.0},
        ]
    )
    assert resolve.done_state_id(c, "t1", "shipped") == "s2"


def test_done_state_missing_configured_name_raises() -> None:
    with pytest.raises(LinearError, match="Released"):
        resolve.done_state_id(_Client(), "t1", "Released")


def test_done_state_without_any_completed_state_raises() -> None:
    with pytest.raises(LinearError, match="completed"):
        resolve.done_state_id(_Client(states=[]), "t1", "")


def test_done_state_is_cached() -> None:
    c = _Client()
    resolve.done_state_id(c, "t1", "")
    resolve.done_state_id(c, "t1", "")
    assert c.state_calls == 1


def test_label_id_reuses_existing_label() -> None:
    c = _Client(label="l1")
    assert resolve.label_id(c, "t1", "aws-health") == "l1"
    assert c.created_labels == []


def test_label_id_creates_when_absent() -> None:
    c = _Client(label=None)
    assert resolve.label_id(c, "t1", "aws-health") == "new-label"
    assert c.created_labels == [("aws-health", "t1")]


def test_label_id_is_cached() -> None:
    c = _Client(label="l1")
    resolve.label_id(c, "t1", "aws-health")
    resolve.label_id(c, "t1", "aws-health")
    assert c.find_calls == 1
