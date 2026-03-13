"""Rules tab: CRUD table for rules.yaml."""

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QFrame,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox,
    QPushButton, QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from open_email.agent_core import AgentConfig, AgentCore, AgentState
from open_email.config_loader import load_rules, save_rules
from open_email.gui.widgets.ui_helpers import create_field_label

COLUMNS = ["Name", "Match", "Action"]
AUTO_SORT_RULE_NAME = "auto-sort-by-sender"
CONTENT_RULES_NAME = "content-based-rules"
OFFICE_RULES_NAME = "office-based-rules"


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
    if "auto_sort_by_sender" in action:
        val = action["auto_sort_by_sender"]
        if isinstance(val, dict):
            parts.append(f"auto_sort_by_sender: {val.get('strategy', 'full_email')}")
        else:
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
        layout.addRow(create_field_label("Rule Name:", "Rule Name", "A descriptive, unique name for your rule."), self._name)

        # Match fields
        layout.addRow(QLabel("<b>--- Match Conditions ---</b>"))
        self._from = QLineEdit()
        self._from.setPlaceholderText("e.g. *@domain.com or user@example.com")
        layout.addRow(create_field_label("From:", "From (Sender)", "Matches the sender's email. Supports globs like *@company.com."), self._from)

        self._to = QLineEdit()
        self._to.setPlaceholderText("e.g. me@example.com")
        layout.addRow(create_field_label("To:", "To (Recipient)", "Matches the recipient's email. Supports globs."), self._to)

        self._subject = QLineEdit()
        self._subject.setPlaceholderText("Comma-separated keywords")
        layout.addRow(create_field_label("Subject:", "Subject Matches", "Matches if ANY of these comma-separated keywords appear in the subject."), self._subject)

        self._body = QLineEdit()
        self._body.setPlaceholderText("Comma-separated keywords")
        layout.addRow(create_field_label("Body:", "Body Matches", "Matches if ANY of these comma-separated keywords appear in the email body."), self._body)

        self._ai_prompt = QLineEdit()
        self._ai_prompt.setPlaceholderText("AI question about the email")
        layout.addRow(create_field_label("AI Prompt:", "AI Classifier Prompt", "A yes/no question asked to the local AI. If the AI replies 'yes', this condition matches. (e.g. 'Is this an invoice?')"), self._ai_prompt)

        self._days_older = QSpinBox()
        self._days_older.setRange(0, 999)
        self._days_older.setValue(0)
        layout.addRow(
            create_field_label(
                "Older Than (Days):",
                "Older Than (Days)",
                "Matches if the email was received more than this many days ago. Use 0 to disable.",
            ),
            self._days_older,
        )

        # Action fields
        layout.addRow(QLabel("<b>--- Actions ---</b>"))
        self._move_to = QLineEdit()
        self._move_to.setPlaceholderText("Folder name")
        layout.addRow(create_field_label("Move To:", "Move To Folder", "Moves the email to this specific IMAP folder. Created if it doesn't exist."), self._move_to)

        self._flag = QCheckBox()
        layout.addRow(create_field_label("Flag:", "Flag Message", "Stars or Flags the active email."), self._flag)

        self._delete = QCheckBox()
        layout.addRow(create_field_label("Delete:", "Delete Email", "Moves the email to Trash or permanently deletes it. STOPS further action processing for this email."), self._delete)

        self._mark_read = QCheckBox()
        layout.addRow(create_field_label("Mark Read:", "Mark Read", "Marks the email as read (seen flag)."), self._mark_read)

        self._mark_unread = QCheckBox()
        layout.addRow(create_field_label("Mark Unread:", "Mark Unread", "Marks the email as unread."), self._mark_unread)

        self._label = QLineEdit()
        self._label.setPlaceholderText("Gmail label")
        layout.addRow(create_field_label("Label:", "Apply Label", "Applies a provider-side label (Primarily applicable to Gmail)."), self._label)

        self._auto_sort_by_sender = QCheckBox()
        layout.addRow(create_field_label("Auto-Sort by Sender:", "Auto-Sort By Sender", "Dynamically determines the folder name by parsing the sender domain or email handle."), self._auto_sort_by_sender)

        # Populate if editing
        if rule:
            self._name.setText(rule.get("name", ""))
            match = rule.get("match", {})
            self._from.setText(self._val_to_str(match.get("from", "")))
            self._to.setText(self._val_to_str(match.get("to", "")))
            self._subject.setText(self._val_to_str(match.get("subject", "")))
            self._body.setText(self._val_to_str(match.get("body", "")))
            self._ai_prompt.setText(match.get("ai_prompt", ""))
            self._days_older.setValue(match.get("days_older", 0))

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
        if self._days_older.value() > 0:
            match["days_older"] = self._days_older.value()

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


