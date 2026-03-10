"""Logs tab: live log viewer with auto-scroll."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QTextCursor
from PyQt6.QtWidgets import (
    QCheckBox, QHBoxLayout, QPushButton, QTextEdit, QVBoxLayout, QWidget,
)

from open_email.gui.widgets.log_handler import QtLogHandler

MAX_LOG_LINES = 5000


class LogsTab(QWidget):
    """Live log viewer powered by QtLogHandler."""

    def __init__(self, log_handler: QtLogHandler, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        # Controls
        controls = QHBoxLayout()

        self._auto_scroll = QCheckBox("Auto-scroll")
        self._auto_scroll.setChecked(True)
        controls.addWidget(self._auto_scroll)

        controls.addStretch()

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear)
        controls.addWidget(clear_btn)

        layout.addLayout(controls)

        # Log display
        self._text = QTextEdit()
        self._text.setReadOnly(True)
        self._text.setFont(QFont("Monospace", 9))
        self._text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self._text, stretch=1)

        self._line_count = 0

        # Connect signal
        log_handler.emitter.log_message.connect(self._append_log)

    def _append_log(self, message: str):
        self._text.append(message)
        self._line_count += 1

        # Trim old lines
        if self._line_count > MAX_LOG_LINES:
            cursor = self._text.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.movePosition(
                QTextCursor.MoveOperation.Down,
                QTextCursor.MoveMode.KeepAnchor,
                self._line_count - MAX_LOG_LINES,
            )
            cursor.removeSelectedText()
            self._line_count = MAX_LOG_LINES

        if self._auto_scroll.isChecked():
            scrollbar = self._text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def _clear(self):
        self._text.clear()
        self._line_count = 0
