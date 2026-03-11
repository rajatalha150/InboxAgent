"""Entry point for the InboxAgent application."""

import argparse
import logging
import signal
import sys

from open_email.agent_core import AgentConfig, AgentCore

logger = logging.getLogger("open_email")

_agent: AgentCore | None = None


def _handle_signal(signum, frame):
    logger.info("Received signal %d, shutting down gracefully...", signum)
    if _agent:
        _agent.request_stop()


def run_cli(config: AgentConfig) -> None:
    """Run the agent in CLI mode (blocking)."""
    global _agent
    _agent = AgentCore(config)
    _agent.run()


def launch_gui(config: AgentConfig, minimized: bool = False) -> None:
    """Launch the PyQt6 GUI application."""
    try:
        from open_email.gui.app import run_app
    except ImportError as e:
        msg = f"GUI dependencies not installed or DLL load failed.\nError: {e}\n\nPlease install: pip install inbox-agent[gui]"
        print(msg, file=sys.stderr)
        
        # Keep terminal open if frozen so user can read it
        if getattr(sys, 'frozen', False):
            try:
                import ctypes
                ctypes.windll.user32.MessageBoxW(0, msg, "InboxAgent Boot Error", 0x10)
            except:
                import time
                time.sleep(15)
        sys.exit(1)
    run_app(config, minimized=minimized)


def main():
    parser = argparse.ArgumentParser(
        prog="inbox-agent",
        description="InboxAgent - Privacy-first local AI email organization agent",
    )
    import os
    if getattr(sys, 'frozen', False):
        # For installed app, use user's AppData roaming dir
        default_config = os.path.join(os.getenv('APPDATA'), 'InboxAgent')
    else:
        # For development, use local config dir
        default_config = "config"
        
    parser.add_argument(
        "--config-dir", default=default_config,
        help=f"Path to config directory (default: {default_config})",
    )
    parser.add_argument(
        "--interval", type=int, default=60,
        help="Poll interval in seconds (default: 60)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Log actions without executing them",
    )
    parser.add_argument(
        "--model", default="llama3.2:3b",
        help="Ollama model for AI classification (default: llama3.2:3b)",
    )
    parser.add_argument(
        "--uid-file", default="processed_uids.json",
        help="Path to processed UIDs tracking file (default: processed_uids.json)",
    )
    parser.add_argument(
        "--log-level", default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )
    parser.add_argument(
        "--batch-size", type=int, default=1000,
        help="Maximum number of emails to process per cycle (default: 1000)",
    )
    parser.add_argument(
        "--gui", action="store_true",
        help="Launch the desktop GUI instead of CLI mode",
    )
    parser.add_argument(
        "--minimized", action="store_true",
        help="Start GUI minimized to system tray (implies --gui)",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    config = AgentConfig(
        config_dir=args.config_dir,
        interval=args.interval,
        dry_run=args.dry_run,
        model=args.model,
        uid_file=args.uid_file,
        log_level=args.log_level,
        batch_size=args.batch_size,
    )

    if args.gui or args.minimized:
        launch_gui(config, minimized=args.minimized)
    else:
        run_cli(config)


def main_gui():
    """Entry point for gui-scripts (always launches GUI)."""
    sys.argv.append("--gui")
    main()


if __name__ == "__main__":
    import sys
    import os
    # If compiled as frozen exe and double-clicked (no args), auto-launch GUI
    if getattr(sys, 'frozen', False):
        # Explicitly register PyQt6 dll path to help Windows loader
        pyqt_bin = os.path.join(getattr(sys, '_MEIPASS', os.path.dirname(sys.executable)), 'PyQt6', 'Qt6', 'bin')
        if os.path.exists(pyqt_bin):
            os.add_dll_directory(pyqt_bin)
            
        if len(sys.argv) == 1:
            sys.argv.append("--gui")
    main()
