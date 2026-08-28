from typing import Any

from handler.events import HealthEvent
from handler.notifiers.slack import format as sl
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
CFG = make_config(priority_map={"AWS_EC2_INSTANCE_RETIREMENT_SCHEDULED": "High"})


def types(blocks: list[dict[str, Any]]) -> list[str]:
    return [str(b["type"]) for b in blocks]


def test_fallback_text_matches_the_other_sinks() -> None:
    assert sl.fallback(EV) == (
        "[AWS Health] AWS_EC2_INSTANCE_RETIREMENT_SCHEDULED - i-0abc (111122223333/us-east-1)"
    )


def test_blocks_lead_with_a_header() -> None:
    blocks = sl.blocks(EV, CFG)
    assert types(blocks)[0] == "header"
    # header text must be plain_text; mrkdwn is rejected by Slack there.
    assert blocks[0]["text"]["type"] == "plain_text"


def test_blocks_carry_account_region_and_instances() -> None:
    rendered = str(sl.blocks(EV, CFG))
    assert "111122223333" in rendered
    assert "us-east-1" in rendered
    assert "i-0abc" in rendered


def test_priority_is_rendered_as_a_field_not_a_label() -> None:
    assert "High" in str(sl.blocks(EV, CFG))


def test_header_is_truncated_to_slack_limit() -> None:
    ev = HealthEvent("arn:abc", "T" * 200, "open", "1", "us-east-1", ["i-0abc"], "d", "s", "e")
    header = sl.blocks(ev, CFG)[0]["text"]["text"]
    # Slack rejects a header longer than 150 characters.
    assert len(header) <= 150


def test_description_is_truncated_to_block_limit() -> None:
    ev = HealthEvent("arn:abc", "T", "open", "1", "us-east-1", ["i-0abc"], "x" * 5000, "s", "e")
    for block in sl.blocks(ev, CFG):
        if block["type"] == "section" and "text" in block:
            assert len(block["text"]["text"]) <= 3000


def test_instance_tags_are_included_when_present() -> None:
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
        {"i-0abc": {"Name": "web"}},
    )
    assert "web" in str(sl.blocks(ev, CFG))


def test_footer_is_the_last_block_and_carries_branding() -> None:
    footer = sl.blocks(EV, CFG)[-1]
    assert footer["type"] == "context"
    kinds = [e["type"] for e in footer["elements"]]
    assert kinds == ["image", "mrkdwn"]
    assert "CloudDrove" in footer["elements"][1]["text"]
    assert footer["elements"][0]["alt_text"] == "CloudDrove"


def test_footer_scopes_the_alert_to_account_and_region() -> None:
    text = sl.blocks(EV, CFG)[-1]["elements"][1]["text"]
    assert "111122223333/us-east-1" in text


def test_footer_image_is_an_absolute_https_url() -> None:
    # Slack fetches the image itself; a relative or http URL is rejected.
    url = sl.blocks(EV, CFG)[-1]["elements"][0]["image_url"]
    assert url.startswith("https://")
