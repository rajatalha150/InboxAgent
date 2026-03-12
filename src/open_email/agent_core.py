"""Extracted agent loop with callback hooks for GUI integration."""

import json
import logging
import threading
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from open_email.actions import execute_actions
from open_email.ai_classifier import AIClassifier
from open_email.config_loader import load_accounts, load_rules
from open_email.email_parser import parse_email
from open_email.imap_client import EmailClient
from open_email.rule_engine import evaluate_rules

logger = logging.getLogger("open_email")


@dataclass
class AgentConfig:
    """Configuration for the agent core."""

    config_dir: str = "config"
    interval: int = 60
    batch_size: int = 1000
    poll_interval_mode: str = "fixed"  # fixed, dynamic, aggressive
    dry_run: bool = False
    model: str = "llama3.2:3b"
    uid_file: str = "processed_uids.json"
    log_level: str = "INFO"


from open_email import summary

@dataclass
class AgentStats:
    """Statistics for an agent run."""

    start_time: float = field(default_factory=time.time)
    cycles_completed: int = 0
    emails_processed: int = 0
    errors: int = 0
    accounts_connected: int = 0
    rules_triggered: int = 0
    actions_taken: list[str] = field(default_factory=list)

    @property
    def uptime(self) -> str:
        """Return human-readable uptime."""
        seconds = int(time.time() - self.start_time)
        if seconds < 60:
            return f"{seconds}s"
        minutes, seconds = divmod(seconds, 60)
        if minutes < 60:
            return f"{minutes}m {seconds}s"
        hours, minutes = divmod(minutes, 60)
        return f"{hours}h {minutes}m"


