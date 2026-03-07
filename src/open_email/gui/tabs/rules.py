"""Rules tab: CRUD table for rules.yaml."""

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox, QFormLayout, QFrame,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from open_email.agent_core import AgentConfig
from open_email.config_loader import load_rules, save_rules

COLUMNS = ["Name", "Match", "Action"]
AUTO_SORT_RULE_NAME = "auto-sort-by-sender"


def _summarize_match(match: dict) -> str:
    parts = []
    for key in ("from", "to", "subject", "body", "ai_prompt"):
        if key in match:
            val = match[key]
            if isinstance(val, list):
                val = ", ".join(str(v) for v in val)
            parts.append(f"{key}: {val}")
    return "; ".join(parts)


def _summarize_action(action: dict) -> str:
    parts = []
    if action.get("delete"):
        parts.append("delete")
    if "move_to" in action:
        parts.append(f"move_to: {action['move_to']}")
    if "flag" in action:
        parts.append(f"flag: {action['flag']}")
    if action.get("mark_read"):
        parts.append("mark_read")
    if action.get("mark_unread"):
        parts.append("mark_unread")
    if "label" in action:
        parts.append(f"label: {action['label']}")
    if action.get("auto_sort_by_sender"):
        parts.append("auto_sort_by_sender")
    return "; ".join(parts)


