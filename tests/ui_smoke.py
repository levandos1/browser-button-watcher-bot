import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QAbstractAnimation
from PySide6.QtWidgets import QApplication, QAbstractSpinBox

from app.models import AppState
from ui.main_window import MainWindow
from ui.widgets import AnimatedButton

app = QApplication.instance() or QApplication([])
window = MainWindow()
assert not window.windowIcon().isNull(), "window icon is null"
assert window.interval_spin.buttonSymbols() == QAbstractSpinBox.ButtonSymbols.PlusMinus
assert window.cooldown_spin.buttonSymbols() == QAbstractSpinBox.ButtonSymbols.PlusMinus
window._set_state(AppState.MONITORING.value)
assert window.start_button.property("monitoringActive") is True
assert window.stop_button.property("monitoringActive") is True
assert window.start_button.text() == "MONITORING ACTIVE"
assert window.stop_button.text() == "STOP MONITORING"
assert all(abs(effect.opacity() - 0.52) < 0.01 for effect in window._panel_effects)
button = AnimatedButton("TEST")
button.click()
assert button._animation.state() == QAbstractAnimation.State.Running
print("UI_SMOKE_OK icon spinboxes monitoring_visuals click_animation")
window.close()
