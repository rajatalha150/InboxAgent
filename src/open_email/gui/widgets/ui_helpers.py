"""UI Utility components like Info Buttons and modern styles."""

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QCursor, QFont
from PyQt6.QtWidgets import QPushButton, QMessageBox, QHBoxLayout, QLabel, QWidget

class InfoButton(QPushButton):
    """A consistent (?) button that opens a styled information popup."""
    def __init__(self, title: str, text: str, parent=None):
        super().__init__("?", parent)
        self.title = title
        self.text_content = text
        self.setObjectName("InfoButton")
        self.setFixedSize(QSize(20, 20))
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setToolTip("Click for more info")
        
        self.setStyleSheet("""
            QPushButton#InfoButton {
                background-color: transparent;
                color: #888888;
                border: 1px solid #444444;
                border-radius: 10px;
                font-weight: bold;
                font-family: monospace;
                font-size: 13px;
                text-align: center;
                padding: 0px;
                margin: 0px;
                padding-bottom: 2px;
            }
            QPushButton#InfoButton:hover {
                color: #ffffff;
                border: 1px solid #3a82f7;
                background-color: #2b2b2b;
            }
        """)
        self.clicked.connect(self.show_info)

    def show_info(self):
        msg = QMessageBox(self)
        msg.setWindowTitle(self.title)
        msg.setText(f"<b>{self.title}</b>")
        msg.setInformativeText(self.text_content)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #1e1e1e;
            }
            QLabel {
                color: #e0e0e0;
                font-size: 13px;
                background-color: transparent;
            }
            QPushButton {
                background-color: #2b2b2b;
                color: #e0e0e0;
                border: 1px solid #444444;
                border-radius: 5px;
                padding: 6px 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                border: 1px solid #555555;
            }
            QPushButton:pressed {
                background-color: #1e1e1e;
            }
        """)
        msg.exec()


def create_field_label(text: str, info_title: str, info_text: str) -> QWidget:
    """Creates a widget containing a label and an InfoButton next to it.
    Can be passed directly into QFormLayout.addRow(widget, field)."""
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(6)
    
    lbl = QLabel(text)
    
    btn = InfoButton(info_title, info_text)
    
    layout.addWidget(lbl)
    layout.addWidget(btn)
    
    return container

GLOBAL_STYLE = """
/* Global Dark Theme Stylesheet */

QWidget {
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
    color: #e0e0e0;
    background-color: transparent;
}

QMainWindow, QDialog, QMessageBox {
    background-color: #121212;
    color: #e0e0e0;
}

QLabel {
    color: #e0e0e0;
    background: transparent;
}

/* ToolTip */
QToolTip {
    background-color: #2b2b2b;
    color: #e0e0e0;
    border: 1px solid #444444;
    border-radius: 4px;
    padding: 6px;
    font-size: 12px;
}

/* Base Frame */
QFrame {
    border: none;
    background: transparent;
}

QFrame[frameShape="6"] { /* StyledPanel */
    border: 1px solid #333333;
    border-radius: 6px;
    background-color: #1e1e1e;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #333333;
    background: #1e1e1e;
    border-radius: 6px;
    top: -1px; /* hide tab overlap */
}
QTabBar::tab {
    background: #2b2b2b;
    border: 1px solid #333333;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    color: #a0a0a0;
    font-weight: bold;
}
QTabBar::tab:selected {
    background: #1e1e1e;
    border-bottom-color: #1e1e1e;
    color: #3a82f7;
}
QTabBar::tab:hover:!selected {
    background: #383838;
}

/* Buttons */
QPushButton {
    background-color: #2b2b2b;
    color: #e0e0e0;
    border: 1px solid #444444;
    border-radius: 5px;
    padding: 6px 14px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #3a3a3a;
    border: 1px solid #555555;
}
QPushButton:pressed {
    background-color: #1e1e1e;
}
QPushButton#PrimaryAction {
    background-color: #3a82f7;
    color: white;
    border: none;
    font-weight: bold;
}
QPushButton#PrimaryAction:hover {
    background-color: #5596fb;
}
QPushButton#PrimaryAction:disabled {
    background-color: #214b8c;
    color: #888888;
}
QPushButton#StopAction {
    background-color: #d32f2f;
    color: white;
    border: none;
    font-weight: bold;
}
QPushButton#StopAction:hover {
    background-color: #f44336;
}
QPushButton#StopAction:disabled {
    background-color: #7f1d1d;
    color: #888888;
}

