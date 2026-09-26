from __future__ import annotations

from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.constants import CLICK_TIMEOUT_MS
from browser.detector import MatchResult


async def click_match(match: MatchResult) -> None:
    """Click inside the browser without touching the Windows pointer."""
    try:
        await match.locator.click(timeout=CLICK_TIMEOUT_MS)
    except PlaywrightTimeoutError as exc:
        raise RuntimeError(
            "Matching element disappeared or could not be clicked in time."
        ) from exc
