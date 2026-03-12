"""Rule actions: move, flag, delete, etc."""

import logging

logger = logging.getLogger(__name__)

def move_to(client, uid: str, dest_folder: str, dry_run: bool):
    if not dry_run:
        client.move_email(uid, dest_folder)
    logger.info("Moved email UID %s to %s", uid, dest_folder)

def flag_email(client, uid: str, dry_run: bool):
    if not dry_run:
        client.flag_email(uid)
    logger.info("Flagged email UID %s", uid)

def delete_email(client, uid: str, dry_run: bool):
    if not dry_run:
        client.delete_email(uid)
    logger.info("Deleted email UID %s", uid)

def mark_as_read(client, uid: str, dry_run: bool):
    if not dry_run:
        client.mark_read(uid)
    logger.info("Marked email UID %s as read", uid)

def mark_as_unread(client, uid: str, dry_run: bool):
    if not dry_run:
        client.mark_unread(uid)
    logger.info("Marked email UID %s as unread", uid)

def add_label(client, uid: str, label: str, dry_run: bool):
    if not dry_run:
        client.add_label(uid, label)
    logger.info("Labeled email UID %s with '%s'", uid, label)

def execute_actions(client, uid: str, action: dict, dry_run: bool, stats, parsed_email):
    """Execute the actions defined in a rule."""
    if action.get("delete"):
        delete_email(client, uid, dry_run)
        stats.actions_taken.append(f"Deleted email from {parsed_email.from_addr}")
        return

    if "move_to" in action:
        move_to(client, uid, action["move_to"], dry_run)
        stats.actions_taken.append(f"Moved email to '{action['move_to']}'")

    if action.get("flag"):
        flag_email(client, uid, dry_run)
        stats.actions_taken.append(f"Flagged email from {parsed_email.from_addr}")

    if action.get("mark_read"):
        mark_as_read(client, uid, dry_run)
        stats.actions_taken.append(f"Marked email from {parsed_email.from_addr} as read")

    if action.get("mark_unread"):
        mark_as_unread(client, uid, dry_run)
        stats.actions_taken.append(f"Marked email from {parsed_email.from_addr} as unread")

    if "label" in action:
        add_label(client, uid, action["label"], dry_run)
        stats.actions_taken.append(f"Labeled email from {parsed_email.from_addr} with '{action['label']}'")