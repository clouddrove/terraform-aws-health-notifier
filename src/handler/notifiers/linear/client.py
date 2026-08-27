from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from ..base import NotifierError

ENDPOINT = "https://api.linear.app/graphql"

_TEAMS = """
query Teams {
  teams(first: 250) { nodes { id key } }
}
"""

# Linear has no notion of a Jira-style transition. An issue is closed by moving
# it to a workflow state whose type is "completed".
_COMPLETED_STATES = """
query CompletedStates($teamId: String!) {
  team(id: $teamId) {
    states(filter: { type: { eq: "completed" } }, first: 20) {
      nodes { id name position }
    }
  }
}
"""

_FIND_LABEL = """
query FindLabel($name: String!) {
  issueLabels(filter: { name: { eq: $name } }, first: 1) { nodes { id } }
}
"""

_CREATE_LABEL = """
mutation CreateLabel($name: String!, $teamId: String!) {
  issueLabelCreate(input: { name: $name, teamId: $teamId }) {
    success
    issueLabel { id }
  }
}
"""

_CREATE_ISSUE = """
mutation CreateIssue($input: IssueCreateInput!) {
  issueCreate(input: $input) {
    success
    issue { id identifier url }
  }
}
"""

_CREATE_COMMENT = """
mutation CreateComment($issueId: String!, $body: String!) {
  commentCreate(input: { issueId: $issueId, body: $body }) { success }
}
"""

_UPDATE_STATE = """
mutation UpdateState($id: String!, $stateId: String!) {
  issueUpdate(id: $id, input: { stateId: $stateId }) { success }
}
"""


class LinearError(NotifierError):
    pass


def _messages(errors: list[dict[str, Any]]) -> str:
    return "; ".join(str(e.get("message", e)) for e in errors)


def _is_rate_limited(errors: list[dict[str, Any]]) -> bool:
    return any(e.get("extensions", {}).get("code") == "RATELIMITED" for e in errors)


class LinearClient:
    def __init__(self, api_key: str, api_url: str = ENDPOINT) -> None:
        self._url = api_url
        self._key = api_key

    def _request(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        data = json.dumps({"query": query, "variables": variables}).encode()
        req = urllib.request.Request(self._url, data=data, method="POST")
        # A personal API key goes in the header verbatim; only OAuth access
        # tokens carry the "Bearer" prefix.
        req.add_header("Authorization", self._key)
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310
                raw = resp.read()
        except urllib.error.HTTPError as exc:
            raise self._http_error(exc) from exc
        except urllib.error.URLError as exc:
            raise LinearError(f"linear graphql -> network error: {exc.reason}") from exc

        body: dict[str, Any] = json.loads(raw) if raw else {}
        # GraphQL reports failures inside a 200 response, and a query can
        # partially succeed, so the errors array is authoritative over status.
        errors = body.get("errors")
        if errors:
            raise LinearError(f"linear graphql error: {_messages(errors)}")
        data_field: dict[str, Any] = body.get("data") or {}
        return data_field

    def _http_error(self, exc: urllib.error.HTTPError) -> LinearError:
        raw = exc.read().decode()
        try:
            errors = json.loads(raw).get("errors") or []
        except ValueError:
            errors = []
        if _is_rate_limited(errors):
            return LinearError(f"linear graphql -> rate limited: {raw}", status=exc.code)
        return LinearError(f"linear graphql -> {exc.code}: {raw}", status=exc.code)

    def _mutate(self, query: str, variables: dict[str, Any], field: str) -> dict[str, Any]:
        payload: dict[str, Any] = self._request(query, variables).get(field) or {}
        if not payload.get("success"):
            raise LinearError(f"linear {field} reported failure")
        return payload

    def teams(self) -> list[dict[str, Any]]:
        nodes: list[dict[str, Any]] = self._request(_TEAMS, {})["teams"]["nodes"]
        return nodes

    def completed_states(self, team_id: str) -> list[dict[str, Any]]:
        team = self._request(_COMPLETED_STATES, {"teamId": team_id}).get("team")
        if not team:
            return []
        nodes: list[dict[str, Any]] = team["states"]["nodes"]
        return nodes

    def find_label(self, name: str) -> str | None:
        nodes = self._request(_FIND_LABEL, {"name": name})["issueLabels"]["nodes"]
        return str(nodes[0]["id"]) if nodes else None

    def create_label(self, name: str, team_id: str) -> str:
        payload = self._mutate(_CREATE_LABEL, {"name": name, "teamId": team_id}, "issueLabelCreate")
        return str(payload["issueLabel"]["id"])

    def create_issue(
        self, team_id: str, title: str, description: str, priority: int, label_ids: list[str]
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "teamId": team_id,
            "title": title,
            "description": description,
            "priority": priority,
        }
        if label_ids:
            payload["labelIds"] = label_ids
        created = self._mutate(_CREATE_ISSUE, {"input": payload}, "issueCreate")
        issue: dict[str, Any] = created["issue"]
        return issue

    def add_comment(self, issue_id: str, body: str) -> None:
        self._mutate(_CREATE_COMMENT, {"issueId": issue_id, "body": body}, "commentCreate")

    def set_state(self, issue_id: str, state_id: str) -> None:
        self._mutate(_UPDATE_STATE, {"id": issue_id, "stateId": state_id}, "issueUpdate")