class AgentState:
    """Thread-safe agent state."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"

    def __init__(self):
        self._state = self.STOPPED
        self._lock = threading.Lock()

    @property
    def state(self) -> str:
        with self._lock:
            return self._state

    @state.setter
    def state(self, value: str):
        with self._lock:
            self._state = value


class AgentCore:
    """Core agent loop, decoupled from CLI/GUI.

    Callbacks:
        on_state_change(state: str)
        on_stats_update(stats: AgentStats)
        on_activity(message: str)
        on_error(message: str)
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self.stats = AgentStats()
        self.agent_state = AgentState()
        self._stop_event = threading.Event()

        # Callbacks (set by GUI or CLI)
        self.on_state_change = None
        self.on_stats_update = None
        self.on_activity = None
        self.on_error = None
        self.on_error_detail = None

    def _emit_state(self, state: str):
        self.agent_state.state = state
        if self.on_state_change:
            self.on_state_change(state)

    def _emit_stats(self):
        if self.on_stats_update:
            self.on_stats_update(self.stats)

    def _emit_activity(self, msg: str):
        if self.on_activity:
            self.on_activity(msg)

    def _emit_error(self, msg: str, detail: str = ""):
        if self.on_error:
            self.on_error(msg)
        if detail and self.on_error_detail:
            self.on_error_detail(msg, detail)

    @property
    def state(self) -> str:
        return self.agent_state.state

    def request_stop(self):
        """Request the agent to stop gracefully."""
        self._stop_event.set()

    def _save_summary(self, summary_text: str):
        """Save the cycle summary to a timestamped file."""
        summaries_dir = Path(self.config.config_dir) / "summaries"
        summaries_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        summary_file = summaries_dir / f"summary_{timestamp}.json"
        with open(summary_file, "w") as f:
            json.dump({"timestamp": timestamp, "summary": summary_text}, f, indent=4)
        logger.info("Saved cycle summary to %s", summary_file)

    def run(self):
        """Main agent loop. Blocks until stopped or error."""
        self._stop_event.clear()
        self.stats = AgentStats()
        self._emit_state(AgentState.STARTING)
        self._emit_stats()

        config_dir = Path(self.config.config_dir)

        try:
            accounts = load_accounts(config_dir / "accounts.yaml")
            rules = load_rules(config_dir / "rules.yaml")
        except Exception as e:
            msg = f"Failed to load config: {e}"
            logger.error(msg)
            self._emit_error(msg, traceback.format_exc())
            self._emit_state(AgentState.ERROR)
            return

        ai_classifier = AIClassifier(model=self.config.model)

        # Connect to accounts
        clients: list[EmailClient] = []
        for account in accounts:
            client = EmailClient(account)
            try:
                client.connect()
                clients.append(client)
                self._emit_activity(f"Connected to {account['name']}")
            except ConnectionError as e:
                msg = f"Skipping account '{account['name']}': {e}"
                logger.error(msg)
                self._emit_error(msg, traceback.format_exc())

        if not clients:
            msg = "No accounts connected successfully."
            logger.error(msg)
            self._emit_error(msg, "All account connections failed. Check credentials and server settings.")
            self._emit_state(AgentState.ERROR)
            return

        self.stats.accounts_connected = len(clients)

        # Load processed UIDs
        self.uid_file = Path(self.config.config_dir) / self.config.uid_file
        all_processed = self._load_processed_uids()

        self._emit_state(AgentState.RUNNING)
        self._emit_stats()
        logger.info("Agent started. Poll interval: %ds. Dry run: %s",
                     self.config.interval, self.config.dry_run)

        try:
            while not self._stop_event.is_set():
                for client in clients:
                    if self._stop_event.is_set():
                        break
                    account_name = client.name
                    processed = set(all_processed.get(account_name, []))

                    newly_processed = self._process_account(
                        client, rules, ai_classifier, processed
                    )

                    if newly_processed:
                        processed.update(newly_processed)
                        all_processed[account_name] = list(processed)
                        self._save_processed_uids(all_processed)

                self.stats.cycles_completed += 1
                self._emit_stats()

                # Generate and save summary
                if self.stats.actions_taken:
                    summary_text = summary.generate_summary(self.stats.actions_taken)
                    self._save_summary(summary_text)
                    self.stats.actions_taken.clear()

                # Dynamic sleep interval
                interval = self._get_current_interval()

                # Wait for next poll (check stop every second)
                for _ in range(interval):
                    if self._stop_event.is_set():
                        break
                    time.sleep(1)
        finally:
            self._emit_state(AgentState.STOPPING)
            for client in clients:
                client.disconnect()
            self._emit_state(AgentState.STOPPED)
            self._emit_stats()
            logger.info("Agent stopped.")

    def _get_current_interval(self) -> int:
        """Return the sleep interval based on the current mode and time."""
        mode = self.config.poll_interval_mode
        if mode == "aggressive":
            return 15  # Very frequent

        if mode == "dynamic":
            now = datetime.now()
            # Business hours (8am - 6pm)
            if 8 <= now.hour < 18:
                return 60  # Frequent
            return 600  # Infrequent

        # Fixed mode
        return self.config.interval

    def _process_account(
        self,
        client: EmailClient,
        rules: list[dict],
        ai_classifier: AIClassifier,
        processed_uids: set[int],
    ) -> set[int]:
        """Process new emails for a single account."""
        newly_processed = set()

        try:
            all_uids = client.fetch_uids("INBOX")
        except Exception as e:
            msg = f"[{client.name}] Failed to fetch UIDs: {e}"
            logger.error(msg)
            self._emit_error(msg, traceback.format_exc())
            self.stats.errors += 1
            return newly_processed

        new_uids = [uid for uid in all_uids if uid not in processed_uids]
        if not new_uids:
            logger.debug("[%s] No new emails", client.name)
            return newly_processed

        logger.info("[%s] Found %d new email(s)", client.name, len(new_uids))

        # Limit to batch size
        uids_to_process = new_uids[: self.config.batch_size]
        logger.info("Processing next batch of %d email(s)", len(uids_to_process))

        for uid in uids_to_process:
            if self._stop_event.is_set():
                break
            try:
                raw = client.fetch_raw_email(uid)
                parsed = parse_email(uid, raw)
                activity = f"[{client.name}] Processing: '{parsed.subject}' from {parsed.from_addr}"
                logger.info(activity)
                self._emit_activity(activity)

                matches = evaluate_rules(parsed, rules, ai_classifier)

                if matches:
                    for match in matches:
                        rule_msg = f"[{client.name}] Rule '{match['name']}' triggered for UID {uid}"
                        logger.info(rule_msg)
                        self._emit_activity(rule_msg)
                        self.stats.rules_triggered += 1
                        execute_actions(
                            client, uid, match["action"],
                            dry_run=self.config.dry_run,
                            stats=self.stats,
                            parsed_email=parsed
                        )
                else:
                    logger.debug("[%s] No rules matched UID %d", client.name, uid)

                newly_processed.add(uid)
                self.stats.emails_processed += 1
                self._emit_stats()

            except Exception as e:
                msg = f"[{client.name}] Error processing UID {uid}: {e}"
                logger.error(msg)
                self._emit_error(msg, traceback.format_exc())
                self.stats.errors += 1

        return newly_processed

    def _load_processed_uids(self) -> dict[str, set[str]]:
        """Load the set of processed UIDs from file for all accounts."""
        if not self.uid_file.exists():
            return {}
        try:
            with open(self.uid_file) as f:
                data = json.load(f)
                if isinstance(data, list):
                    logger.warning("Old UID format detected, converting to new format.")
                    return {"default": set(data)} # Convert old list format
                return {account: set(uids) for account, uids in data.items()}
        except (json.JSONDecodeError, IOError) as e:
            logger.warning("Could not load processed UIDs, starting fresh: %s", e)
            return {}

    def _save_processed_uids(self, all_uids: dict[str, set[str]]):
        """Save the set of processed UIDs to file for all accounts."""
        try:
            with open(self.uid_file, "w") as f:
                data_to_save = {account: list(uids) for account, uids in all_uids.items()}
                json.dump(data_to_save, f)
        except IOError as e:
            logger.error("Could not save processed UIDs to %s: %s", self.uid_file, e)
