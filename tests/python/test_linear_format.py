from handler.events import HealthEvent
from handler.notifiers.linear import format as lin
from tests.python.conftest import make_config

EV = HealthEvent(
    "arn:abc",
    "AWS_EC2_INSTANCE_RETIREMENT_SCHEDULED",
    "open",
    "111122223333",
    "us-east-1",
    ["i-0abc"],
    "Instance retiring",
    "2026-09-01T00:00:00Z",
    "2026-09-02T00:00:00Z",
)


def test_summary_matches_the_other_sinks() -> None:
    assert lin.summary(EV) == (
        "[AWS Health] AWS_EC2_INSTANCE_RETIREMENT_SCHEDULED - i-0abc (111122223333/us-east-1)"
    )


def test_body_is_markdown() -> None:
    body = lin.body(EV)
    assert "**Account**: 111122223333" in body
    assert "Instance retiring" in body


def test_body_includes_instance_tags() -> None:
    ev = HealthEvent(
        "arn:abc",
        "T",
        "open",
        "1",
        "us-east-1",
        ["i-0abc"],
        "d",
        "s",
        "e",
        {"i-0abc": {"Name": "web", "Environment": "prod"}},
    )
    assert "- **i-0abc**:" in lin.body(ev)


def test_priority_maps_names_onto_linear_integers() -> None:
    cases = {"Urgent": 1, "High": 2, "Medium": 3, "Low": 4}
    for name, expected in cases.items():
        cfg = make_config(priority_map={"AWS_EC2_INSTANCE_RETIREMENT_SCHEDULED": name})
        assert lin.priority_value(cfg, EV) == expected


def test_priority_is_case_insensitive() -> None:
    cfg = make_config(priority_map={"AWS_EC2_INSTANCE_RETIREMENT_SCHEDULED": "hIgH"})
    assert lin.priority_value(cfg, EV) == 2


def test_unmapped_priority_falls_back_to_no_priority() -> None:
    # Linear treats 0 as "no priority" rather than rejecting the value.
    cfg = make_config(priority_map={"AWS_EC2_INSTANCE_RETIREMENT_SCHEDULED": "Blocker"})
    assert lin.priority_value(cfg, EV) == 0


def test_priority_falls_back_to_config_default() -> None:
    cfg = make_config(priority_map={}, default_priority="Low")
    assert lin.priority_value(cfg, EV) == 4
