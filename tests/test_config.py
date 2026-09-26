from app.config import AppConfig
from app.models import BrowserType


def test_config_defaults_are_valid():
    cfg = AppConfig()
    assert cfg.endpoint.startswith("http://127.0.0.1:")
    assert 100 <= cfg.interval_ms <= 5000
    assert 0.5 <= cfg.cooldown_seconds <= 60.0
    assert cfg.language in {"en", "ru"}
    assert cfg.browser_type == BrowserType.CHROME.value
