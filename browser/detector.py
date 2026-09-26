from __future__ import annotations

from dataclasses import dataclass

from playwright.async_api import Frame, Locator, Page

from app.models import MatchMode, normalize_text, text_matches

INTERACTIVE_SELECTOR = (
    "button, input[type='button'], input[type='submit'], "
    "[role='button'], a[href]"
)


@dataclass(slots=True)
class MatchResult:
    locator: Locator
    frame_url: str
    text: str
    total_matches: int


async def _locator_text(locator: Locator) -> str:
    tag = await locator.evaluate("(el) => el.tagName.toLowerCase()")
    if tag == "input":
        value = await locator.get_attribute("value")
        return normalize_text(value or "")
    try:
        return normalize_text(await locator.inner_text(timeout=300))
    except Exception:
        aria = await locator.get_attribute("aria-label")
        return normalize_text(aria or "")


async def find_in_frame(
    frame: Frame,
    target: str,
    mode: MatchMode,
) -> list[MatchResult]:
    candidates = frame.locator(INTERACTIVE_SELECTOR)
    try:
        count = await candidates.count()
    except Exception:
        return []
    matched: list[tuple[Locator, str]] = []
    for index in range(count):
        locator = candidates.nth(index)
        try:
            if not await locator.is_visible(timeout=200):
                continue
            if not await locator.is_enabled(timeout=200):
                continue
            text = await _locator_text(locator)
            if text and text_matches(text, target, mode):
                matched.append((locator, text))
        except Exception:
            continue
    total = len(matched)
    results = []
    for locator, text in matched:
        results.append(
            MatchResult(
                locator=locator,
                frame_url=frame.url,
                text=text,
                total_matches=total,
            )
        )
    return results


async def find_matches(
    page: Page,
    target: str,
    mode: MatchMode,
) -> list[MatchResult]:
    results: list[MatchResult] = []
    for frame in list(page.frames):
        try:
            frame_results = await find_in_frame(frame, target, mode)
            results.extend(frame_results)
        except Exception:
            continue
    return results
