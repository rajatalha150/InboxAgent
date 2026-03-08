"""Accounts tab: CRUD table for accounts.yaml."""

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QMessageBox, QPushButton,
    QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from open_email.agent_core import AgentConfig
from open_email.config_loader import load_accounts, save_accounts
from open_email.gui.widgets.ui_helpers import create_field_label

COLUMNS = ["Name", "IMAP Server", "Port", "Email", "SSL"]


class AccountDialog(QDialog):
    """Dialog for adding/editing an account."""

    def __init__(self, account: dict | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Account" if account else "Add Account")
        self.setMinimumWidth(400)

        layout = QFormLayout(self)

        self._name = QLineEdit(account.get("name", "") if account else "")
        layout.addRow(create_field_label("Name:", "Account Name", "A friendly internal name for this account. Example: 'Personal Gmail'"), self._name)

        self._server = QLineEdit(account.get("imap_server", "") if account else "")
        layout.addRow(create_field_label("IMAP Server:", "IMAP Server Address", "The provider IMAP address (e.g. 'imap.gmail.com' or 'outlook.office365.com')"), self._server)

        self._port = QSpinBox()
        self._port.setRange(1, 65535)
        self._port.setValue(account.get("imap_port", 993) if account else 993)
        layout.addRow(create_field_label("Port:", "IMAP Port", "Standard IMAP port is 143. IMAP over SSL/TLS uses 993."), self._port)

        self._email = QLineEdit(account.get("email", "") if account else "")
        layout.addRow(create_field_label("Email:", "Email Address", "Your full email address authentication login."), self._email)

        self._password = QLineEdit(account.get("password", "") if account else "")
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow(create_field_label("Password:", "Password / App Password", "If using 2FA on Gmail, Outlook, or Yahoo, you must generate a special 'App Password' rather than providing your main login password."), self._password)

        self._ssl = QCheckBox()
        self._ssl.setChecked(account.get("ssl", True) if account else True)
        layout.addRow(create_field_label("SSL:", "Enable SSL", "Forces an encrypted SSL connection to the IMAP server. Strongly Recommended."), self._ssl)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _validate_and_accept(self):
        if not self._name.text().strip():
            QMessageBox.warning(self, "Validation", "Name is required.")
            return
        if not self._server.text().strip():
            QMessageBox.warning(self, "Validation", "IMAP Server is required.")
            return
        if not self._email.text().strip():
            QMessageBox.warning(self, "Validation", "Email is required.")
            return
        if not self._password.text():
            QMessageBox.warning(self, "Validation", "Password is required.")
            return
        self.accept()

    def get_account(self) -> dict:
        return {
            "name": self._name.text().strip(),
            "imap_server": self._server.text().strip(),
            "imap_port": self._port.value(),
            "email": self._email.text().strip(),
            "password": self._password.text(),
            "ssl": self._ssl.isChecked(),
        }


class AccountsTab(QWidget):
    """CRUD table for email accounts."""

    def __init__(self, config: AgentConfig, parent=None):
        super().__init__(parent)
        self._config = config
        self._accounts_path = Path(config.config_dir) / "accounts.yaml"
        self._accounts: list[dict] = []

        layout = QVBoxLayout(self)

        # Toolbar
        toolbar = QHBoxLayout()
        add_btn = QPushButton("Add Account")
        add_btn.clicked.connect(self._add_account)
        toolbar.addWidget(add_btn)

        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self._edit_account)
        toolbar.addWidget(edit_btn)

        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self._remove_account)
        toolbar.addWidget(remove_btn)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Table
        self._table = QTableWidget(0, len(COLUMNS))
        self._table.setHorizontalHeaderLabels(COLUMNS)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        layout.addWidget(self._table, stretch=1)

        self._load()

    def _load(self):
        """Load accounts from YAML."""
        try:
            self._accounts = load_accounts(self._accounts_path)
        except Exception:
            self._accounts = []
        self._refresh_table()

    def _refresh_table(self):
        self._table.setRowCount(len(self._accounts))
        for row, acc in enumerate(self._accounts):
            self._table.setItem(row, 0, QTableWidgetItem(acc["name"]))
            self._table.setItem(row, 1, QTableWidgetItem(acc["imap_server"]))
            self._table.setItem(row, 2, QTableWidgetItem(str(acc["imap_port"])))
            self._table.setItem(row, 3, QTableWidgetItem(acc["email"]))
            self._table.setItem(row, 4, QTableWidgetItem("Yes" if acc["ssl"] else "No"))

    def _save(self):
        save_accounts(self._accounts_path, self._accounts)

    def _add_account(self):
        dlg = AccountDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._accounts.append(dlg.get_account())
            self._save()
            self._refresh_table()

    def _edit_account(self):
        row = self._table.currentRow()
        if row < 0:
            return
        dlg = AccountDialog(account=self._accounts[row], parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._accounts[row] = dlg.get_account()
            self._save()
            self._refresh_table()

    def _remove_account(self):
        row = self._table.currentRow()
        if row < 0:
            return
        name = self._accounts[row]["name"]
        reply = QMessageBox.question(
            self, "Confirm", f"Remove account '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._accounts.pop(row)
            self._save()
            self._refresh_table()
