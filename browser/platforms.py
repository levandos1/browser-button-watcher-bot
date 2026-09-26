from __future__ import annotations

import os
import shutil
from pathlib import Path

from app.config import app_data_dir
from app.models import BrowserType


BROWSER_NAMES: dict[BrowserType, str] = {
    BrowserType.CHROME: "Google Chrome",
    BrowserType.EDGE: "Microsoft Edge",
    BrowserType.OPERA: "Opera",
    BrowserType.YANDEX: "Yandex Browser",
    BrowserType.CHROMIUM: "Chromium",
}


def browser_name(browser_type: BrowserType) -> str:
    return BROWSER_NAMES[browser_type]


def _env_path(variable: str, relative: str) -> Path | None:
    base = os.getenv(variable)
    return Path(base) / relative if base else None


def _dedupe(paths: list[Path | None]) -> list[Path]:
    result: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        if path is None:
            continue
        key = str(path).casefold()
        if key not in seen:
            result.append(path)
            seen.add(key)
    return result


def browser_candidates(browser_type: BrowserType) -> list[Path]:
    if browser_type == BrowserType.CHROME:
        return _dedupe([
            _env_path("PROGRAMFILES", "Google/Chrome/Application/chrome.exe"),
            _env_path("PROGRAMFILES(X86)", "Google/Chrome/Application/chrome.exe"),
            _env_path("LOCALAPPDATA", "Google/Chrome/Application/chrome.exe"),
        ])
    if browser_type == BrowserType.EDGE:
        return _dedupe([
            _env_path("PROGRAMFILES", "Microsoft/Edge/Application/msedge.exe"),
            _env_path("PROGRAMFILES(X86)", "Microsoft/Edge/Application/msedge.exe"),
            _env_path("LOCALAPPDATA", "Microsoft/Edge/Application/msedge.exe"),
        ])
    if browser_type == BrowserType.OPERA:
        return _dedupe([
            _env_path("LOCALAPPDATA", "Programs/Opera/opera.exe"),
            _env_path("LOCALAPPDATA", "Programs/Opera GX/opera.exe"),
            _env_path("PROGRAMFILES", "Opera/opera.exe"),
            _env_path("PROGRAMFILES", "Opera GX/opera.exe"),
        ])
    if browser_type == BrowserType.YANDEX:
        return _dedupe([
            _env_path("LOCALAPPDATA", "Yandex/YandexBrowser/Application/browser.exe"),
            _env_path("PROGRAMFILES", "Yandex/YandexBrowser/Application/browser.exe"),
            _env_path("PROGRAMFILES(X86)", "Yandex/YandexBrowser/Application/browser.exe"),
        ])
    return _dedupe([
        _env_path("LOCALAPPDATA", "Chromium/Application/chrome.exe"),
        _env_path("PROGRAMFILES", "Chromium/Application/chrome.exe"),
        _env_path("PROGRAMFILES(X86)", "Chromium/Application/chrome.exe"),
    ])


def executable_names(browser_type: BrowserType) -> tuple[str, ...]:
    mapping = {
        BrowserType.CHROME: ("chrome.exe", "chrome"),
        BrowserType.EDGE: ("msedge.exe", "msedge"),
        BrowserType.OPERA: ("opera.exe", "opera"),
        BrowserType.YANDEX: ("browser.exe",),
        BrowserType.CHROMIUM: ("chromium.exe", "chromium", "chrome.exe"),
    }
    return mapping[browser_type]


def discover_executable(browser_type: BrowserType) -> Path | None:
    for path in browser_candidates(browser_type):
        if path.exists():
            return path
    for name in executable_names(browser_type):
        found = shutil.which(name)
        if found:
            return Path(found)
    return None


def automation_profile_dir(browser_type: BrowserType) -> Path:
    # Preserve the original Chrome profile path for existing users.
    names = {
        BrowserType.CHROME: "browser-profile",
        BrowserType.EDGE: "browser-profile-edge",
        BrowserType.OPERA: "browser-profile-opera",
        BrowserType.YANDEX: "browser-profile-yandex",
        BrowserType.CHROMIUM: "browser-profile-chromium",
    }
    return app_data_dir() / names[browser_type]


def active_port_files(browser_type: BrowserType) -> list[Path]:
    files: list[Path | None] = [
        automation_profile_dir(browser_type) / "DevToolsActivePort"
    ]
    if browser_type == BrowserType.CHROME:
        files.append(_env_path("LOCALAPPDATA", "Google/Chrome/User Data/DevToolsActivePort"))
    elif browser_type == BrowserType.EDGE:
        files.append(_env_path("LOCALAPPDATA", "Microsoft/Edge/User Data/DevToolsActivePort"))
    elif browser_type == BrowserType.OPERA:
        files.extend([
            _env_path("APPDATA", "Opera Software/Opera Stable/DevToolsActivePort"),
            _env_path("APPDATA", "Opera Software/Opera GX Stable/DevToolsActivePort"),
        ])
    elif browser_type == BrowserType.YANDEX:
        files.append(_env_path("LOCALAPPDATA", "Yandex/YandexBrowser/User Data/DevToolsActivePort"))
    else:
        files.append(_env_path("LOCALAPPDATA", "Chromium/User Data/DevToolsActivePort"))
    return _dedupe(files)
