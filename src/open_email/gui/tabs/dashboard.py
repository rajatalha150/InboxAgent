"""Dashboard tab: status indicator, start/stop, stats, activity log."""

from datetime import datetime

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from open_email.agent_core import AgentState, AgentStats

MAX_ACTIVITY_ITEMS = 200

# Category definitions: (key, label, dot_unicode, color)
CATEGORIES = {
    "connection": ("Connection", "\U0001f535", QColor(30, 144, 255)),   # blue dot
    "processing": ("Processing", "\u26aa", QColor(160, 160, 160)),      # gray dot
    "rule":       ("Rule", "\U0001f7e2", QColor(50, 180, 50)),          # green dot
    "error":      ("Error", "\U0001f534", QColor(220, 50, 50)),         # red dot
}


def _detect_category(message: str) -> str:
    """Auto-detect activity category from message text patterns."""
    if message.lstrip("[").split("]", 1)[-1].strip().startswith("Connected to"):
        return "connection"
    if "Processing:" in message:
        return "processing"
    if "Rule '" in message and "triggered" in message:
        return "rule"
    return "processing"  # default fallback


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
        self._start_btn.setObjectName("PrimaryAction")
        self._start_btn.setMinimumWidth(120)
        self._start_btn.clicked.connect(self.start_requested.emit)
        status_layout.addWidget(self._start_btn)

        self._stop_btn = QPushButton("Stop Agent")
        self._stop_btn.setObjectName("StopAction")
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

        # --- Activity header + toolbar ---
        activity_label = QLabel("Recent Activity")
        activity_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        layout.addWidget(activity_label)

        toolbar = QHBoxLayout()

        self._filter_combo = QComboBox()
        self._filter_combo.addItems(["All", "Connections", "Processing", "Rules", "Errors"])
        self._filter_combo.setMinimumWidth(120)
        self._filter_combo.currentIndexChanged.connect(self._apply_filters)
        toolbar.addWidget(self._filter_combo)

        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText("Search...")
        self._search_box.textChanged.connect(self._apply_filters)
        toolbar.addWidget(self._search_box)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_activity)
        toolbar.addWidget(clear_btn)

        layout.addLayout(toolbar)

        # --- Activity tree ---
        self._activity_tree = QTreeWidget()
        self._activity_tree.setHeaderLabels(["Time", "Category", "Message"])
        self._activity_tree.setColumnWidth(0, 140)
        self._activity_tree.setColumnWidth(1, 100)
        self._activity_tree.setRootIsDecorated(True)
        self._activity_tree.setAlternatingRowColors(True)
        self._activity_tree.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self._activity_tree, stretch=1)

        # Internal store: list of dicts for filtering
        self._entries: list[dict] = []

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
        """Add an activity message, auto-detecting category."""
        category = _detect_category(message)
        self._add_entry(category, message)

    def add_error(self, message: str, detail: str = ""):
        """Add an error message with optional extended detail."""
        self._add_entry("error", message, detail)

    def _add_entry(self, category: str, message: str, detail: str = ""):
        """Core method to add an activity entry."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = {
            "category": category,
            "message": message,
            "detail": detail,
            "timestamp": timestamp,
        }

        self._entries.insert(0, entry)
        if len(self._entries) > MAX_ACTIVITY_ITEMS:
            self._entries.pop()

        if self._entry_matches_filter(entry):
            self._insert_tree_item(entry, position=0)
            # Trim visible items
            while self._activity_tree.topLevelItemCount() > MAX_ACTIVITY_ITEMS:
                self._activity_tree.takeTopLevelItem(
                    self._activity_tree.topLevelItemCount() - 1
                )

    def _insert_tree_item(self, entry: dict, position: int = 0):
        """Create and insert a QTreeWidgetItem for an entry."""
        cat_key = entry["category"]
        cat_label, dot, color = CATEGORIES.get(
            cat_key, ("Unknown", "\u26aa", QColor(128, 128, 128))
        )

        item = QTreeWidgetItem()
        item.setText(0, f"{dot} {entry['timestamp']}")
        item.setText(1, cat_label)
        item.setText(2, entry["message"])
        item.setForeground(0, color)
        item.setForeground(1, color)

        if cat_key == "error":
            item.setForeground(2, QColor(220, 50, 50))

        # Store detail for double-click
        item.setData(0, Qt.ItemDataRole.UserRole, entry.get("detail", ""))

        # Add expandable child for error detail
        if entry.get("detail"):
            child = QTreeWidgetItem(item)
            child.setText(0, "  \u2514 Details:")
            detail_preview = entry["detail"].strip().split("\n")[-1][:120]
            child.setText(2, detail_preview)
            child.setForeground(0, QColor(160, 160, 160))
            child.setForeground(2, QColor(160, 160, 160))

        self._activity_tree.insertTopLevelItem(position, item)

    def _entry_matches_filter(self, entry: dict) -> bool:
        """Check if an entry matches the current filter and search."""
        # Category filter
        filter_idx = self._filter_combo.currentIndex()
        filter_map = {0: None, 1: "connection", 2: "processing", 3: "rule", 4: "error"}
        required_cat = filter_map.get(filter_idx)
        if required_cat and entry["category"] != required_cat:
            return False

        # Text search
        search_text = self._search_box.text().strip().lower()
        if search_text and search_text not in entry["message"].lower():
            return False

        return True

    def _apply_filters(self):
        """Re-populate the tree based on current filter/search settings."""
        self._activity_tree.clear()
        for entry in self._entries:
            if self._entry_matches_filter(entry):
                self._insert_tree_item(
                    entry, position=self._activity_tree.topLevelItemCount()
                )

    def _on_double_click(self, index):
        """Show error detail in a popup on double-click."""
        item = self._activity_tree.currentItem()
        if not item:
            return
        # If it's a child item, use parent
        parent = item.parent()
        if parent:
            item = parent

        detail = item.data(0, Qt.ItemDataRole.UserRole)
        if not detail:
            return

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Error Detail")
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setText(item.text(2))
        msg_box.setDetailedText(detail)
        msg_box.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        msg_box.exec()

    def _clear_activity(self):
        """Clear all activity entries."""
        self._entries.clear()
        self._activity_tree.clear()

    def show_restart_warning(self):
        """Show the restart-needed banner."""
        self._restart_banner.setVisible(True)
