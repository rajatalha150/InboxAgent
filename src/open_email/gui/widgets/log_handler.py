"""Logging handler that bridges Python logging to Qt signals."""

import logging

from PyQt6.QtCore import QObject, pyqtSignal


class LogSignalEmitter(QObject):
    """QObject that emits log messages as Qt signals."""
    log_message = pyqtSignal(str)


class QtLogHandler(logging.Handler):
    """A logging.Handler that emits log records via a pyqtSignal.

    Usage:
        handler = QtLogHandler()
        handler.emitter.log_message.connect(some_slot)
        logging.getLogger().addHandler(handler)
    """

    def __init__(self, level=logging.DEBUG):
        super().__init__(level)
        self.emitter = LogSignalEmitter()
        self.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        ))

    def emit(self, record):
        try:
            msg = self.format(record)
            self.emitter.log_message.emit(msg)
        except Exception:
            self.handleError(record)
