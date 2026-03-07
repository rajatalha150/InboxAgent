"""Tests for actions module."""

from unittest.mock import MagicMock

from open_email.actions import execute_actions


def _make_client():
    client = MagicMock()
    client.name = "test-account"
    return client


class TestMoveAction:
    def test_move_to_folder(self):
        client = _make_client()
        execute_actions(client, uid=1, action={"move_to": "Archive"})
        client.move_email.assert_called_once_with(1, "Archive")

    def test_move_dry_run(self):
        client = _make_client()
        execute_actions(client, uid=1, action={"move_to": "Archive"}, dry_run=True)
        client.move_email.assert_not_called()


class TestFlagAction:
    def test_flag_email(self):
        client = _make_client()
        execute_actions(client, uid=1, action={"flag": True})
        client.flag_email.assert_called_once_with(1, True)

    def test_unflag_email(self):
        client = _make_client()
        execute_actions(client, uid=1, action={"flag": False})
        client.flag_email.assert_called_once_with(1, False)

    def test_flag_dry_run(self):
        client = _make_client()
        execute_actions(client, uid=1, action={"flag": True}, dry_run=True)
        client.flag_email.assert_not_called()


class TestDeleteAction:
    def test_delete_email(self):
        client = _make_client()
        execute_actions(client, uid=1, action={"delete": True})
        client.delete_email.assert_called_once_with(1)

    def test_delete_dry_run(self):
        client = _make_client()
        execute_actions(client, uid=1, action={"delete": True}, dry_run=True)
        client.delete_email.assert_not_called()

    def test_delete_skips_other_actions(self):
        client = _make_client()
        execute_actions(client, uid=1, action={"delete": True, "flag": True})
        client.delete_email.assert_called_once()
        client.flag_email.assert_not_called()


class TestMarkReadUnread:
    def test_mark_read(self):
        client = _make_client()
        execute_actions(client, uid=1, action={"mark_read": True})
        client.mark_read.assert_called_once_with(1)

    def test_mark_unread(self):
        client = _make_client()
        execute_actions(client, uid=1, action={"mark_unread": True})
        client.mark_unread.assert_called_once_with(1)


class TestLabelAction:
    def test_add_label(self):
        client = _make_client()
        execute_actions(client, uid=1, action={"label": "Important"})
        client.add_label.assert_called_once_with(1, "Important")


class TestAutoSortBySender:
    def _make_parsed(self, from_addr):
        parsed = MagicMock()
        parsed.from_addr = from_addr
        return parsed

    def test_auto_sort_moves_to_sender_folder(self):
        client = _make_client()
        parsed = self._make_parsed("John Doe <john@example.com>")
        execute_actions(client, uid=1, action={"auto_sort_by_sender": True}, parsed_email=parsed)
        client.move_email.assert_called_once_with(1, "john@example.com")

    def test_auto_sort_bare_email(self):
        client = _make_client()
        parsed = self._make_parsed("john@example.com")
        execute_actions(client, uid=1, action={"auto_sort_by_sender": True}, parsed_email=parsed)
        client.move_email.assert_called_once_with(1, "john@example.com")

    def test_auto_sort_empty_sender_skips(self):
        client = _make_client()
        parsed = self._make_parsed("")
        execute_actions(client, uid=1, action={"auto_sort_by_sender": True}, parsed_email=parsed)
        client.move_email.assert_not_called()

    def test_auto_sort_no_parsed_email_skips(self):
        client = _make_client()
        execute_actions(client, uid=1, action={"auto_sort_by_sender": True})
        client.move_email.assert_not_called()

    def test_auto_sort_dry_run(self):
        client = _make_client()
        parsed = self._make_parsed("John <john@example.com>")
        execute_actions(client, uid=1, action={"auto_sort_by_sender": True}, dry_run=True, parsed_email=parsed)
        client.move_email.assert_not_called()


class TestCombinedActions:
    def test_move_and_flag(self):
        client = _make_client()
        execute_actions(client, uid=1, action={"move_to": "Jobs", "flag": True})
        client.move_email.assert_called_once_with(1, "Jobs")
        client.flag_email.assert_called_once_with(1, True)
