import json
from typing import Any

import boto3
import pytest
from moto import mock_aws

from handler import notifiers
from handler.events import HealthEvent
from handler.notifiers.github.notifier import GithubNotifier
from handler.notifiers.jira.notifier import JiraNotifier
from handler.notifiers.linear.notifier import LinearNotifier
from handler.notifiers.slack.notifier import SlackNotifier
from tests.python.conftest import make_config

EV = HealthEvent(
    "arn:abc",
    "AWS_EC2_INSTANCE_RETIREMENT_SCHEDULED",
    "open",
    "111122223333",
    "us-east-1",
    ["i-0abc123"],
    "d",
    "s",
    "e",
)


class _JiraClient:
    def __init__(self) -> None:
        self.created: dict[str, Any] = {}
        self.comments: list[tuple[str, str]] = []
        self.transitions: list[tuple[str, str]] = []

    def create_issue(self, project_key, issue_type, summary, description, priority) -> str:
        self.created = {"project": project_key, "priority": priority, "summary": summary}
        return "OPS-9"

    def add_comment(self, ref, text) -> None:
        self.comments.append((ref, text))

    def transition(self, ref, name) -> None:
        self.transitions.append((ref, name))


def test_jira_notifier_open_uses_enrichment() -> None:
    client = _JiraClient()
    cfg = make_config(priority_map={"AWS_EC2_INSTANCE_RETIREMENT_SCHEDULED": "High"})
    ref = JiraNotifier(client).open(EV, cfg)  # type: ignore[arg-type]
    assert ref == "OPS-9"
    assert client.created["priority"] == "High"
    assert "i-0abc123" in client.created["summary"]


def test_jira_notifier_close_comments_and_transitions() -> None:
    client = _JiraClient()
    JiraNotifier(client).close("OPS-9", make_config())  # type: ignore[arg-type]
    assert client.comments[0][0] == "OPS-9"
    assert client.transitions[0] == ("OPS-9", "Done")


def _secret(name: str, payload: dict[str, Any]) -> str:
    sm = boto3.client("secretsmanager", region_name="us-east-1")
    return sm.create_secret(Name=name, SecretString=json.dumps(payload))["ARN"]


def test_build_all_jira_only() -> None:
    with mock_aws():
        arn = _secret("j", {"base_url": "https://x.atlassian.net", "email": "e", "api_token": "t"})
        cfg = make_config(notifiers=["jira"], project_key="OPS", jira_secret_arn=arn)
        built = notifiers.build_all(cfg)
        assert [n for n, _ in built] == ["jira"]
        assert isinstance(built[0][1], JiraNotifier)


def test_build_all_both() -> None:
    with mock_aws():
        ja = _secret("j", {"base_url": "https://x.atlassian.net", "email": "e", "api_token": "t"})
        ga = _secret("g", {"token": "t"})
        cfg = make_config(
            notifiers=["jira", "github"],
            project_key="OPS",
            github_repo="o/r",
            jira_secret_arn=ja,
            github_secret_arn=ga,
        )
        built = notifiers.build_all(cfg)
        assert [n for n, _ in built] == ["jira", "github"]
        assert isinstance(built[1][1], GithubNotifier)


def test_build_all_jira_missing_project_key() -> None:
    cfg = make_config(notifiers=["jira"], project_key="")
    with pytest.raises(ValueError, match="requires JIRA_PROJECT_KEY"):
        notifiers.build_all(cfg)


def test_build_all_github_missing_repo() -> None:
    cfg = make_config(notifiers=["github"], github_repo="")
    with pytest.raises(ValueError, match="requires GITHUB_REPO"):
        notifiers.build_all(cfg)


def test_build_all_unknown() -> None:
    # "slack" used to stand in for an unknown sink here; it is a real one now.
    cfg = make_config(notifiers=["pagerduty"])
    with pytest.raises(ValueError, match="unknown notifier"):
        notifiers.build_all(cfg)


def test_build_all_linear() -> None:
    with mock_aws():
        arn = _secret("l", {"api_key": "lin_api_x"})
        cfg = make_config(notifiers=["linear"], linear_team_key="OPS", linear_secret_arn=arn)
        built = notifiers.build_all(cfg)
        assert [n for n, _ in built] == ["linear"]
        assert isinstance(built[0][1], LinearNotifier)


def test_build_all_three_sinks_preserves_order() -> None:
    with mock_aws():
        ja = _secret("j", {"base_url": "https://x.atlassian.net", "email": "e", "api_token": "t"})
        ga = _secret("g", {"token": "t"})
        la = _secret("l", {"api_key": "lin_api_x"})
        cfg = make_config(
            notifiers=["jira", "github", "linear"],
            project_key="OPS",
            github_repo="o/r",
            linear_team_key="OPS",
            jira_secret_arn=ja,
            github_secret_arn=ga,
            linear_secret_arn=la,
        )
        assert [n for n, _ in notifiers.build_all(cfg)] == ["jira", "github", "linear"]


def test_build_all_linear_missing_team_key() -> None:
    cfg = make_config(notifiers=["linear"], linear_team_key="")
    with pytest.raises(ValueError, match="requires LINEAR_TEAM_KEY"):
        notifiers.build_all(cfg)


def test_build_all_linear_honours_api_url_override() -> None:
    with mock_aws():
        arn = _secret("l", {"api_key": "k", "api_url": "https://linear.internal/graphql"})
        cfg = make_config(notifiers=["linear"], linear_team_key="OPS", linear_secret_arn=arn)
        built = notifiers.build_all(cfg)
        linear = built[0][1]
        assert isinstance(linear, LinearNotifier)
        assert linear._client._url == "https://linear.internal/graphql"


def test_build_all_slack() -> None:
    with mock_aws():
        arn = _secret("s", {"bot_token": "xoxb-x"})
        cfg = make_config(notifiers=["slack"], slack_channel="C123", slack_secret_arn=arn)
        built = notifiers.build_all(cfg)
        assert [n for n, _ in built] == ["slack"]
        assert isinstance(built[0][1], SlackNotifier)


def test_build_all_slack_missing_channel() -> None:
    cfg = make_config(notifiers=["slack"], slack_channel="")
    with pytest.raises(ValueError, match="requires SLACK_CHANNEL"):
        notifiers.build_all(cfg)


def test_build_all_four_sinks_preserves_order() -> None:
    with mock_aws():
        ja = _secret("j", {"base_url": "https://x.atlassian.net", "email": "e", "api_token": "t"})
        ga = _secret("g", {"token": "t"})
        la = _secret("l", {"api_key": "lin_api_x"})
        sa = _secret("s", {"bot_token": "xoxb-x"})
        cfg = make_config(
            notifiers=["jira", "github", "linear", "slack"],
            project_key="OPS",
            github_repo="o/r",
            linear_team_key="OPS",
            slack_channel="C123",
            jira_secret_arn=ja,
            github_secret_arn=ga,
            linear_secret_arn=la,
            slack_secret_arn=sa,
        )
        assert [n for n, _ in notifiers.build_all(cfg)] == ["jira", "github", "linear", "slack"]
