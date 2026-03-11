"""Activity tab: view cycle summaries."""

import json
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout, QListWidget, QListWidgetItem, QPushButton,
    QTextEdit, QVBoxLayout, QWidget,
)

class ActivityTab(QWidget):
    """Panel for viewing cycle summaries."""

    def __init__(self, agent_core: AgentCore, parent=None):
        super().__init__(parent)
        self._agent_core = agent_core
        self._summaries_dir = Path(self._agent_core.config.config_dir) / "summaries"

        layout = QHBoxLayout(self)

        self._summary_list = QListWidget()
        self._summary_list.itemSelectionChanged.connect(self._on_summary_selected)
        layout.addWidget(self._summary_list, 1)

        self._summary_detail = QTextEdit()
        self._summary_detail.setReadOnly(True)
        layout.addWidget(self._summary_detail, 2)

        btn_layout = QVBoxLayout()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_summaries)
        btn_layout.addWidget(refresh_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self._delete_summary)
        btn_layout.addWidget(delete_btn)
        layout.addLayout(btn_layout)

        self.refresh_summaries()

    def refresh_summaries(self):
        """Reload the list of summaries from the summaries directory."""
        self._summary_list.clear()
        if not self._summaries_dir.exists():
            return

        for summary_file in sorted(self._summaries_dir.glob("summary_*.json"), reverse=True):
            item = QListWidgetItem(summary_file.name)
            item.setData(Qt.ItemDataRole.UserRole, summary_file)
            self._summary_list.addItem(item)

    def _on_summary_selected(self):
        """Load the selected summary into the detail view."""
        selected_items = self._summary_list.selectedItems()
        if not selected_items:
            return

        summary_file = selected_items[0].data(Qt.ItemDataRole.UserRole)
        with open(summary_file) as f:
            data = json.load(f)
        self._summary_detail.setText(data.get("summary", ""))

    def _delete_summary(self):
        """Delete the selected summary file."""
        selected_items = self._summary_list.selectedItems()
        if not selected_items:
            return

        summary_file = selected_items[0].data(Qt.ItemDataRole.UserRole)
        summary_file.unlink()
        self.refresh_summaries()