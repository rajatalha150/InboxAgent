"""Settings tab: poll interval, model, dry-run, log level, auto-start."""

import json
import logging
from pathlib import Path

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QFormLayout, QGroupBox, QLabel,
    QLineEdit, QMessageBox, QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from open_email.agent_core import AgentConfig, AgentCore
from open_email.gui.widgets.ui_helpers import create_field_label

logger = logging.getLogger("open_email")


class SettingsTab(QWidget):
    """Settings panel for agent configuration."""

    config_changed = pyqtSignal(object)  # AgentConfig

    def __init__(self, agent_core: AgentCore, parent=None):
        super().__init__(parent)
        self._agent_core = agent_core

        layout = QVBoxLayout(self)

        # --- Agent settings ---
        agent_group = QGroupBox("Agent Settings")
        agent_form = QFormLayout(agent_group)

        self._interval = QSpinBox()
        self._interval.setRange(10, 3600)
        self._interval.setSuffix(" seconds")
        self._interval.setValue(self._agent_core.config.interval)
        agent_form.addRow(
            create_field_label(
                "Poll Interval:",
                "Poll Interval & Cycles",
                "How frequently InboxAgent checks your email. "
                "Once the agent scans all connected accounts, it completes one 'Cycle' and "
                "enters a sleep phase for this exact Poll Interval length. "
                "Because it sleeps in 1-second ticks, clicking 'Stop Agent' immediately "
                "interrupts the wait time. Setting this interval too low (<60s) may cause your provider to permanently rate-limit your account."
            ), 
            self._interval
        )

        self._poll_interval_mode = QComboBox()
        self._poll_interval_mode.addItems(["Fixed", "Dynamic", "Aggressive"])
        self._poll_interval_mode.setCurrentText(self._agent_core.config.poll_interval_mode.capitalize())
        agent_form.addRow(
            create_field_label(
                "Poll Interval Mode:",
                "Poll Interval Mode",
                "'Fixed': Use the value above. 'Dynamic': Poll frequently during business hours, less at night. 'Aggressive': Poll very frequently.",
            ),
            self._poll_interval_mode,
        )

        self._batch_size = QSpinBox()
        self._batch_size.setRange(10, 10000)
        self._batch_size.setValue(self._agent_core.config.batch_size)
        agent_form.addRow(
            create_field_label(
                "Batch Size:",
                "Max Emails Per Cycle",
                "The maximum number of emails to process in a single cycle. Lower this if you have a very large inbox or are experiencing timeouts.",
            ),
            self._batch_size,
        )

        self._model = QLineEdit(self._agent_core.config.model)
        agent_form.addRow(
            create_field_label(
                "AI Model:",
                "AI Classification Model",
                "The Ollama local LLM wrapper model to use. You must have Ollama installed "
                "locally, and you must use 'ollama pull <model>' first. The default is 'llama3.2:3b'. "
                "Leave blank if you aren't using AI Prompt matching rules."
            ),
            self._model
        )

        self._dry_run = QCheckBox()
        self._dry_run.setChecked(self._agent_core.config.dry_run)
        agent_form.addRow(
            create_field_label(
                "Dry Run:",
                "Dry Run Mode",
                "When enabled, InboxAgent will process emails and log the actions it *would* take, "
                "but will not actually modify, move, or delete anything on the server. Safest for testing rules."
            ),
            self._dry_run
        )

        self._log_level = QComboBox()
        self._log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self._log_level.setCurrentText(self._agent_core.config.log_level)
        self._log_level.currentTextChanged.connect(self._apply_log_level)
        agent_form.addRow(
            create_field_label(
                "Log Level:",
                "Log Output Detail Level",
                "Set to DEBUG to see detailed processing information (like which rules evaluate to false "
                "and raw payloads). Change to ERROR for minimal console noise. 'INFO' is the default."
            ),
            self._log_level
        )

        self._config_dir = QLineEdit(self._agent_core.config.config_dir)
        agent_form.addRow(
            create_field_label(
                "Config Directory:",
                "Configuration Directory",
                "The folder where accounts.yaml and rules.yaml are stored. You must restart the agent "
                "(Stop and Start) to fully reload resources from a new directory location."
            ),
            self._config_dir
        )

        layout.addWidget(agent_group)

        # --- System settings ---
        system_group = QGroupBox("System")
        system_form = QFormLayout(system_group)

        self._autostart = QCheckBox("Start on boot")
        system_form.addRow("Auto-Start:", self._autostart)

        # Load current autostart state
        try:
            from open_email.platform.autostart import is_autostart_enabled
            self._autostart.setChecked(is_autostart_enabled())
        except Exception:
            pass

        self._autostart.toggled.connect(self._toggle_autostart)

        layout.addWidget(system_group)

        # --- Cache Management ---
        cache_group = QGroupBox("Cache Management")
        cache_form = QFormLayout(cache_group)

        clear_summaries_btn = QPushButton("Clear Cycle Summaries")
        clear_summaries_btn.clicked.connect(self._clear_summaries)
        cache_form.addRow(clear_summaries_btn)

        clear_uids_btn = QPushButton("Clear Processed Email History")
        clear_uids_btn.clicked.connect(self._clear_uids)
        cache_form.addRow(clear_uids_btn)

        clear_logs_btn = QPushButton("Clear Agent Logs")
        clear_logs_btn.clicked.connect(self._clear_logs)
        cache_form.addRow(clear_logs_btn)

        layout.addWidget(cache_group)

        # Apply button
        apply_btn = QPushButton("Apply Settings")
        apply_btn.clicked.connect(self._apply)
        layout.addWidget(apply_btn)

        layout.addStretch()

    def _apply(self):
        new_config = AgentConfig(
            config_dir=self._config_dir.text().strip(),
            interval=self._interval.value(),
            poll_interval_mode=self._poll_interval_mode.currentText().lower(),
            dry_run=self._dry_run.isChecked(),
            model=self._model.text().strip(),
            uid_file=self._agent_core.config.uid_file,
            log_level=self._log_level.currentText(),
            batch_size=self._batch_size.value(),
        )
        self._agent_core.config = new_config
        self._apply_log_level(new_config.log_level)
        self.config_changed.emit(new_config)
        logger.info("Settings applied: interval=%ds, model=%s, dry_run=%s, batch_size=%d",
                     new_config.interval, new_config.model, new_config.dry_run, new_config.batch_size)

    def _apply_log_level(self, level: str):
        logging.getLogger("open_email").setLevel(getattr(logging, level, logging.INFO))

    def _toggle_autostart(self, enabled: bool):
        try:
            from open_email.platform.autostart import set_autostart
            set_autostart(enabled)
            logger.info("Auto-start %s", "enabled" if enabled else "disabled")
        except Exception as e:
            logger.warning("Failed to set auto-start: %s", e)

    def _clear_summaries(self):
        """Delete all summary files."""
        reply = QMessageBox.question(self, "Confirm", "Are you sure you want to delete all cycle summaries?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return

        summaries_dir = Path(self._agent_core.config.config_dir) / "summaries"
        if not summaries_dir.exists():
            return
        for summary_file in summaries_dir.glob("summary_*.json"):
            summary_file.unlink()
        logger.info("Cleared all cycle summaries.")
        QMessageBox.information(self, "Success", "All cycle summaries have been deleted.")

    def _clear_uids(self):
        """Delete the processed UIDs file."""
        uid_file = Path(self._agent_core.config.config_dir) / self._agent_core.config.uid_file
        try:
            with open(uid_file, "w") as f:
                json.dump({}, f)
            logger.info("Cleared processed email history.")
            QMessageBox.information(self, "Success", "Processed email history has been cleared.")
        except Exception as e:
            logger.error("Failed to clear processed email history: %s", e)
            QMessageBox.warning(self, "Error", f"Failed to clear processed email history: {e}")

    def _clear_logs(self):
        """Delete the agent log file."""
        reply = QMessageBox.question(self, "Confirm", "Are you sure you want to delete the agent log file?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return

        log_file = Path(self._agent_core.config.config_dir) / "agent.log"
        if log_file.exists():
            try:
                log_file.unlink()
                logger.info("Cleared agent logs.")
                QMessageBox.information(self, "Success", "Agent logs have been cleared.")
            except Exception as e:
                logger.error("Failed to clear agent logs: %s", e)
                QMessageBox.warning(self, "Error", f"Failed to clear agent logs: {e}")
