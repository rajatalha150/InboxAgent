"""Execute email actions (move, flag, delete, etc.)."""

import logging

from open_email.imap_client import EmailClient

logger = logging.getLogger(__name__)


def execute_actions(
    client: EmailClient,
    uid: int,
    action: dict,
    dry_run: bool = False,
) -> None:
    """Execute the actions defined in a matched rule.

    Args:
        client: The IMAP client to use.
        uid: The email UID to act on.
        action: Action dict from the matched rule.
        dry_run: If True, log actions without executing them.
    """
    if action.get("delete"):
        if dry_run:
            logger.info("[DRY RUN] Would delete UID %d", uid)
        else:
            client.delete_email(uid)
        return  # No further actions needed after delete

    if "move_to" in action:
        folder = action["move_to"]
        if dry_run:
            logger.info("[DRY RUN] Would move UID %d to '%s'", uid, folder)
        else:
            client.move_email(uid, folder)

    if "flag" in action:
        flagged = action["flag"]
        if dry_run:
            logger.info("[DRY RUN] Would %s UID %d", "flag" if flagged else "unflag", uid)
        else:
            client.flag_email(uid, flagged)

    if action.get("mark_read"):
        if dry_run:
            logger.info("[DRY RUN] Would mark UID %d as read", uid)
        else:
            client.mark_read(uid)

    if action.get("mark_unread"):
        if dry_run:
            logger.info("[DRY RUN] Would mark UID %d as unread", uid)
        else:
            client.mark_unread(uid)

    if "label" in action:
        label = action["label"]
        if dry_run:
            logger.info("[DRY RUN] Would add label '%s' to UID %d", label, uid)
        else:
            client.add_label(uid, label)
