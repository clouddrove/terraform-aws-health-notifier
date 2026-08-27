from __future__ import annotations

from .. import secrets
from ..config import Config
from .base import Notifier, NotifierError
from .github.client import GithubClient
from .github.notifier import GithubNotifier
from .jira.client import JiraClient
from .jira.notifier import JiraNotifier
from .linear.client import ENDPOINT, LinearClient
from .linear.notifier import LinearNotifier


def _build_one(cfg: Config, name: str) -> Notifier:
    if name == "jira":
        if not cfg.project_key:
            raise ValueError("notifier 'jira' requires JIRA_PROJECT_KEY")
        creds = secrets.load(cfg.jira_secret_arn)
        return JiraNotifier(JiraClient(creds["base_url"], creds["email"], creds["api_token"]))
    if name == "github":
        if not cfg.github_repo:
            raise ValueError("notifier 'github' requires GITHUB_REPO")
        creds = secrets.load(cfg.github_secret_arn)
        gh = GithubClient(creds["token"], creds.get("api_url", "https://api.github.com"))
        return GithubNotifier(gh, cfg.github_repo, cfg.issue_label)
    if name == "linear":
        if not cfg.linear_team_key:
            raise ValueError("notifier 'linear' requires LINEAR_TEAM_KEY")
        creds = secrets.load(cfg.linear_secret_arn)
        lin = LinearClient(creds["api_key"], creds.get("api_url", ENDPOINT))
        return LinearNotifier(lin, cfg.linear_team_key, cfg.linear_done_state, cfg.issue_label)
    raise ValueError(f"unknown notifier: {name}")


def build_all(cfg: Config) -> list[tuple[str, Notifier]]:
    """Build one Notifier per configured name, in order."""
    return [(name, _build_one(cfg, name)) for name in cfg.notifiers]


__all__ = ["Notifier", "NotifierError", "build_all"]
