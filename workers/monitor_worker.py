from __future__ import annotations

import asyncio
import logging
import threading
from datetime import datetime
from urllib.parse import urlparse

from PySide6.QtCore import QThread, Signal

from app.models import AppState, BrowserType, MonitorSettings
from browser.clicker import click_match
from browser.detector import find_matches
from browser.manager import BrowserManager

LOGGER = logging.getLogger(__name__)


class BrowserWorker(QThread):
    """Run all Playwright operations on a dedicated asyncio event loop."""

    state_changed = Signal(str)
    tabs_updated = Signal(object)
    log_message = Signal(str, str)
    error_occurred = Signal(str)
    metrics_updated = Signal(object)
    endpoint_detected = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.loop: asyncio.AbstractEventLoop | None = None
        self.manager = BrowserManager()
        self.monitor_task: asyncio.Task | None = None
        self._ready = threading.Event()
        self._settings: MonitorSettings | None = None
        self._cooldown_until = 0.0
        self._checks = 0
        self._detections = 0
        self._clicks = 0
        self._errors = 0
        self._started_at: datetime | None = None
        self._last_url = ""

    def run(self) -> None:
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self._ready.set()
        try:
            self.loop.run_forever()
        finally:
            pending = asyncio.all_tasks(self.loop)
            for task in pending:
                task.cancel()
            if pending:
                self.loop.run_until_complete(
                    asyncio.gather(*pending, return_exceptions=True)
                )
            self.loop.run_until_complete(
                self.manager.disconnect(close_launched_browser=False)
            )
            self.loop.close()

    def _submit(self, coro) -> None:
        if not self.isRunning():
            self.start()
        self._ready.wait(3)
        if not self.loop:
            self.error_occurred.emit("Background worker failed to start.")
            return
        asyncio.run_coroutine_threadsafe(coro, self.loop)

    def connect_browser(self, endpoint: str, browser_type: BrowserType) -> None:
        self._submit(self._connect(endpoint, browser_type))

    async def _connect(self, endpoint: str, browser_type: BrowserType) -> None:
        try:
            try:
                tabs = await self.manager.connect(endpoint)
                active_endpoint = endpoint
            except Exception as first_error:
                discovered = await self.manager.discover_debug_endpoint(endpoint, browser_type)
                if not discovered:
                    raise RuntimeError(
                        "No debugging endpoint was found for the selected browser. "
                        "A normal browser session cannot be attached retroactively; "
                        "start it with remote debugging or use LAUNCH BROWSER."
                    ) from first_error
                tabs = await self.manager.connect(discovered)
                active_endpoint = discovered
                self._log("INFO", f"Auto-detected browser debugging endpoint: {discovered}")
            self.endpoint_detected.emit(active_endpoint)
            self.state_changed.emit(AppState.CONNECTED.value)
            self.tabs_updated.emit(tabs)
            self._log("INFO", f"Connected to browser; found {len(tabs)} tab(s)")
        except Exception as exc:
            self._fail(f"Browser connection failed: {exc}")

    def launch_browser(self, endpoint: str, browser_type: BrowserType) -> None:
        self._submit(self._launch_browser(endpoint, browser_type))

    async def _launch_browser(self, endpoint: str, browser_type: BrowserType) -> None:
        try:
            parsed = urlparse(endpoint)
            port = parsed.port or 9222
            executable = self.manager.launch_dedicated_browser(browser_type, port=port)
            self._log("INFO", f"Launched dedicated browser: {executable.name}")
            tabs = await self.manager.wait_until_connectable(endpoint)
            self.state_changed.emit(AppState.CONNECTED.value)
            self.tabs_updated.emit(tabs)
            self._log("INFO", f"Connected; found {len(tabs)} tab(s)")
        except Exception as exc:
            self._fail(f"Could not launch automation browser: {exc}")

    def refresh_tabs(self) -> None:
        self._submit(self._refresh_tabs())

    async def _refresh_tabs(self) -> None:
        try:
            tabs = await self.manager.list_tabs()
            self.tabs_updated.emit(tabs)
            self._log("INFO", f"Refreshed tabs: {len(tabs)} found")
        except Exception as exc:
            self._fail(f"Could not refresh tabs: {exc}")

    def select_tab(self, key: str) -> None:
        self._submit(self._select_tab(key))

    async def _select_tab(self, key: str) -> None:
        try:
            self.manager.select_tab(key)
            page = self.manager.selected_page
            self._last_url = page.url if page else ""
            self.state_changed.emit(AppState.READY.value)
            self._log("INFO", f"Target tab selected: {self._last_url}")
        except Exception as exc:
            self._fail(str(exc))

    def start_monitoring(self, settings: MonitorSettings) -> None:
        self._settings = settings
        self._submit(self._start_monitoring())

    async def _start_monitoring(self) -> None:
        if self.monitor_task and not self.monitor_task.done():
            return
        if not self.manager.selected_page:
            self._fail("Select a target tab before monitoring.")
            return
        self._cooldown_until = 0.0
        self._checks = 0
        self._detections = 0
        self._clicks = 0
        self._errors = 0
        self._started_at = datetime.now()
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        self.state_changed.emit(AppState.MONITORING.value)
        assert self._settings is not None
        self._log("MONITOR", f'Monitoring for "{self._settings.target_text}"')

    def stop_monitoring(self) -> None:
        if not self.loop:
            return
        self.loop.call_soon_threadsafe(self._cancel_monitor)

    def _cancel_monitor(self) -> None:
        if self.monitor_task and not self.monitor_task.done():
            self.monitor_task.cancel()

    async def _monitor_loop(self) -> None:
        assert self._settings is not None
        settings = self._settings
        try:
            while True:
                page = self.manager.selected_page
                if not page or page.is_closed():
                    raise RuntimeError("Target tab was closed.")
                if page.url != self._last_url:
                    self._last_url = page.url
                    self._log("INFO", f"Navigation detected: {self._last_url}")

                matches = await find_matches(
                    page, settings.target_text, settings.match_mode
                )
                self._checks += 1
                now = asyncio.get_running_loop().time()

                if not matches or now < self._cooldown_until:
                    self._emit_metrics()
                    await asyncio.sleep(settings.interval_ms / 1000)
                    continue

                first = matches[0]
                self._detections += 1
                self._log(
                    "DETECTED",
                    f'{len(matches)} matching element(s); "{first.text}"',
                )
                try:
                    await click_match(first)
                except Exception as exc:
                    self._errors += 1
                    self._log("WARNING", str(exc))
                else:
                    self._clicks += 1
                    self._cooldown_until = (
                        asyncio.get_running_loop().time() + settings.cooldown_seconds
                    )
                    self._log("CLICKED", "Browser-level click successful")

                self._emit_metrics()
                await asyncio.sleep(settings.interval_ms / 1000)

        except asyncio.CancelledError:
            self._log("INFO", "Monitoring stopped")
        except Exception as exc:
            self._errors += 1
            self._fail(str(exc))
        finally:
            self.monitor_task = None
            if self.manager.browser:
                self.state_changed.emit(AppState.READY.value)
            else:
                self.state_changed.emit(AppState.DISCONNECTED.value)
            self._emit_metrics()

    def shutdown(self, close_launched_browser: bool) -> None:
        if not self.loop:
            return
        future = asyncio.run_coroutine_threadsafe(
            self.manager.disconnect(
                close_launched_browser=close_launched_browser,
            ),
            self.loop,
        )
        try:
            future.result(timeout=5)
        except Exception:
            pass
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.wait(5000)

    def _fail(self, message: str) -> None:
        LOGGER.error(message)
        self._errors += 1
        self.state_changed.emit(AppState.ERROR.value)
        self.error_occurred.emit(message)
        self._log("ERROR", message)
        self._emit_metrics()

    def _log(self, level: str, message: str) -> None:
        LOGGER.info("%s %s", level, message)
        self.log_message.emit(level, message)

    def _emit_metrics(self) -> None:
        runtime = 0
        if self._started_at:
            runtime = int((datetime.now() - self._started_at).total_seconds())
        self.metrics_updated.emit({
            "runtime": runtime,
            "checks": self._checks,
            "detections": self._detections,
            "clicks": self._clicks,
            "errors": self._errors,
        })