class RuleDialog(QDialog):
    """Dialog for adding/editing a rule."""

    def __init__(self, rule: dict | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Rule" if rule else "Add Rule")
        self.setMinimumWidth(500)

        layout = QFormLayout(self)

        self._name = QLineEdit()
        layout.addRow("Rule Name:", self._name)

        # Match fields
        layout.addRow(QLabel("--- Match Conditions ---"))
        self._from = QLineEdit()
        self._from.setPlaceholderText("e.g. *@domain.com or user@example.com")
        layout.addRow("From:", self._from)

        self._to = QLineEdit()
        self._to.setPlaceholderText("e.g. me@example.com")
        layout.addRow("To:", self._to)

        self._subject = QLineEdit()
        self._subject.setPlaceholderText("Comma-separated keywords")
        layout.addRow("Subject:", self._subject)

        self._body = QLineEdit()
        self._body.setPlaceholderText("Comma-separated keywords")
        layout.addRow("Body:", self._body)

        self._ai_prompt = QLineEdit()
        self._ai_prompt.setPlaceholderText("AI question about the email")
        layout.addRow("AI Prompt:", self._ai_prompt)

        # Action fields
        layout.addRow(QLabel("--- Actions ---"))
        self._move_to = QLineEdit()
        self._move_to.setPlaceholderText("Folder name")
        layout.addRow("Move To:", self._move_to)

        self._flag = QCheckBox()
        layout.addRow("Flag:", self._flag)

        self._delete = QCheckBox()
        layout.addRow("Delete:", self._delete)

        self._mark_read = QCheckBox()
        layout.addRow("Mark Read:", self._mark_read)

        self._mark_unread = QCheckBox()
        layout.addRow("Mark Unread:", self._mark_unread)

        self._label = QLineEdit()
        self._label.setPlaceholderText("Gmail label")
        layout.addRow("Label:", self._label)

        self._auto_sort_by_sender = QCheckBox()
        layout.addRow("Auto-Sort by Sender:", self._auto_sort_by_sender)

        # Populate if editing
        if rule:
            self._name.setText(rule.get("name", ""))
            match = rule.get("match", {})
            self._from.setText(self._val_to_str(match.get("from", "")))
            self._to.setText(self._val_to_str(match.get("to", "")))
            self._subject.setText(self._val_to_str(match.get("subject", "")))
            self._body.setText(self._val_to_str(match.get("body", "")))
            self._ai_prompt.setText(match.get("ai_prompt", ""))

            action = rule.get("action", {})
            self._move_to.setText(action.get("move_to", ""))
            self._flag.setChecked(action.get("flag", False))
            self._delete.setChecked(action.get("delete", False))
            self._mark_read.setChecked(action.get("mark_read", False))
            self._mark_unread.setChecked(action.get("mark_unread", False))
            self._label.setText(action.get("label", ""))
            self._auto_sort_by_sender.setChecked(action.get("auto_sort_by_sender", False))

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    @staticmethod
    def _val_to_str(val) -> str:
        if isinstance(val, list):
            return ", ".join(str(v) for v in val)
        return str(val) if val else ""

    @staticmethod
    def _str_to_val(text: str):
        """Convert comma-separated text to a string or list."""
        text = text.strip()
        if not text:
            return None
        parts = [p.strip() for p in text.split(",") if p.strip()]
        if len(parts) == 1:
            return parts[0]
        return parts

    def _validate_and_accept(self):
        if not self._name.text().strip():
            QMessageBox.warning(self, "Validation", "Rule name is required.")
            return
        # Need at least one match condition
        has_match = any([
            self._from.text().strip(),
            self._to.text().strip(),
            self._subject.text().strip(),
            self._body.text().strip(),
            self._ai_prompt.text().strip(),
        ])
        if not has_match:
            QMessageBox.warning(self, "Validation", "At least one match condition is required.")
            return
        # Need at least one action
        has_action = any([
            self._move_to.text().strip(),
            self._flag.isChecked(),
            self._delete.isChecked(),
            self._mark_read.isChecked(),
            self._mark_unread.isChecked(),
            self._label.text().strip(),
            self._auto_sort_by_sender.isChecked(),
        ])
        if not has_action:
            QMessageBox.warning(self, "Validation", "At least one action is required.")
            return
        self.accept()

    def get_rule(self) -> dict:
        match = {}
        for key, widget in [
            ("from", self._from), ("to", self._to),
            ("subject", self._subject), ("body", self._body),
        ]:
            val = self._str_to_val(widget.text())
            if val is not None:
                match[key] = val
        if self._ai_prompt.text().strip():
            match["ai_prompt"] = self._ai_prompt.text().strip()

        action = {}
        if self._move_to.text().strip():
            action["move_to"] = self._move_to.text().strip()
        if self._flag.isChecked():
            action["flag"] = True
        if self._delete.isChecked():
            action["delete"] = True
        if self._mark_read.isChecked():
            action["mark_read"] = True
        if self._mark_unread.isChecked():
            action["mark_unread"] = True
        if self._label.text().strip():
            action["label"] = self._label.text().strip()
        if self._auto_sort_by_sender.isChecked():
            action["auto_sort_by_sender"] = True

        return {
            "name": self._name.text().strip(),
            "match": match,
            "action": action,
        }


class RulesTab(QWidget):
    """CRUD table for email rules."""

    def __init__(self, config: AgentConfig, parent=None):
        super().__init__(parent)
        self._config = config
        self._rules_path = Path(config.config_dir) / "rules.yaml"
        self._rules: list[dict] = []

        layout = QVBoxLayout(self)

        # Auto-sort panel
        auto_sort_frame = QFrame()
        auto_sort_frame.setFrameShape(QFrame.Shape.StyledPanel)
        auto_sort_frame.setStyleSheet(
            "QFrame { background-color: #f0f7ff; border: 1px solid #b0d0f0;"
            " border-radius: 6px; padding: 8px; }"
        )
        auto_sort_layout = QVBoxLayout(auto_sort_frame)
        auto_sort_layout.setContentsMargins(10, 8, 10, 8)

        header_row = QHBoxLayout()
        auto_sort_label = QLabel("<b>Auto-Sort by Sender</b>")
        header_row.addWidget(auto_sort_label)
        header_row.addStretch()
        self._auto_sort_toggle = QCheckBox("Enable")
        self._auto_sort_toggle.toggled.connect(self._on_auto_sort_toggled)
        header_row.addWidget(self._auto_sort_toggle)
        auto_sort_layout.addLayout(header_row)

        desc = QLabel(
            "Automatically move emails into folders named after the sender's "
            "email address. Only applies when no other rule matches. "
            "Folders are created on the mail server if they don't exist."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #555; font-size: 12px;")
        auto_sort_layout.addWidget(desc)

        layout.addWidget(auto_sort_frame)

        # Toolbar
        toolbar = QHBoxLayout()
        add_btn = QPushButton("Add Rule")
        add_btn.clicked.connect(self._add_rule)
        toolbar.addWidget(add_btn)

        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self._edit_rule)
        toolbar.addWidget(edit_btn)

        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self._remove_rule)
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
        layout.addWidget(self._table, stretch=1)

        self._load()

    def _load(self):
        try:
            self._rules = load_rules(self._rules_path)
        except Exception:
            self._rules = []
        # Sync toggle state (block signals to avoid re-triggering _on_auto_sort_toggled)
        has_auto_sort = any(r["name"] == AUTO_SORT_RULE_NAME for r in self._rules)
        self._auto_sort_toggle.blockSignals(True)
        self._auto_sort_toggle.setChecked(has_auto_sort)
        self._auto_sort_toggle.blockSignals(False)
        self._refresh_table()

    def _user_rules(self) -> list[dict]:
        """Return rules excluding the auto-sort rule."""
        return [r for r in self._rules if r["name"] != AUTO_SORT_RULE_NAME]

    def _refresh_table(self):
        visible = self._user_rules()
        self._table.setRowCount(len(visible))
        for row, rule in enumerate(visible):
            self._table.setItem(row, 0, QTableWidgetItem(rule["name"]))
            self._table.setItem(row, 1, QTableWidgetItem(_summarize_match(rule["match"])))
            self._table.setItem(row, 2, QTableWidgetItem(_summarize_action(rule["action"])))

    def _save(self):
        save_rules(self._rules_path, self._rules)

    def _on_auto_sort_toggled(self, checked: bool):
        """Add or remove the auto-sort rule based on toggle state."""
        # Remove existing auto-sort rule if present
        self._rules = [r for r in self._rules if r["name"] != AUTO_SORT_RULE_NAME]
        if checked:
            # Append as last rule (catch-all)
            self._rules.append({
                "name": AUTO_SORT_RULE_NAME,
                "match": {"from": "*"},
                "action": {"auto_sort_by_sender": True},
            })
        self._save()
        self._refresh_table()

    def _add_rule(self):
        dlg = RuleDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_rule = dlg.get_rule()
            # Insert before auto-sort rule if present (keep auto-sort last)
            auto_sort_idx = next(
                (i for i, r in enumerate(self._rules) if r["name"] == AUTO_SORT_RULE_NAME),
                None,
            )
            if auto_sort_idx is not None:
                self._rules.insert(auto_sort_idx, new_rule)
            else:
                self._rules.append(new_rule)
            self._save()
            self._refresh_table()

    def _edit_rule(self):
        row = self._table.currentRow()
        if row < 0:
            return
        visible = self._user_rules()
        rule = visible[row]
        real_idx = self._rules.index(rule)
        dlg = RuleDialog(rule=rule, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._rules[real_idx] = dlg.get_rule()
            self._save()
            self._refresh_table()

    def _remove_rule(self):
        row = self._table.currentRow()
        if row < 0:
            return
        visible = self._user_rules()
        rule = visible[row]
        real_idx = self._rules.index(rule)
        name = rule["name"]
        reply = QMessageBox.question(
            self, "Confirm", f"Remove rule '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._rules.pop(real_idx)
            self._save()
            self._refresh_table()
