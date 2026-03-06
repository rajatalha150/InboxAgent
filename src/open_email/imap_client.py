"""IMAP client for connecting to email servers and fetching messages."""

import logging
import time

from imapclient import IMAPClient

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds


class EmailClient:
    """Manages an IMAP connection to a single email account."""

    def __init__(self, account: dict):
        self.account = account
        self.name = account["name"]
        self.server = account["imap_server"]
        self.port = account["imap_port"]
        self.email = account["email"]
        self.password = account["password"]
        self.ssl = account["ssl"]
        self.client: IMAPClient | None = None

    def connect(self) -> None:
        """Establish IMAP connection with retries."""
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info("[%s] Connecting to %s:%d (attempt %d)", self.name, self.server, self.port, attempt)
                self.client = IMAPClient(self.server, port=self.port, ssl=self.ssl)
                self.client.login(self.email, self.password)
                logger.info("[%s] Connected successfully", self.name)
                return
            except Exception as e:
                logger.warning("[%s] Connection attempt %d failed: %s", self.name, attempt, e)
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
                else:
                    raise ConnectionError(f"[{self.name}] Failed to connect after {MAX_RETRIES} attempts") from e

    def ensure_connected(self) -> None:
        """Reconnect if the connection was lost."""
        if self.client is None:
            self.connect()
            return
        try:
            self.client.noop()
        except Exception:
            logger.info("[%s] Connection lost, reconnecting...", self.name)
            self.client = None
            self.connect()

    def fetch_uids(self, folder: str = "INBOX") -> list[int]:
        """Fetch all message UIDs from the given folder."""
        self.ensure_connected()
        self.client.select_folder(folder, readonly=False)
        uids = self.client.search(["ALL"])
        return uids

    def fetch_raw_email(self, uid: int) -> bytes:
        """Fetch the raw RFC822 message bytes for a given UID."""
        self.ensure_connected()
        messages = self.client.fetch([uid], ["RFC822"])
        return messages[uid][b"RFC822"]

    def move_email(self, uid: int, destination_folder: str) -> None:
        """Move an email to a destination folder (COPY + delete from current)."""
        self.ensure_connected()
        self._ensure_folder_exists(destination_folder)
        self.client.copy([uid], destination_folder)
        self.client.set_flags([uid], [b"\\Deleted"])
        self.client.expunge([uid])
        logger.info("[%s] Moved UID %d to %s", self.name, uid, destination_folder)

    def flag_email(self, uid: int, flagged: bool = True) -> None:
        """Set or remove the flagged status on an email."""
        self.ensure_connected()
        if flagged:
            self.client.add_flags([uid], [b"\\Flagged"])
        else:
            self.client.remove_flags([uid], [b"\\Flagged"])
        logger.info("[%s] %s UID %d", self.name, "Flagged" if flagged else "Unflagged", uid)

    def delete_email(self, uid: int) -> None:
        """Delete an email (move to Trash or expunge)."""
        self.ensure_connected()
        # Try moving to Trash first; fall back to direct expunge
        trash_names = ["Trash", "[Gmail]/Trash", "Deleted Items", "Deleted"]
        moved = False
        for trash in trash_names:
            try:
                self.client.copy([uid], trash)
                moved = True
                break
            except Exception:
                continue

        self.client.set_flags([uid], [b"\\Deleted"])
        self.client.expunge([uid])
        logger.info("[%s] Deleted UID %d (moved to trash: %s)", self.name, uid, moved)

    def mark_read(self, uid: int) -> None:
        """Mark an email as read."""
        self.ensure_connected()
        self.client.add_flags([uid], [b"\\Seen"])

    def mark_unread(self, uid: int) -> None:
        """Mark an email as unread."""
        self.ensure_connected()
        self.client.remove_flags([uid], [b"\\Seen"])

    def add_label(self, uid: int, label: str) -> None:
        """Add a Gmail label to an email. Only works with Gmail IMAP."""
        self.ensure_connected()
        try:
            self.client.add_gmail_labels([uid], [label])
            logger.info("[%s] Added label '%s' to UID %d", self.name, label, uid)
        except Exception as e:
            logger.warning("[%s] Failed to add label '%s' to UID %d: %s (may not be Gmail)", self.name, label, uid, e)

    def _ensure_folder_exists(self, folder: str) -> None:
        """Create the folder if it doesn't exist."""
        try:
            self.client.create_folder(folder)
            logger.info("[%s] Created folder: %s", self.name, folder)
        except Exception:
            # Folder likely already exists
            pass

    def disconnect(self) -> None:
        """Close the IMAP connection."""
        if self.client:
            try:
                self.client.logout()
            except Exception:
                pass
            self.client = None
            logger.info("[%s] Disconnected", self.name)
