"""Parser tests for the Agent Zero GitHub release tag lookup."""

import pytest

from amctl.agent_zero_release import is_latest_keyword, tag_from_release_payload


def test_latest_keyword_is_case_insensitive():
    assert is_latest_keyword("latest")
    assert is_latest_keyword(" Latest ")
    assert not is_latest_keyword("v2.15")


def test_tag_from_release_payload_returns_version_tag():
    assert tag_from_release_payload({"tag_name": "v2.15"}) == "v2.15"


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [],
        {},
        {"tag_name": ""},
        {"tag_name": "latest"},
        {"tag_name": "v2.15\nimage: evil"},
    ],
)
def test_tag_from_release_payload_rejects_unusable_tags(payload):
    with pytest.raises(ValueError):
        tag_from_release_payload(payload)
