"""Cached lookups that turn human-readable config into Linear UUIDs.

`config.load()` and `notifiers.build_all()` both run inside `lambda_handler`,
so a notifier instance lives for a single invocation. These caches sit at
module scope instead, where they survive for the life of the execution
environment and spare every warm invocation the lookup round trips.
"""

from __future__ import annotations

from typing import Any, Protocol

from .client import LinearError


class _Lookups(Protocol):
    def teams(self) -> list[dict[str, Any]]: ...
    def completed_states(self, team_id: str) -> list[dict[str, Any]]: ...
    def find_label(self, name: str) -> str | None: ...
    def create_label(self, name: str, team_id: str) -> str: ...


_teams: dict[str, str] = {}
_states: dict[tuple[str, str], str] = {}
_labels: dict[tuple[str, str], str] = {}


def reset_cache() -> None:
    _teams.clear()
    _states.clear()
    _labels.clear()


def team_id(client: _Lookups, key: str) -> str:
    wanted = key.strip().lower()
    if wanted in _teams:
        return _teams[wanted]
    available = client.teams()
    for team in available:
        if str(team["key"]).lower() == wanted:
            _teams[wanted] = str(team["id"])
            return _teams[wanted]
    keys = ", ".join(sorted(str(t["key"]) for t in available)) or "none"
    raise LinearError(f"no Linear team with key {key!r}; available: {keys}")


def done_state_id(client: _Lookups, team: str, preferred_name: str) -> str:
    cache_key = (team, preferred_name.lower())
    if cache_key in _states:
        return _states[cache_key]

    states = client.completed_states(team)
    if not states:
        raise LinearError(f"Linear team {team} has no completed workflow state")

    if preferred_name:
        match = next((s for s in states if str(s["name"]).lower() == preferred_name.lower()), None)
        if match is None:
            names = ", ".join(str(s["name"]) for s in states)
            raise LinearError(
                f"no completed Linear state named {preferred_name!r}; available: {names}"
            )
    else:
        # Teams often carry several completed states (Done, Duplicate, ...).
        # Position orders them as they appear in the board, so the first is the
        # ordinary "finished" state.
        match = min(states, key=lambda s: float(s.get("position") or 0))

    _states[cache_key] = str(match["id"])
    return _states[cache_key]


def label_id(client: _Lookups, team: str, name: str) -> str:
    cache_key = (team, name)
    if cache_key in _labels:
        return _labels[cache_key]
    found = client.find_label(name) or client.create_label(name, team)
    _labels[cache_key] = found
    return found
