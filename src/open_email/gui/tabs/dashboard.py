"""Dashboard tab: status indicator, start/stop, stats, activity log."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QVBoxLayout, QWidget,
)

from open_email.agent_core import AgentState, AgentStats

MAX_ACTIVITY_ITEMS = 200


class DashboardTab(QWidget):
    """Dashboard with status, controls, stats, and activity feed."""

    start_requested = pyqtSignal()
    stop_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        # --- Status bar ---
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        status_layout = QHBoxLayout(status_frame)

        self._status_dot = QLabel("\u2b24")
        self._status_dot.setFont(QFont("Arial", 14))
        self._status_dot.setStyleSheet("color: gray;")
        status_layout.addWidget(self._status_dot)

        self._status_label = QLabel("Stopped")
        self._status_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        status_layout.addWidget(self._status_label)

        status_layout.addStretch()

        self._start_btn = QPushButton("Start Agent")
        self._start_btn.setMinimumWidth(120)
        self._start_btn.clicked.connect(self.start_requested.emit)
        status_layout.addWidget(self._start_btn)

        self._stop_btn = QPushButton("Stop Agent")
        self._stop_btn.setMinimumWidth(120)
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self.stop_requested.emit)
        status_layout.addWidget(self._stop_btn)

        layout.addWidget(status_frame)

        # --- Restart warning banner ---
        self._restart_banner = QLabel(
            "Config changed while agent is running. Restart agent to apply."
        )
        self._restart_banner.setStyleSheet(
            "background-color: #fff3cd; color: #856404; padding: 8px; border-radius: 4px;"
        )
        self._restart_banner.setVisible(False)
        layout.addWidget(self._restart_banner)

        # --- Stats ---
        stats_frame = QFrame()
        stats_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        stats_layout = QHBoxLayout(stats_frame)

        self._stat_labels = {}
        for key, label in [
            ("accounts", "Accounts"),
            ("processed", "Processed"),
            ("rules", "Rules Triggered"),
            ("errors", "Errors"),
            ("cycles", "Cycles"),
        ]:
            vbox = QVBoxLayout()
            count = QLabel("0")
            count.setFont(QFont("Arial", 18, QFont.Weight.Bold))
            count.setAlignment(Qt.AlignmentFlag.AlignCenter)
            desc = QLabel(label)
            desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vbox.addWidget(count)
            vbox.addWidget(desc)
            stats_layout.addLayout(vbox)
            self._stat_labels[key] = count

        layout.addWidget(stats_frame)

        # --- Activity log ---
        activity_label = QLabel("Recent Activity")
        activity_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        layout.addWidget(activity_label)

        self._activity_list = QListWidget()
        layout.addWidget(self._activity_list, stretch=1)

    def update_state(self, state: str):
        """Update the status indicator."""
        colors = {
            AgentState.STOPPED: ("gray", "Stopped"),
            AgentState.STARTING: ("orange", "Starting..."),
            AgentState.RUNNING: ("green", "Running"),
            AgentState.STOPPING: ("orange", "Stopping..."),
            AgentState.ERROR: ("red", "Error"),
        }
        color, text = colors.get(state, ("gray", state.capitalize()))
        self._status_dot.setStyleSheet(f"color: {color};")
        self._status_label.setText(text)

        running = state == AgentState.RUNNING
        starting = state == AgentState.STARTING
        self._start_btn.setEnabled(not running and not starting)
        self._stop_btn.setEnabled(running)

        if state == AgentState.STOPPED:
            self._restart_banner.setVisible(False)

    def update_stats(self, stats: AgentStats):
        """Update stat counters."""
        self._stat_labels["accounts"].setText(str(stats.accounts_connected))
        self._stat_labels["processed"].setText(str(stats.emails_processed))
        self._stat_labels["rules"].setText(str(stats.rules_triggered))
        self._stat_labels["errors"].setText(str(stats.errors))
        self._stat_labels["cycles"].setText(str(stats.cycles_completed))

    def add_activity(self, message: str):
        """Add an activity message to the list."""
        item = QListWidgetItem(message)
        self._activity_list.insertItem(0, item)
        if self._activity_list.count() > MAX_ACTIVITY_ITEMS:
            self._activity_list.takeItem(self._activity_list.count() - 1)

    def add_error(self, message: str):
        """Add an error message to the activity list in red."""
        item = QListWidgetItem(message)
        item.setForeground(QColor("red"))
        self._activity_list.insertItem(0, item)
        if self._activity_list.count() > MAX_ACTIVITY_ITEMS:
            self._activity_list.takeItem(self._activity_list.count() - 1)

    def show_restart_warning(self):
        """Show the restart-needed banner."""
        self._restart_banner.setVisible(True)
