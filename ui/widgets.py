from __future__ import annotations

from PySide6.QtCore import QEasingCurve, Qt, QVariantAnimation
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QPushButton


class AnimatedButton(QPushButton):
    """Push button with a short visual pulse on every mouse click."""

    def __init__(self, text: str = "", parent=None) -> None:
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._pulse = 0.0
        self._animation = QVariantAnimation(self)
        self._animation.setDuration(190)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._animation.setKeyValueAt(0.0, 0.0)
        self._animation.setKeyValueAt(0.28, 1.0)
        self._animation.setKeyValueAt(1.0, 0.0)
        self._animation.valueChanged.connect(self._set_pulse)
        self.pressed.connect(self._start_pulse)

    def _start_pulse(self) -> None:
        self._animation.stop()
        self._animation.start()

    def _set_pulse(self, value: object) -> None:
        self._pulse = float(value)
        self.update()
    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        if self._pulse <= 0.01 or not self.isEnabled():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor("#ffffff")
        color.setAlphaF(min(0.34, 0.34 * self._pulse))
        pen = QPen(color, 2 + 2 * self._pulse)
        painter.setPen(pen)
        inset = int(2 + (1.0 - self._pulse) * 5)
        painter.drawRoundedRect(
            self.rect().adjusted(inset, inset, -inset, -inset),
            5,
            5,
        )
