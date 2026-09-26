import asyncio
import shutil
import subprocess
import tempfile
from pathlib import Path

from app.models import MatchMode, MonitorSettings
from browser.clicker import click_match
from browser.detector import find_matches
from browser.manager import BrowserManager
from workers.monitor_worker import BrowserWorker

CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
ENDPOINT = "http://127.0.0.1:9333"


async def main():
    profile = tempfile.mkdtemp(prefix="button-watcher-smoke-")
    proc = subprocess.Popen([
        str(CHROME),
        "--headless=new",
        "--remote-debugging-port=9333",
        "--remote-debugging-address=127.0.0.1",
        f"--user-data-dir={profile}",
        "--no-first-run",
        "--no-default-browser-check",
    ])
    manager = BrowserManager()
    try:
        tabs = await manager.wait_until_connectable(ENDPOINT, timeout=10)
        if not tabs:
            raise RuntimeError("Chrome exposed no tabs")
        discovered = await manager.discover_debug_endpoint("http://127.0.0.1:9999")
        if discovered != ENDPOINT:
            raise RuntimeError(f"Auto-discovery failed: {discovered}")
        manager.select_tab(tabs[0].key)
        page = manager.selected_page
        fixture = Path(__file__).with_name("test_page.html").resolve().as_uri()
        await page.goto(fixture)
        await page.evaluate(
            "document.getElementById('immediate').addEventListener('click', "
            "() => window.__clicked = 1)"
        )
        matches = await find_matches(page, "Я тут", MatchMode.EXACT)
        if len(matches) < 2:
            raise RuntimeError(f"Expected main+iframe matches, got {len(matches)}")
        await click_match(matches[0])
        clicked = await page.evaluate("window.__clicked === 1")
        if not clicked:
            raise RuntimeError("Browser-level click did not fire page handler")
        await page.evaluate("window.__repeatClicks = 0; "
                           "document.getElementById('immediate').onclick = "
                           "() => window.__repeatClicks++")
        worker = BrowserWorker()
        worker.manager = manager
        worker._settings = MonitorSettings(
            target_text="Я тут", match_mode=MatchMode.EXACT,
            interval_ms=100, cooldown_seconds=0.5
        )
        worker._last_url = page.url
        task = asyncio.create_task(worker._monitor_loop())
        await asyncio.sleep(1.35)
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        repeat_clicks = await page.evaluate("window.__repeatClicks")
        if repeat_clicks < 2:
            raise RuntimeError(f"Expected repeated clicks, got {repeat_clicks}")
        print(
            f"INTEGRATION_OK matches={len(matches)} click={clicked} "
            f"repeat_clicks={repeat_clicks} discovery={discovered}"
        )
    finally:
        await manager.disconnect(close_launched_browser=False)
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        shutil.rmtree(profile, ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(main())