/* Inputs */
QLineEdit, QSpinBox, QComboBox {
    border: 1px solid #444444;
    border-radius: 4px;
    padding: 6px 10px;
    background-color: #2b2b2b;
    color: #e0e0e0;
    selection-background-color: #3a82f7;
    selection-color: white;
}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1px solid #3a82f7;
}
QComboBox QAbstractItemView {
    background-color: #2b2b2b;
    color: #e0e0e0;
    border: 1px solid #444444;
    selection-background-color: #3a82f7;
    selection-color: white;
}

/* Checkboxes */
QCheckBox {
    spacing: 8px;
    color: #e0e0e0;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #555555;
    border-radius: 4px;
    background: #2b2b2b;
}
QCheckBox::indicator:hover {
    border: 1px solid #3a82f7;
}
QCheckBox::indicator:checked {
    background-color: #3a82f7;
    border: 1px solid #3a82f7;
    image: url("data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0ibm9uZSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIzIiBkPSJNNSAxMmw1IDVMMjAgNyIvPjwvc3ZnPg==");
}

/* Group Boxes */
QGroupBox {
    border: 1px solid #333333;
    border-radius: 6px;
    margin-top: 14px;
    background-color: #1e1e1e;
    font-weight: bold;
    color: #e0e0e0;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 5px;
    color: #a0a0a0;
}

/* Tables and Trees */
QTableWidget, QTreeView, QTreeWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
    border: 1px solid #333333;
    border-radius: 4px;
    gridline-color: #333333;
    selection-background-color: #2a3f5f;
    selection-color: #ffffff;
    alternate-background-color: #252526;
}
QTreeView::item:hover, QTableWidget::item:hover {
    background-color: #2a2d31;
}
QTreeView::item:selected, QTableWidget::item:selected {
    background-color: #2a3f5f;
    color: #ffffff;
}
QHeaderView {
    background-color: #1e1e1e;
    border: none;
    border-bottom: 1px solid #333333;
}
QHeaderView::section {
    background-color: #2b2b2b;
    color: #e0e0e0;
    padding: 6px;
    border: none;
    border-right: 1px solid #333333;
    border-bottom: 1px solid #333333;
    font-weight: bold;
}
QTableCornerButton::section {
    background-color: #2b2b2b;
    border: none;
    border-right: 1px solid #333333;
    border-bottom: 1px solid #333333;
}

/* Text Edit / Logs */
QTextEdit, QPlainTextEdit {
    background-color: #0d0d0d !important;
    color: #4af626 !important;
    border: 1px solid #333333;
    border-radius: 4px;
    font-family: monospace;
    font-size: 13px;
    padding: 4px;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #1e1e1e;
    width: 12px;
    margin: 0px 0 0px 0;
    border-radius: 6px;
}
QScrollBar::handle:vertical {
    background: #444444;
    min-height: 20px;
    border-radius: 6px;
}
QScrollBar::handle:vertical:hover {
    background: #666666;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background: #1e1e1e;
    height: 12px;
    margin: 0px 0 0px 0;
    border-radius: 6px;
}
QScrollBar::handle:horizontal {
    background: #444444;
    min-width: 20px;
    border-radius: 6px;
}
QScrollBar::handle:horizontal:hover {
    background: #666666;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Menus */
QMenuBar {
    background-color: #121212;
    color: #e0e0e0;
}
QMenu {
    background-color: #1e1e1e;
    color: #e0e0e0;
    border: 1px solid #333333;
}
QMenu::item:selected {
    background-color: #3a82f7;
    color: white;
}
"""
