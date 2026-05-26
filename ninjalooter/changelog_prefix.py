"""In-app changelog prefix (prepended in the Changelog tab only)."""

from pathlib import Path

_PREFIX_PATH = Path(__file__).with_name("changelog_prefix.md")
_cached: str | None = None


def get_changelog_prefix() -> str:
    """Return the standard prefix block (cached)."""
    global _cached  # noqa: PLW0603
    if _cached is None:
        _cached = _PREFIX_PATH.read_text(encoding="utf-8").strip()
    return _cached


def strip_changelog_prefix(body: str) -> str:
    """Remove the prefix from a release body if present (avoids duplicate sections)."""
    text = body.strip()
    prefix = get_changelog_prefix()
    if text.startswith(prefix):
        return text[len(prefix) :].strip()
    return text
