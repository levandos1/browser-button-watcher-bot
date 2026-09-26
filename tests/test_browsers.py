from pathlib import Path

from app.models import BrowserType
from browser.platforms import (
    BROWSER_NAMES,
    automation_profile_dir,
    browser_candidates,
)


def test_all_supported_browsers_have_names_and_candidates():
    for browser_type in BrowserType:
        assert browser_type in BROWSER_NAMES
        assert BROWSER_NAMES[browser_type]
        assert browser_candidates(browser_type)


def test_each_browser_uses_a_separate_automation_profile():
    profiles = [automation_profile_dir(browser_type) for browser_type in BrowserType]
    assert len({str(path).casefold() for path in profiles}) == len(BrowserType)
    assert all(isinstance(path, Path) for path in profiles)


def test_expected_windows_executables_are_present_in_candidates():
    joined = {
        browser_type: "|".join(str(path).lower() for path in browser_candidates(browser_type))
        for browser_type in BrowserType
    }
    assert "chrome.exe" in joined[BrowserType.CHROME]
    assert "msedge.exe" in joined[BrowserType.EDGE]
    assert "opera.exe" in joined[BrowserType.OPERA]
    assert "browser.exe" in joined[BrowserType.YANDEX]
