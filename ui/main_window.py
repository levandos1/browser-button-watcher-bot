from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QGraphicsOpacityEffect,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.config import AppConfig
from app.constants import MAX_LOG_LINES
from app.models import AppState, MatchMode, MonitorSettings, TabInfo
from workers.monitor_worker import BrowserWorker
from ui.widgets import AnimatedButton
from ui.theme import resource_path


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.config = AppConfig.load()
        self.worker = BrowserWorker()
        self.tabs: list[TabInfo] = []
        self.state = AppState.DISCONNECTED
        self.setWindowTitle("ButtonWatcher")
        self.setWindowIcon(QIcon(str(resource_path("resources/icon.ico"))))
        self.resize(self.config.window_width, self.config.window_height)
        self._build_ui()
        self._bind_worker()
        self._apply_config()
        self._update_controls()

    def _build_ui(self) -> None:
        root = QWidget()
        self.root_widget = root
        layout = QVBoxLayout(root)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("BUTTON WATCHER")
        title.setStyleSheet("font-size: 16pt; font-weight: 700;")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(QLabel("v1.0"))
        layout.addLayout(header)

        browser_box = QGroupBox("BROWSER")
        self.browser_box = browser_box
        browser_grid = QGridLayout(browser_box)
        self.status_label = QLabel("● DISCONNECTED")
        self.status_label.setObjectName("status")
        self.endpoint_edit = QLineEdit()
        self.connect_button = AnimatedButton("CONNECT")
        self.launch_button = AnimatedButton("LAUNCH BROWSER")
        self.refresh_button = AnimatedButton("REFRESH TABS")
        browser_grid.addWidget(QLabel("Status"), 0, 0)
        browser_grid.addWidget(self.status_label, 0, 1, 1, 3)
        browser_grid.addWidget(QLabel("Endpoint"), 1, 0)
        browser_grid.addWidget(self.endpoint_edit, 1, 1, 1, 3)
        browser_grid.addWidget(self.connect_button, 2, 1)
        browser_grid.addWidget(self.launch_button, 2, 2)
        browser_grid.addWidget(self.refresh_button, 2, 3)
        layout.addWidget(browser_box)

        target_box = QGroupBox("TARGET")
        self.target_box = target_box
        target_form = QFormLayout(target_box)
        self.tab_combo = QComboBox()
        self.tab_url = QLabel("No target tab selected")
        self.tab_url.setObjectName("muted")
        self.tab_url.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.target_edit = QLineEdit()
        self.target_edit.setPlaceholderText("Enter button text...")
        self.match_combo = QComboBox()
        for mode in MatchMode:
            self.match_combo.addItem(mode.value, mode)
        target_form.addRow("Target tab", self.tab_combo)
        target_form.addRow("", self.tab_url)
        target_form.addRow("Button text", self.target_edit)
        target_form.addRow("Match mode", self.match_combo)
        layout.addWidget(target_box)

        settings_box = QGroupBox("SETTINGS")
        self.settings_box = settings_box
        settings_form = QFormLayout(settings_box)
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(100, 5000)
        self.interval_spin.setSuffix(" ms")
        self.interval_spin.setSingleStep(100)
        self.interval_spin.setButtonSymbols(QSpinBox.ButtonSymbols.PlusMinus)
        self.cooldown_spin = QDoubleSpinBox()
        self.cooldown_spin.setRange(0.5, 60.0)
        self.cooldown_spin.setSingleStep(0.5)
        self.cooldown_spin.setSuffix(" sec")
        self.cooldown_spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.PlusMinus)
        self.close_browser_check = QCheckBox(
            "Close dedicated automation browser on app exit"
        )
        settings_form.addRow("Check interval", self.interval_spin)
        settings_form.addRow("Click cooldown", self.cooldown_spin)
        settings_form.addRow("", self.close_browser_check)
        layout.addWidget(settings_box)

        controls = QHBoxLayout()
        self.start_button = AnimatedButton("START MONITORING")
        self.start_button.setObjectName("primaryButton")
        self.stop_button = AnimatedButton("STOP")
        self.stop_button.setObjectName("dangerButton")
        controls.addWidget(self.start_button)
        controls.addWidget(self.stop_button)
        controls.addStretch()
        self.metrics_label = QLabel(
            "Runtime 00:00:00  Checks 0  Detections 0  Clicks 0  Errors 0"
        )
        self.metrics_label.setObjectName("muted")
        controls.addWidget(self.metrics_label)
        layout.addLayout(controls)

        log_box = QGroupBox("LOG")
        self.log_box = log_box
        log_layout = QVBoxLayout(log_box)
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.document().setMaximumBlockCount(MAX_LOG_LINES)
        clear_button = AnimatedButton("CLEAR LOG")
        clear_button.clicked.connect(self.log_view.clear)
        log_layout.addWidget(self.log_view, 1)
        log_layout.addWidget(clear_button, 0, Qt.AlignRight)
        layout.addWidget(log_box, 1)
        self.setCentralWidget(root)

        self.connect_button.clicked.connect(self._connect)
        self.launch_button.clicked.connect(self._launch)
        self.refresh_button.clicked.connect(self.worker.refresh_tabs)
        self.tab_combo.currentIndexChanged.connect(self._select_tab)
        self.start_button.clicked.connect(self._start)
        self.stop_button.clicked.connect(self.worker.stop_monitoring)
        self.target_edit.textChanged.connect(self._update_controls)
        QShortcut(QKeySequence("Ctrl+R"), self, activated=self.worker.refresh_tabs)
        QShortcut(QKeySequence("Ctrl+S"), self, activated=self._start)
        QShortcut(
            QKeySequence("Ctrl+Shift+S"),
            self,
            activated=self.worker.stop_monitoring,
        )

    def _bind_worker(self) -> None:
        self.worker.state_changed.connect(self._set_state)
        self.worker.tabs_updated.connect(self._set_tabs)
        self.worker.log_message.connect(self._append_log)
        self.worker.error_occurred.connect(self._show_error)
        self.worker.metrics_updated.connect(self._set_metrics)
        self.worker.endpoint_detected.connect(self.endpoint_edit.setText)

    def _apply_config(self) -> None:
        self.endpoint_edit.setText(self.config.endpoint)
        self.target_edit.setText(self.config.target_text)
        index = self.match_combo.findText(self.config.match_mode)
        self.match_combo.setCurrentIndex(max(0, index))
        self.interval_spin.setValue(self.config.interval_ms)
        self.cooldown_spin.setValue(self.config.cooldown_seconds)
        self.close_browser_check.setChecked(
            self.config.close_launched_browser_on_exit
        )

    def _connect(self) -> None:
        self.worker.connect_browser(self.endpoint_edit.text().strip())

    def _launch(self) -> None:
        self.worker.launch_browser(self.endpoint_edit.text().strip())

    def _select_tab(self, index: int) -> None:
        if index < 0 or index >= len(self.tabs):
            self.tab_url.setText("No target tab selected")
            self._update_controls()
            return
        tab = self.tabs[index]
        self.tab_url.setText(tab.url)
        self.worker.select_tab(tab.key)

    def _start(self) -> None:
        text = self.target_edit.text().strip()
        if not text:
            QMessageBox.warning(
                self,
                "ButtonWatcher",
                "Target button text cannot be empty.",
            )
            return
        if self.tab_combo.currentIndex() < 0:
            QMessageBox.warning(
                self,
                "ButtonWatcher",
                "Select a target tab first.",
            )
            return
        settings = MonitorSettings(
            target_text=text,
            match_mode=self.match_combo.currentData(),
            interval_ms=self.interval_spin.value(),
            cooldown_seconds=self.cooldown_spin.value(),
        )
        self.worker.start_monitoring(settings)

    def _set_tabs(self, tabs: list[TabInfo]) -> None:
        previous_key = None
        current = self.tab_combo.currentIndex()
        if 0 <= current < len(self.tabs):
            previous_key = self.tabs[current].key
        self.tabs = tabs
        self.tab_combo.blockSignals(True)
        self.tab_combo.clear()
        restore = -1
        for i, tab in enumerate(tabs):
            self.tab_combo.addItem(f"{tab.title}  —  {tab.url}")
            if tab.key == previous_key:
                restore = i
        self.tab_combo.setCurrentIndex(restore)
        self.tab_combo.blockSignals(False)
        if restore < 0:
            self.tab_url.setText("No target tab selected")
        else:
            self.tab_url.setText(tabs[restore].url)
            self.worker.select_tab(tabs[restore].key)
        self._update_controls()

    def _set_state(self, value: str) -> None:
        try:
            self.state = AppState(value)
        except ValueError:
            self.state = AppState.ERROR
        colors = {
            AppState.DISCONNECTED: "#8b949e",
            AppState.CONNECTED: "#3fb950",
            AppState.READY: "#58a6ff",
            AppState.MONITORING: "#3fb950",
            AppState.STOPPING: "#d29922",
            AppState.ERROR: "#f85149",
        }
        self.status_label.setText(f"● {self.state.value}")
        self.status_label.setStyleSheet(
            f"color: {colors[self.state]}; font-weight: 700;"
        )
        self._update_controls()

    def _update_controls(self) -> None:
        connected = self.state in {
            AppState.CONNECTED,
            AppState.READY,
            AppState.MONITORING,
        }
        monitoring = self.state == AppState.MONITORING
        has_tab = self.tab_combo.currentIndex() >= 0
        has_text = bool(self.target_edit.text().strip())
        self.refresh_button.setEnabled(connected and not monitoring)
        self.tab_combo.setEnabled(connected and not monitoring)
        self.target_edit.setEnabled(not monitoring)
        self.match_combo.setEnabled(not monitoring)
        self.interval_spin.setEnabled(not monitoring)
        self.cooldown_spin.setEnabled(not monitoring)
        self.start_button.setEnabled(
            self.state == AppState.READY and has_tab and has_text
        )
        self.stop_button.setEnabled(monitoring)
        self.connect_button.setEnabled(not monitoring)
        self.launch_button.setEnabled(not monitoring)
        self._apply_monitoring_visuals(monitoring)

    def _apply_monitoring_visuals(self, monitoring: bool) -> None:
        self.start_button.setProperty("monitoringActive", monitoring)
        self.stop_button.setProperty("monitoringActive", monitoring)
        self.start_button.setText("MONITORING ACTIVE" if monitoring else "START MONITORING")
        self.stop_button.setText("STOP MONITORING" if monitoring else "STOP")
        for button in (self.start_button, self.stop_button):
            button.style().unpolish(button)
            button.style().polish(button)

        panels = (self.browser_box, self.target_box, self.settings_box, self.log_box)
        if not hasattr(self, "_panel_effects"):
            self._panel_effects = []
            for panel in panels:
                effect = QGraphicsOpacityEffect(panel)
                panel.setGraphicsEffect(effect)
                self._panel_effects.append(effect)
        opacity = 0.52 if monitoring else 1.0
        for effect in self._panel_effects:
            effect.setOpacity(opacity)

    def _append_log(self, level: str, message: str) -> None:
        stamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.log_view.appendPlainText(f"{stamp}  {level:<9} {message}")
        bar = self.log_view.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _show_error(self, message: str) -> None:
        if self.isVisible():
            QMessageBox.warning(self, "ButtonWatcher", message)

    def _set_metrics(self, metrics: dict) -> None:
        sec = metrics["runtime"]
        hours, rem = divmod(sec, 3600)
        minutes, seconds = divmod(rem, 60)
        self.metrics_label.setText(
            f"Runtime {hours:02}:{minutes:02}:{seconds:02}  "
            f"Checks {metrics['checks']:,}  "
            f"Detections {metrics['detections']:,}  "
            f"Clicks {metrics['clicks']:,}  "
            f"Errors {metrics['errors']:,}"
        )

    def closeEvent(self, event: QCloseEvent) -> None:
        self.config.endpoint = self.endpoint_edit.text().strip()
        self.config.target_text = self.target_edit.text()
        self.config.match_mode = self.match_combo.currentText()
        self.config.interval_ms = self.interval_spin.value()
        self.config.cooldown_seconds = self.cooldown_spin.value()
        self.config.close_launched_browser_on_exit = (
            self.close_browser_check.isChecked()
        )
        self.config.window_width = self.width()
        self.config.window_height = self.height()
        self.config.save()
        self.worker.stop_monitoring()
        self.worker.shutdown(self.close_browser_check.isChecked())
        event.accept()
