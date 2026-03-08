"""Settings tab: poll interval, model, dry-run, log level, auto-start."""

import logging

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QFormLayout, QGroupBox, QLabel,
    QLineEdit, QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from open_email.agent_core import AgentConfig
from open_email.gui.widgets.ui_helpers import create_field_label

logger = logging.getLogger("open_email")


class SettingsTab(QWidget):
    """Settings panel for agent configuration."""

    config_changed = pyqtSignal(object)  # AgentConfig

    def __init__(self, config: AgentConfig, parent=None):
        super().__init__(parent)
        self._config = config

        layout = QVBoxLayout(self)

        # --- Agent settings ---
        agent_group = QGroupBox("Agent Settings")
        agent_form = QFormLayout(agent_group)

        self._interval = QSpinBox()
        self._interval.setRange(10, 3600)
        self._interval.setSuffix(" seconds")
        self._interval.setValue(config.interval)
        agent_form.addRow(
            create_field_label(
                "Poll Interval:",
                "Poll Interval",
                "How frequently InboxAgent should check your email accounts for new messages. "
                "Settings this too low may cause you to be rate-limited by your email provider. "
                "60-120 seconds is generally recommended."
            ),
            self._interval
        )

        self._model = QLineEdit(config.model)
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
        self._dry_run.setChecked(config.dry_run)
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
        self._log_level.setCurrentText(config.log_level)
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

        self._config_dir = QLineEdit(config.config_dir)
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

        # Apply button
        apply_btn = QPushButton("Apply Settings")
        apply_btn.clicked.connect(self._apply)
        layout.addWidget(apply_btn)

        layout.addStretch()

    def _apply(self):
        new_config = AgentConfig(
            config_dir=self._config_dir.text().strip(),
            interval=self._interval.value(),
            dry_run=self._dry_run.isChecked(),
            model=self._model.text().strip(),
            uid_file=self._config.uid_file,
            log_level=self._log_level.currentText(),
        )
        self._config = new_config
        self._apply_log_level(new_config.log_level)
        self.config_changed.emit(new_config)
        logger.info("Settings applied: interval=%ds, model=%s, dry_run=%s",
                     new_config.interval, new_config.model, new_config.dry_run)

    def _apply_log_level(self, level: str):
        logging.getLogger("open_email").setLevel(getattr(logging, level, logging.INFO))

    def _toggle_autostart(self, enabled: bool):
        try:
            from open_email.platform.autostart import set_autostart
            set_autostart(enabled)
            logger.info("Auto-start %s", "enabled" if enabled else "disabled")
        except Exception as e:
            logger.warning("Failed to set auto-start: %s", e)
