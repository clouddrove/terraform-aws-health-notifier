import pytest

from handler import config


def _env(monkeypatch: pytest.MonkeyPatch, **kw: str) -> None:
    monkeypatch.setenv("TABLE_NAME", "t")
    for k, v in kw.items():
        monkeypatch.setenv(k, v)


def test_notifiers_default_jira(monkeypatch):
    _env(monkeypatch)
    assert config.load().notifiers == ["jira"]


def test_notifiers_list_parsed(monkeypatch):
    _env(monkeypatch, NOTIFIERS="jira, github , jira")
    assert config.load().notifiers == ["jira", "github"]


def test_parse_notifiers_helper():
    assert config.parse_notifiers("GitHub, ,jira") == ["github", "jira"]


def test_per_sink_secret_arns(monkeypatch):
    _env(monkeypatch, JIRA_SECRET_ARN="arn:j", GITHUB_SECRET_ARN="arn:g", GITHUB_REPO="o/r")
    cfg = config.load()
    assert cfg.jira_secret_arn == "arn:j"
    assert cfg.github_secret_arn == "arn:g"
    assert cfg.github_repo == "o/r"


def test_enrich_defaults(monkeypatch):
    _env(monkeypatch)
    cfg = config.load()
    assert cfg.enrich_tags is False
    assert cfg.describe_role_name == "aws-health-notifier-describe"
    assert cfg.tag_keys == ["Name", "Environment"]


def test_enrich_enabled(monkeypatch):
    _env(monkeypatch, ENRICH_TAGS="true", TAG_KEYS="Name, Team")
    cfg = config.load()
    assert cfg.enrich_tags is True
    assert cfg.tag_keys == ["Name", "Team"]


def test_linear_config(monkeypatch):
    _env(
        monkeypatch,
        NOTIFIERS="linear",
        LINEAR_SECRET_ARN="arn:l",
        LINEAR_TEAM_KEY="OPS",
        LINEAR_DONE_STATE="Shipped",
    )
    cfg = config.load()
    assert cfg.notifiers == ["linear"]
    assert cfg.linear_secret_arn == "arn:l"
    assert cfg.linear_team_key == "OPS"
    assert cfg.linear_done_state == "Shipped"


def test_linear_done_state_defaults_to_empty(monkeypatch):
    _env(monkeypatch)
    assert config.load().linear_done_state == ""


def test_issue_label_defaults(monkeypatch):
    _env(monkeypatch)
    assert config.load().issue_label == "aws-health"


def test_issue_label_override(monkeypatch):
    _env(monkeypatch, ISSUE_LABEL="infra-alerts")
    assert config.load().issue_label == "infra-alerts"


def test_slack_config(monkeypatch):
    _env(monkeypatch, NOTIFIERS="slack", SLACK_SECRET_ARN="arn:s", SLACK_CHANNEL="C123")
    cfg = config.load()
    assert cfg.notifiers == ["slack"]
    assert cfg.slack_secret_arn == "arn:s"
    assert cfg.slack_channel == "C123"


def test_slack_defaults_empty(monkeypatch):
    _env(monkeypatch)
    cfg = config.load()
    assert cfg.slack_secret_arn == "" and cfg.slack_channel == ""
