"""Tests for email_parser module."""

import email.mime.multipart
import email.mime.text

from open_email.email_parser import decode_header_value, parse_email


def _build_simple_email(from_addr="sender@example.com", to_addr="me@test.com",
                        subject="Test Subject", body="Hello, World!") -> bytes:
    msg = email.mime.text.MIMEText(body)
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg["Date"] = "Thu, 01 Jan 2025 12:00:00 +0000"
    return msg.as_bytes()


def _build_multipart_email(text_body="Plain text", html_body="<p>HTML body</p>") -> bytes:
    msg = email.mime.multipart.MIMEMultipart("alternative")
    msg["From"] = "sender@example.com"
    msg["To"] = "me@test.com"
    msg["Subject"] = "Multipart Test"
    msg.attach(email.mime.text.MIMEText(text_body, "plain"))
    msg.attach(email.mime.text.MIMEText(html_body, "html"))
    return msg.as_bytes()


class TestParseSimpleEmail:
    def test_basic_fields(self):
        raw = _build_simple_email()
        parsed = parse_email(42, raw)
        assert parsed.uid == 42
        assert parsed.from_addr == "sender@example.com"
        assert parsed.to_addr == "me@test.com"
        assert parsed.subject == "Test Subject"
        assert "Hello, World!" in parsed.body_text

    def test_empty_body(self):
        raw = _build_simple_email(body="")
        parsed = parse_email(1, raw)
        assert parsed.body_text == ""


class TestParseMultipartEmail:
    def test_extracts_text_and_html(self):
        raw = _build_multipart_email()
        parsed = parse_email(1, raw)
        assert "Plain text" in parsed.body_text
        assert "<p>HTML body</p>" in parsed.body_html

    def test_subject(self):
        raw = _build_multipart_email()
        parsed = parse_email(1, raw)
        assert parsed.subject == "Multipart Test"


class TestDecodeHeader:
    def test_plain_header(self):
        assert decode_header_value("Hello World") == "Hello World"

    def test_none_header(self):
        assert decode_header_value(None) == ""

    def test_encoded_header(self):
        # RFC2047 encoded UTF-8
        encoded = "=?utf-8?B?SGVsbG8gV29ybGQ=?="
        assert decode_header_value(encoded) == "Hello World"