class AutoSortConfigDialog(QDialog):
    """Dialog for configuring how auto-sort dynamically names target folders."""
    def __init__(self, current_config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Auto-Sort")
        self.setMinimumWidth(380)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItem("Full Sender Email (e.g. user@domain.com)", "full_email")
        self.strategy_combo.addItem("Sender Domain Only (e.g. domain.com)", "domain")
        self.strategy_combo.addItem("Sender Name (e.g. John Doe)", "sender_name")
        self.strategy_combo.addItem("Full Subject Line", "subject")
        self.strategy_combo.addItem("First Word of Subject", "subject_first_word")
        
        # Load existing selection
        current_strat = "full_email"
        if isinstance(current_config, dict):
            current_strat = current_config.get("strategy", "full_email")
            
        index = self.strategy_combo.findData(current_strat)
        if index >= 0:
            self.strategy_combo.setCurrentIndex(index)
            
        form.addRow(create_field_label("Naming Strategy:", "Naming Strategy", "Determines what attribute of the incoming email should be parsed to create the folder name on your email server."), self.strategy_combo)
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def get_config(self) -> dict:
        return {"strategy": self.strategy_combo.currentData()}


class ContentRulesConfigDialog(QDialog):
    """Dialog for configuring content-based rules."""
    def __init__(self, current_config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Content-Based Rules")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.rules = {
            "Promotions & Social": {
                "subject": ["promotion", "sale", "newsletter", "offer", "deals", "discount"],
                "from": ["*@facebook.com", "*@linkedin.com", "*@twitter.com", "*@instagram.com", "*@pinterest.com"]
            },
            "High-Priority": {
                "subject": ["urgent", "action required", "important", "response needed"]
            },
            "Junk": {
                "subject": ["unsubscribe from our mailing list", "confirm your unsubscription"]
            },
            "Calendar": {
                "subject": ["invitation", "meeting", "calendar", "webinar", "event"]
            }
        }
        
        self.widgets = {}
        for rule_name, conditions in self.rules.items():
            rule_config = current_config.get(rule_name, {})
            enabled = rule_config.get("enabled", False)
            keywords = rule_config.get("keywords", {})
            
            enable_checkbox = QCheckBox(f"Enable {rule_name} Rule")
            enable_checkbox.setChecked(enabled)
            form.addRow(enable_checkbox)
            self.widgets[rule_name] = {"enabled": enable_checkbox, "keywords": {}}
            for condition, default_keywords in conditions.items():
                current_keywords = keywords.get(condition, default_keywords)
                keyword_edit = QLineEdit(", ".join(current_keywords))
                form.addRow(f"    {condition.capitalize()} Keywords:", keyword_edit)
                self.widgets[rule_name]["keywords"][condition] = keyword_edit
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_config(self) -> dict:
        config = {}
        for rule_name, widgets in self.widgets.items():
            config[rule_name] = {
                "enabled": widgets["enabled"].isChecked(),
                "keywords": {
                    condition: [kw.strip() for kw in widget.text().split(",")]
                    for condition, widget in widgets["keywords"].items()
                }
            }
        return config

class OfficeRulesConfigDialog(QDialog):
    """Dialog for configuring office-based rules."""
    def __init__(self, current_config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Office-Based Rules")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.rules = {
            "Meeting Prep": {
                "subject": ["meeting", "agenda", "calendar", "sync", "standup", "huddle"],
                "body": ["please find the agenda", "zoom.us/j", "meet.google.com"]
            },
            "Client Follow-ups": {
                "subject": ["checking in", "following up", "status update"]
            },
            "Team Collaboration": {
                "subject": ["team", "collab", "brainstorm", "project sync"]
            },
            "Expense / Finance": {
                "subject": ["invoice", "receipt", "payment", "reimbursement", "expense"]
            },
            "Urgent Deadlines": {
                "subject": ["due today", "immediate", "urgent", "action required", "eod", "asap"]
            },
            "Recurring Reports": {
                "subject": ["weekly report", "monthly report", "analytics summary"]
            },
            "Internal Memos": {
                "subject": ["all-hands", "company update", "policy change", "memo"]
            },
            "Low Priority Notifications": {
                "subject": ["system update", "maintenance", "alert"]
            },
            "Follow-up Chains": {
                "subject": ["re:"]
            },
            "Flag Unusual Sender": {
                "subject": ["introduction", "new contact"]
            }
        }
        
        self.widgets = {}
        for rule_name, conditions in self.rules.items():
            rule_config = current_config.get(rule_name, {})
            enabled = rule_config.get("enabled", False)
            keywords = rule_config.get("keywords", {})
            
            enable_checkbox = QCheckBox(f"Enable {rule_name} Rule")
            enable_checkbox.setChecked(enabled)
            form.addRow(enable_checkbox)
            self.widgets[rule_name] = {"enabled": enable_checkbox, "keywords": {}}
            for condition, default_keywords in conditions.items():
                current_keywords = keywords.get(condition, default_keywords)
                keyword_edit = QLineEdit(", ".join(current_keywords))
                form.addRow(f"    {condition.capitalize()} Keywords:", keyword_edit)
                self.widgets[rule_name]["keywords"][condition] = keyword_edit
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_config(self) -> dict:
        config = {}
        for rule_name, widgets in self.widgets.items():
            config[rule_name] = {
                "enabled": widgets["enabled"].isChecked(),
                "keywords": {
                    condition: [kw.strip() for kw in widget.text().split(",") if kw.strip()]
                    for condition, widget in widgets["keywords"].items()
                }
            }
        return config

class RulesTab(QWidget):
    """CRUD table for email rules."""

    def __init__(self, agent_core: AgentCore, parent=None):
        super().__init__(parent)
        self._agent_core = agent_core
        self._rules_path = Path(self._agent_core.config.config_dir) / "rules.yaml"
        self._rules: list[dict] = []
        self._current_content_rules_config = {}
        self._current_office_rules_config = {}

        layout = QVBoxLayout(self)

        # Auto-sort panel
        auto_sort_frame = QFrame()
        auto_sort_frame.setFrameShape(QFrame.Shape.StyledPanel)
        auto_sort_frame.setStyleSheet(
            "QFrame { background-color: #1e1e1e; border: 1px solid #333333;"
            " border-radius: 6px; padding: 8px; }"
        )
        auto_sort_layout = QVBoxLayout(auto_sort_frame)
        auto_sort_layout.setContentsMargins(10, 8, 10, 8)

        header_row = QHBoxLayout()
        auto_sort_label = QLabel("<b>Auto-Sort by Sender</b>")
        header_row.addWidget(auto_sort_label)
        header_row.addStretch()
        
        self._auto_sort_config_btn = QPushButton("Configure")
        self._auto_sort_config_btn.clicked.connect(self._configure_auto_sort)
        header_row.addWidget(self._auto_sort_config_btn)
        
        self._auto_sort_toggle = QCheckBox("Enable")
        self._auto_sort_toggle.toggled.connect(self._on_auto_sort_toggled)
        header_row.addWidget(self._auto_sort_toggle)
        auto_sort_layout.addLayout(header_row)

        self._current_auto_sort_config = True

        desc = QLabel(
            "Automatically move emails into folders named after the sender's "
            "email address. Only applies when no other rule matches. "
            "Folders are created on the mail server if they don't exist."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #a0a0a0; font-size: 13px;")
        auto_sort_layout.addWidget(desc)

        layout.addWidget(auto_sort_frame)

        # Content-based rules panel
        content_rules_frame = QFrame()
        content_rules_frame.setFrameShape(QFrame.Shape.StyledPanel)
        content_rules_frame.setStyleSheet(
            "QFrame { background-color: #1e1e1e; border: 1px solid #333333;"
            " border-radius: 6px; padding: 8px; }"
        )
        content_rules_layout = QVBoxLayout(content_rules_frame)
        content_rules_layout.setContentsMargins(10, 8, 10, 8)

        content_header_row = QHBoxLayout()
        content_rules_label = QLabel("<b>Content-Based Rules</b>")
        content_header_row.addWidget(content_rules_label)
        content_header_row.addStretch()

        self._content_rules_config_btn = QPushButton("Configure")
        self._content_rules_config_btn.clicked.connect(self._configure_content_rules)
        content_header_row.addWidget(self._content_rules_config_btn)

        content_rules_layout.addLayout(content_header_row)

        content_desc = QLabel(
            "Enable and configure pre-defined rules for common email types like promotions, social media, and more."
        )
        content_desc.setWordWrap(True)
        content_desc.setStyleSheet("color: #a0a0a0; font-size: 13px;")
        content_rules_layout.addWidget(content_desc)

        layout.addWidget(content_rules_frame)

        # Office-based rules panel
        office_rules_frame = QFrame()
        office_rules_frame.setFrameShape(QFrame.Shape.StyledPanel)
        office_rules_frame.setStyleSheet(
            "QFrame { background-color: #1e1e1e; border: 1px solid #333333;"
            " border-radius: 6px; padding: 8px; }"
        )
        office_rules_layout = QVBoxLayout(office_rules_frame)
        office_rules_layout.setContentsMargins(10, 8, 10, 8)

        office_header_row = QHBoxLayout()
        office_rules_label = QLabel("<b>Office-Based Rules</b>")
        office_header_row.addWidget(office_rules_label)
        office_header_row.addStretch()

        self._office_rules_config_btn = QPushButton("Configure")
        self._office_rules_config_btn.clicked.connect(self._configure_office_rules)
        office_header_row.addWidget(self._office_rules_config_btn)

        office_rules_layout.addLayout(office_header_row)

        office_desc = QLabel(
            "Enable and configure pre-defined workspace rules for business workflow like Meeting Prep, Financials, and Urgent Deadlines."
        )
        office_desc.setWordWrap(True)
        office_desc.setStyleSheet("color: #a0a0a0; font-size: 13px;")
        office_rules_layout.addWidget(office_desc)

        layout.addWidget(office_rules_frame)

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
        self._table.verticalHeader().setVisible(False)
        layout.addWidget(self._table, stretch=1)

        self._load()

    def _load(self):
        try:
            self._rules = load_rules(self._rules_path)
        except Exception:
            self._rules = []
            
        # Extract existing config status if present
        has_auto_sort = False
        for r in self._rules:
            if r["name"] == AUTO_SORT_RULE_NAME:
                has_auto_sort = True
                self._current_auto_sort_config = r.get("action", {}).get("auto_sort_by_sender", True)
            elif r["name"] == CONTENT_RULES_NAME:
                self._current_content_rules_config = r.get("action", {}).get("content_based_rules", {})
            elif r["name"] == OFFICE_RULES_NAME:
                self._current_office_rules_config = r.get("action", {}).get("office_based_rules", {})

        if not hasattr(self, '_current_auto_sort_config'):
            self._current_auto_sort_config = True

        self._auto_sort_toggle.blockSignals(True)
        self._auto_sort_toggle.setChecked(has_auto_sort)
        self._auto_sort_toggle.blockSignals(False)
        self._refresh_table()

    def _configure_auto_sort(self):
        # Open dialog pushing the memory struct
        dlg = AutoSortConfigDialog(self._current_auto_sort_config, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._current_auto_sort_config = dlg.get_config()
            
            # If enabled, update the appended rule immediately
            if self._auto_sort_toggle.isChecked():
                for r in self._rules:
                    if r["name"] == AUTO_SORT_RULE_NAME:
                        r["action"]["auto_sort_by_sender"] = self._current_auto_sort_config
                self._save()
                self._refresh_table()

    def _configure_content_rules(self):
        dlg = ContentRulesConfigDialog(self._current_content_rules_config, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._current_content_rules_config = dlg.get_config()
            self._save()
            self._refresh_table()

    def _configure_office_rules(self):
        dlg = OfficeRulesConfigDialog(self._current_office_rules_config, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._current_office_rules_config = dlg.get_config()
            self._save()
            self._refresh_table()

    def _user_rules(self) -> list[dict]:
        """Return rules excluding the auto-sort rule."""
        return [r for r in self._rules if r["name"] not in (AUTO_SORT_RULE_NAME, CONTENT_RULES_NAME, OFFICE_RULES_NAME)]

    def _refresh_table(self):
        visible = self._user_rules()
        self._table.setRowCount(len(visible))
        for row, rule in enumerate(visible):
            self._table.setItem(row, 0, QTableWidgetItem(rule["name"]))
            self._table.setItem(row, 1, QTableWidgetItem(_summarize_match(rule["match"])))
            self._table.setItem(row, 2, QTableWidgetItem(_summarize_action(rule["action"])))

    def _save(self):
        # Update content-based rules
        content_rule_found = False
        office_rule_found = False
        
        for r in self._rules:
            if r["name"] == CONTENT_RULES_NAME:
                r["action"]["content_based_rules"] = self._current_content_rules_config
                content_rule_found = True
            elif r["name"] == OFFICE_RULES_NAME:
                r["action"]["office_based_rules"] = self._current_office_rules_config
                office_rule_found = True

        if not content_rule_found and self._current_content_rules_config:
            self._rules.append({
                "name": CONTENT_RULES_NAME,
                "match": {},
                "action": {"content_based_rules": self._current_content_rules_config}
            })
            
        if not office_rule_found and self._current_office_rules_config:
            self._rules.append({
                "name": OFFICE_RULES_NAME,
                "match": {},
                "action": {"office_based_rules": self._current_office_rules_config}
            })
        
        save_rules(self._rules_path, self._rules)

    def _on_auto_sort_toggled(self, checked: bool):
        """Add or remove the auto-sort rule based on toggle state."""
        # Remove existing auto-sort rule if present
        self._rules = [r for r in self._rules if r["name"] != AUTO_SORT_RULE_NAME]
        if checked:
            # Append as last rule (catch-all) using memory state
            self._rules.append({
                "name": AUTO_SORT_RULE_NAME,
                "match": {"from": "*"},
                "action": {"auto_sort_by_sender": getattr(self, "_current_auto_sort_config", True)},
            })
        self._save()
        self._refresh_table()

    def _add_rule(self):
        if self._agent_core.state == AgentState.RUNNING:
            self._show_restart_warning()
            return
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
        if self._agent_core.state == AgentState.RUNNING:
            self._show_restart_warning()
            return
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
        if self._agent_core.state == AgentState.RUNNING:
            self._show_restart_warning()
            return
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

    def _show_restart_warning(self):
        QMessageBox.warning(
            self, "Agent Running",
            "Please stop the agent before modifying rules. Changes will apply after a restart."
        )
