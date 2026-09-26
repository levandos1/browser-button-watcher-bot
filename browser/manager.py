from __future__ import annotations

import asyncio
import logging
import os
import shutil
import subprocess
import json
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import Browser, Playwright, async_playwright

from app.config import app_data_dir
from app.constants import LOCALHOST_HOSTS
from app.models import TabInfo

LOGGER = logging.getLogger(__name__)


class BrowserManager:
    """Own Playwright/CDP objects inside the background worker thread."""

    def __init__(self) -> None:
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.pages: dict[str, object] = {}
        self.selected_page = None
        self.launched_process: subprocess.Popen | None = None

    async def connect(self, endpoint: str) -> list[TabInfo]:
        self._validate_local_endpoint(endpoint)
        await self.disconnect(close_launched_browser=False)
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.connect_over_cdp(endpoint)
        return await self.list_tabs()

    async def disconnect(self, close_launched_browser: bool = False) -> None:
        self.selected_page = None
        self.pages.clear()
        # A CDP connection may point at a browser we did not launch.
        # Never send Browser.close() to an arbitrary attached browser.
        self.browser = None
        if self.playwright:
            try:
                await self.playwright.stop()
            except Exception:
                LOGGER.debug("Playwright stop failed", exc_info=True)
            self.playwright = None
        if close_launched_browser:
            self.close_launched_browser()

    async def list_tabs(self) -> list[TabInfo]:
        if not self.browser:
            raise RuntimeError("Browser is not connected.")
        self.pages.clear()
        result: list[TabInfo] = []
        for context in self.browser.contexts:
            for page in context.pages:
                key = str(id(page))
                self.pages[key] = page
                try:
                    title = await page.title()
                except Exception:
                    title = "(untitled)"
                result.append(TabInfo(key=key, title=title or "(untitled)", url=page.url))
        return result

    def select_tab(self, key: str) -> None:
        page = self.pages.get(key)
        if page is None:
            raise RuntimeError("Selected tab is no longer available.")
        self.selected_page = page

    @staticmethod
    def discover_browser() -> Path | None:
        candidates: list[Path] = []
        local = os.getenv("LOCALAPPDATA")
        program_files = os.getenv("PROGRAMFILES")
        program_files_x86 = os.getenv("PROGRAMFILES(X86)")
        if program_files:
            candidates.extend([
                Path(program_files) / "Google/Chrome/Application/chrome.exe",
                Path(program_files) / "Microsoft/Edge/Application/msedge.exe",
            ])
        if program_files_x86:
            candidates.extend([
                Path(program_files_x86) / "Google/Chrome/Application/chrome.exe",
                Path(program_files_x86) / "Microsoft/Edge/Application/msedge.exe",
            ])
        if local:
            candidates.extend([
                Path(local) / "Google/Chrome/Application/chrome.exe",
                Path(local) / "Microsoft/Edge/Application/msedge.exe",
                Path(local) / "Chromium/Application/chrome.exe",
            ])
        for name in ("chrome.exe", "msedge.exe", "chromium.exe"):
            found = shutil.which(name)
            if found:
                candidates.append(Path(found))
        return next((path for path in candidates if path.exists()), None)

    def launch_dedicated_browser(self, port: int = 9222) -> Path:
        executable = self.discover_browser()
        if not executable:
            raise RuntimeError("Chrome, Edge, or Chromium was not found.")
        profile = app_data_dir() / "browser-profile"
        profile.mkdir(parents=True, exist_ok=True)
        args = [
            str(executable),
            f"--remote-debugging-port={port}",
            "--remote-debugging-address=127.0.0.1",
            f"--user-data-dir={profile}",
            "--no-first-run",
            "--no-default-browser-check",
        ]
        self.launched_process = subprocess.Popen(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return executable

    async def wait_until_connectable(
        self,
        endpoint: str,
        timeout: float = 12.0,
    ) -> list[TabInfo]:
        deadline = asyncio.get_running_loop().time() + timeout
        last_error: Exception | None = None
        while asyncio.get_running_loop().time() < deadline:
            try:
                return await self.connect(endpoint)
            except Exception as exc:
                last_error = exc
                await asyncio.sleep(0.4)
        raise RuntimeError(f"Browser did not become available: {last_error}")

    async def discover_debug_endpoint(self, preferred: str | None = None) -> str | None:
        """Find a locally running Chromium CDP endpoint without touching normal Chrome."""
        ports: list[int] = []
        if preferred:
            try:
                port = urlparse(preferred).port
                if port:
                    ports.append(port)
            except ValueError:
                pass

        # Chrome writes DevToolsActivePort for profiles launched with remote debugging.
        local = os.getenv("LOCALAPPDATA")
        active_files = [app_data_dir() / "browser-profile" / "DevToolsActivePort"]
        if local:
            active_files.extend([
                Path(local) / "Google/Chrome/User Data/DevToolsActivePort",
                Path(local) / "Microsoft/Edge/User Data/DevToolsActivePort",
                Path(local) / "Chromium/User Data/DevToolsActivePort",
            ])
        for active_file in active_files:
            try:
                value = int(active_file.read_text(encoding="utf-8").splitlines()[0])
                ports.append(value)
            except (OSError, ValueError, IndexError):
                pass

        ports.extend(range(9222, 9233))
        ports.extend([9333, 9515])
        seen: set[int] = set()
        for port in ports:
            if port in seen:
                continue
            seen.add(port)
            endpoint = f"http://127.0.0.1:{port}"
            if await asyncio.to_thread(self._is_cdp_endpoint, endpoint):
                return endpoint
        return None

    @staticmethod
    def _is_cdp_endpoint(endpoint: str) -> bool:
        try:
            with urllib.request.urlopen(endpoint + "/json/version", timeout=0.18) as response:
                payload = json.loads(response.read().decode("utf-8", errors="replace"))
            return bool(payload.get("webSocketDebuggerUrl"))
        except Exception:
            return False

    def close_launched_browser(self) -> None:
        if self.launched_process and self.launched_process.poll() is None:
            self.launched_process.terminate()
        self.launched_process = None

    @staticmethod
    def _validate_local_endpoint(endpoint: str) -> None:
        parsed = urlparse(endpoint)
        if parsed.scheme not in {"http", "https", "ws", "wss"}:
            raise ValueError("Debug endpoint must be an http(s) or ws(s) URL.")
        if parsed.hostname not in LOCALHOST_HOSTS:
            raise ValueError("Debug endpoint must use localhost/127.0.0.1.")
