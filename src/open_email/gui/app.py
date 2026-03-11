"""Main GUI application: MainWindow, QSystemTrayIcon, tab container."""

import logging
import sys

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QAction, QIcon, QPixmap, QPainter, QColor, QFont
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QMenu, QSystemTrayIcon, QTabWidget,
)

from open_email.agent_core import AgentConfig, AgentCore
from open_email.gui.agent_thread import AgentThread
from open_email.gui.tabs.accounts import AccountsTab
from open_email.gui.tabs.dashboard import DashboardTab
from open_email.gui.tabs.logs import LogsTab
from open_email.gui.tabs.rules import RulesTab
from open_email.gui.tabs.settings import SettingsTab
from open_email.gui.tabs.activity import ActivityTab
from open_email.gui.widgets.log_handler import QtLogHandler
from open_email.gui.widgets.ui_helpers import GLOBAL_STYLE

logger = logging.getLogger("open_email")


def _create_app_icon() -> QIcon:
    """Create a simple programmatic icon (envelope)."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(52, 120, 246))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(4, 14, 56, 40, 6, 6)
    painter.setPen(QColor(255, 255, 255))
    painter.setFont(QFont("Arial", 22, QFont.Weight.Bold))
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "@")
    painter.end()
    return QIcon(pixmap)


class MainWindow(QMainWindow):
    """Main application window with tabs and system tray."""

    def __init__(self, config: AgentConfig, minimized: bool = False):
        super().__init__()
        self.config = config
        self._agent_core = AgentCore(config)
        self._agent_thread: AgentThread | None = None
        self._really_quit = False

        self.setWindowTitle("InboxAgent")
        self.setMinimumSize(QSize(800, 600))
        self.setWindowIcon(_create_app_icon())

        # Log handler for GUI
        self._log_handler = QtLogHandler()
        logging.getLogger("open_email").addHandler(self._log_handler)

        # Tabs
        self._tabs = QTabWidget()
        self.setCentralWidget(self._tabs)

        self._dashboard_tab = DashboardTab(self._agent_core, self)
        self._accounts_tab = AccountsTab(self._agent_core, self)
        self._rules_tab = RulesTab(self._agent_core, self)
        self._activity_tab = ActivityTab(self._agent_core, self)
        self._logs_tab = LogsTab(self._log_handler, self)
        self._settings_tab = SettingsTab(self._agent_core, self)

        self._tabs.addTab(self._dashboard_tab, "Dashboard")
        self._tabs.addTab(self._accounts_tab, "Accounts")
        self._tabs.addTab(self._rules_tab, "Rules")
        self._tabs.addTab(self._activity_tab, "Activity")
        self._tabs.addTab(self._logs_tab, "Logs")
        self._tabs.addTab(self._settings_tab, "Settings")

        # Connect dashboard start/stop
        self._dashboard_tab.start_requested.connect(self._start_agent)
        self._dashboard_tab.stop_requested.connect(self._stop_agent)

        # Connect settings changes
        self._settings_tab.config_changed.connect(self._on_config_changed)

        # System tray
        self._setup_tray()

        if minimized:
            self.hide()
        else:
            self.show()

    def _setup_tray(self):
        """Set up the system tray icon and menu."""
        self._tray_icon = QSystemTrayIcon(_create_app_icon(), self)
        self._tray_icon.setToolTip("InboxAgent")

        tray_menu = QMenu()

        self._tray_start_action = QAction("Start Agent", self)
        self._tray_start_action.triggered.connect(self._start_agent)
        tray_menu.addAction(self._tray_start_action)

        self._tray_stop_action = QAction("Stop Agent", self)
        self._tray_stop_action.triggered.connect(self._stop_agent)
        self._tray_stop_action.setEnabled(False)
        tray_menu.addAction(self._tray_stop_action)

        tray_menu.addSeparator()

        open_action = QAction("Open", self)
        open_action.triggered.connect(self._show_window)
        tray_menu.addAction(open_action)

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self._quit_app)
        tray_menu.addAction(quit_action)

        self._tray_icon.setContextMenu(tray_menu)
        self._tray_icon.activated.connect(self._on_tray_activated)
        self._tray_icon.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_window()

    def _show_window(self):
        self.showNormal()
        self.activateWindow()

    def _start_agent(self):
        if self._agent_thread and self._agent_thread.isRunning():
            return

        self._agent_thread = AgentThread(self._agent_core, parent=self)
        self._agent_thread.state_changed.connect(self._on_state_changed)
        self._agent_thread.stats_updated.connect(self._dashboard_tab.update_stats)
        self._agent_thread.activity.connect(self._dashboard_tab.add_activity)
        self._agent_thread.error.connect(self._dashboard_tab.add_error)
        self._agent_thread.error_detail.connect(self._dashboard_tab.add_error)
        self._agent_thread.start()

    def _stop_agent(self):
        if self._agent_thread and self._agent_thread.isRunning():
            self._agent_thread.quit()
            self._agent_thread.wait(5000) # Wait up to 5 seconds

    def _on_state_changed(self, state: str):
        try:
            self._dashboard_tab.update_state(state)
            running = state == "running"
            self._tray_start_action.setEnabled(not running)
            self._tray_stop_action.setEnabled(running)
            self._tray_icon.setToolTip(f"InboxAgent - {state.capitalize()}")
        except RuntimeError: # Main window was closed
            pass

    def _on_config_changed(self, new_config: AgentConfig):
        self.config = new_config
        if self._agent_thread and self._agent_thread.isRunning():
            self._dashboard_tab.show_restart_warning()

    def closeEvent(self, event):
        """Minimize to tray instead of closing."""
        if not self._really_quit:
            event.ignore()
            self.hide()
            self._tray_icon.showMessage(
                "InboxAgent",
                "Application minimized to tray. Right-click tray icon to quit.",
                QSystemTrayIcon.MessageIcon.Information,
                2000,
            )
        else:
            # Actually quit
            if self._agent_thread and self._agent_thread.isRunning():
                self._agent_thread.request_stop()
                self._agent_thread.wait(5000)
            logging.getLogger("open_email").removeHandler(self._log_handler)
            event.accept()

    def _quit_app(self):
        """Actually quit the application."""
        self._really_quit = True
        self.close()
        QApplication.instance().quit()


def run_app(config: AgentConfig, minimized: bool = False):
    """Entry point for launching the GUI."""
    app = QApplication(sys.argv)
    app.setApplicationName("InboxAgent")
    app.setQuitOnLastWindowClosed(False)
    app.setStyleSheet(GLOBAL_STYLE)

    window = MainWindow(config, minimized=minimized)

    sys.exit(app.exec())
