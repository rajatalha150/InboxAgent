"""Entry point for the open-email agent."""

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
        print(f"GUI dependencies not installed. Install with: pip install open-email[gui]\nError: {e}", file=sys.stderr)
        sys.exit(1)
    run_app(config, minimized=minimized)


def main():
    parser = argparse.ArgumentParser(
        prog="open-email",
        description="Privacy-first local AI email organization agent",
    )
    parser.add_argument(
        "--config-dir", default="config",
        help="Path to config directory (default: config/)",
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
    main()
