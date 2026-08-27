import io
import json
import urllib.error
import urllib.request
from email.message import Message
from typing import Any, cast
from unittest.mock import patch

import pytest

from handler.notifiers.linear.client import ENDPOINT, LinearClient, LinearError


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


def test_personal_api_key_is_sent_raw_without_bearer(rec):
    rec.enqueue(200, {"data": {"teams": {"nodes": []}}})
    LinearClient("lin_api_key").teams()
    # Linear reserves the "Bearer" prefix for OAuth tokens; personal API keys
    # are rejected when prefixed.
    assert rec.requests[0].get_header("Authorization") == "lin_api_key"
    assert rec.requests[0].full_url == ENDPOINT
    assert rec.requests[0].method == "POST"


def test_custom_api_url_is_honoured(rec):
    rec.enqueue(200, {"data": {"teams": {"nodes": []}}})
    LinearClient("k", "https://linear.internal/graphql").teams()
    assert rec.requests[0].full_url == "https://linear.internal/graphql"


def test_graphql_errors_on_http_200_raise(rec):
    # Linear returns failures inside a 200 response; treating status alone as
    # success would silently swallow them.
    rec.enqueue(200, {"errors": [{"message": "Entity not found"}], "data": None})
    with pytest.raises(LinearError, match="Entity not found"):
        LinearClient("k").teams()


def test_partial_success_with_errors_still_raises(rec):
    rec.enqueue(
        200,
        {
            "data": {"teams": {"nodes": [{"id": "t1", "key": "OPS"}]}},
            "errors": [{"message": "bad"}],
        },
    )
    with pytest.raises(LinearError, match="bad"):
        LinearClient("k").teams()


def test_rate_limit_is_reported_as_such(rec):
    # Linear signals throttling with HTTP 400 and a RATELIMITED code, not 429.
    rec.enqueue(400, {"errors": [{"extensions": {"code": "RATELIMITED"}, "message": "slow down"}]})
    with pytest.raises(LinearError, match="rate limited") as exc:
        LinearClient("k").teams()
    assert exc.value.status == 400


def test_other_http_errors_keep_status(rec):
    rec.enqueue(401, {"errors": [{"message": "Authentication required"}]})
    with pytest.raises(LinearError, match="401") as exc:
        LinearClient("k").teams()
    assert exc.value.status == 401


def test_network_error_raises(rec):
    def boom(req, timeout=None):
        raise urllib.error.URLError("unreachable")

    with patch("urllib.request.urlopen", boom), pytest.raises(LinearError, match="network error"):
        LinearClient("k").teams()


def test_teams_returns_nodes(rec):
    rec.enqueue(200, {"data": {"teams": {"nodes": [{"id": "t1", "key": "OPS"}]}}})
    assert LinearClient("k").teams() == [{"id": "t1", "key": "OPS"}]


def test_completed_states_queries_by_team(rec):
    rec.enqueue(
        200,
        {"data": {"team": {"states": {"nodes": [{"id": "s1", "name": "Done", "position": 3.0}]}}}},
    )
    states = LinearClient("k").completed_states("t1")
    assert states == [{"id": "s1", "name": "Done", "position": 3.0}]
    body = sent(rec.requests[0])
    assert body["variables"] == {"teamId": "t1"}
    assert 'type: { eq: "completed" }' in body["query"]


def test_completed_states_on_unknown_team_returns_empty(rec):
    rec.enqueue(200, {"data": {"team": None}})
    assert LinearClient("k").completed_states("nope") == []


def test_find_label_returns_id(rec):
    rec.enqueue(200, {"data": {"issueLabels": {"nodes": [{"id": "l1"}]}}})
    assert LinearClient("k").find_label("aws-health") == "l1"
    assert sent(rec.requests[0])["variables"] == {"name": "aws-health"}


def test_find_label_returns_none_when_absent(rec):
    rec.enqueue(200, {"data": {"issueLabels": {"nodes": []}}})
    assert LinearClient("k").find_label("aws-health") is None


def test_create_label_returns_id(rec):
    rec.enqueue(200, {"data": {"issueLabelCreate": {"success": True, "issueLabel": {"id": "l9"}}}})
    assert LinearClient("k").create_label("aws-health", "t1") == "l9"
    assert sent(rec.requests[0])["variables"] == {"name": "aws-health", "teamId": "t1"}


def test_create_issue_sends_input_and_returns_refs(rec):
    rec.enqueue(
        200,
        {
            "data": {
                "issueCreate": {
                    "success": True,
                    "issue": {"id": "uuid-1", "identifier": "OPS-7", "url": "https://lin/OPS-7"},
                }
            }
        },
    )
    issue = LinearClient("k").create_issue("t1", "title", "body", 2, ["l1"])
    assert issue == {"id": "uuid-1", "identifier": "OPS-7", "url": "https://lin/OPS-7"}
    assert sent(rec.requests[0])["variables"]["input"] == {
        "teamId": "t1",
        "title": "title",
        "description": "body",
        "priority": 2,
        "labelIds": ["l1"],
    }


def test_create_issue_omits_empty_labels(rec):
    rec.enqueue(
        200,
        {"data": {"issueCreate": {"success": True, "issue": {"id": "u", "identifier": "OPS-1"}}}},
    )
    LinearClient("k").create_issue("t1", "t", "b", 0, [])
    assert "labelIds" not in sent(rec.requests[0])["variables"]["input"]


def test_mutation_reporting_failure_raises(rec):
    # A mutation can return success: false without a GraphQL error.
    rec.enqueue(200, {"data": {"issueCreate": {"success": False, "issue": None}}})
    with pytest.raises(LinearError, match="issueCreate"):
        LinearClient("k").create_issue("t1", "t", "b", 0, [])


def test_add_comment_posts_body(rec):
    rec.enqueue(200, {"data": {"commentCreate": {"success": True}}})
    LinearClient("k").add_comment("uuid-1", "resolved")
    assert sent(rec.requests[0])["variables"] == {"issueId": "uuid-1", "body": "resolved"}


def test_set_state_updates_issue(rec):
    rec.enqueue(200, {"data": {"issueUpdate": {"success": True}}})
    LinearClient("k").set_state("uuid-1", "s1")
    assert sent(rec.requests[0])["variables"] == {"id": "uuid-1", "stateId": "s1"}
