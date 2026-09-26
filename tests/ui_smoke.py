import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QAbstractAnimation
from PySide6.QtWidgets import QApplication

from app.models import AppState, BrowserType, MatchMode
from ui.main_window import MainWindow
from ui.widgets import AnimatedButton

app = QApplication.instance() or QApplication([])
window = MainWindow()
original_language = window.language
assert not window.windowIcon().isNull(), "window icon is null"
assert window.browser_combo.count() == len(BrowserType)
assert window.browser_combo.findData(BrowserType.CHROME) >= 0
assert window.browser_combo.findData(BrowserType.EDGE) >= 0
assert window.browser_combo.findData(BrowserType.OPERA) >= 0
assert window.browser_combo.findData(BrowserType.YANDEX) >= 0
window.interval_spin.setValue(100)
window.interval_spin._up_button.click()
assert window.interval_spin.value() == 200
window.interval_spin._down_button.click()
assert window.interval_spin.value() == 100
window.cooldown_spin.setValue(0.5)
window.cooldown_spin._up_button.click()
assert abs(window.cooldown_spin.value() - 1.0) < 1e-9
window.cooldown_spin._down_button.click()
assert abs(window.cooldown_spin.value() - 0.5) < 1e-9

window._set_language("ru", persist=False)
assert window.browser_box.title() == "БРАУЗЕР"
assert window.settings_box.title() == "НАСТРОЙКИ"
assert window.language_button.text() == "EN"
assert "Точное" in window.match_combo.itemText(window.match_combo.findData(MatchMode.EXACT))

window._set_state(AppState.MONITORING.value)
assert window.start_button.property("monitoringActive") is True
assert window.stop_button.property("monitoringActive") is True
assert window.start_button.text() == "МОНИТОРИНГ АКТИВЕН"
assert window.stop_button.text() == "ОСТАНОВИТЬ МОНИТОРИНГ"
assert all(abs(effect.opacity() - 0.52) < 0.01 for effect in window._panel_effects)

window._set_language("en", persist=False)
assert window.browser_box.title() == "BROWSER"
assert window.language_button.text() == "RU"
assert window.start_button.text() == "MONITORING ACTIVE"

button = AnimatedButton("TEST")
button.click()
assert button._animation.state() == QAbstractAnimation.State.Running
print("UI_SMOKE_OK icon custom_step_buttons i18n monitoring_visuals click_animation")
window._set_language(original_language, persist=False)
window.close()
