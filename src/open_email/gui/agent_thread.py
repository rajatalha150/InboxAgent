"""QThread wrapper for AgentCore with Qt signal bridge."""

from PyQt6.QtCore import QThread, pyqtSignal

from open_email.agent_core import AgentConfig, AgentCore, AgentStats


class AgentThread(QThread):
    """Runs AgentCore in a separate thread, bridging callbacks to Qt signals."""

    state_changed = pyqtSignal(str)
    stats_updated = pyqtSignal(object)  # AgentStats
    activity = pyqtSignal(str)
    error = pyqtSignal(str)
    error_detail = pyqtSignal(str, str)

    def __init__(self, config: AgentConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self._core: AgentCore | None = None

    def run(self):
        self._core = AgentCore(self.config)
        self._core.on_state_change = self.state_changed.emit
        self._core.on_stats_update = self.stats_updated.emit
        self._core.on_activity = self.activity.emit
        self._core.on_error = self.error.emit
        self._core.on_error_detail = lambda s, d: self.error_detail.emit(s, d)
        self._core.run()

    def request_stop(self):
        """Request the agent to stop gracefully."""
        if self._core:
            self._core.request_stop()

    @property
    def agent_state(self) -> str:
        if self._core:
            return self._core.state
        return "stopped"
