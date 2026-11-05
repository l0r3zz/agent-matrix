"""Resolve the Agent Zero image tag from the upstream GitHub release."""

import re

import httpx

_TAG_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$")

LATEST_RELEASE_URL = "https://api.github.com/repos/agent0ai/agent-zero/releases/latest"
GITHUB_HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "am-ctl",
}


def is_latest_keyword(image_version: str) -> bool:
    """True when the operator asked for the current GitHub release tag."""
    return image_version.strip().lower() == "latest"


def tag_from_release_payload(payload: object) -> str:
    """Return the Docker image tag from a GitHub release object."""
    if not isinstance(payload, dict):
        raise ValueError("GitHub latest release response was not an object")
    tag = payload.get("tag_name")
    if not isinstance(tag, str) or not tag.strip():
        raise ValueError("GitHub latest release did not include a tag_name")
    tag = tag.strip()
    if tag.lower() == "latest" or not _TAG_RE.fullmatch(tag):
        raise ValueError("GitHub release tag_name must be a version tag")
    return tag


def _tag_from_response(response: httpx.Response) -> str:
    if response.status_code != 200:
        raise ValueError(
            f"GitHub latest release lookup failed: HTTP {response.status_code}"
        )
    return tag_from_release_payload(response.json())


def fetch_latest_tag_sync(timeout: float = 15.0) -> str:
    """GET the latest non-prerelease Agent Zero release and return its tag."""
    try:
        with httpx.Client(timeout=timeout, headers=GITHUB_HEADERS) as client:
            response = client.get(LATEST_RELEASE_URL)
    except httpx.HTTPError as exc:
        raise ValueError(f"GitHub latest release lookup failed: {exc}") from exc
    return _tag_from_response(response)


async def fetch_latest_tag(timeout: float = 15.0) -> str:
    """Async form of :func:`fetch_latest_tag_sync` for the deploy API."""
    try:
        async with httpx.AsyncClient(timeout=timeout, headers=GITHUB_HEADERS) as client:
            response = await client.get(LATEST_RELEASE_URL)
    except httpx.HTTPError as exc:
        raise ValueError(f"GitHub latest release lookup failed: {exc}") from exc
    return _tag_from_response(response)
