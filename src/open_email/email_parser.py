"""Parse raw email bytes into structured data."""

import email
import email.header
import email.utils
import logging
from dataclasses import dataclass, field
from email.message import Message

logger = logging.getLogger(__name__)


@dataclass
class ParsedEmail:
    """Structured representation of a parsed email."""
    uid: int
    from_addr: str = ""
    to_addr: str = ""
    subject: str = ""
    date: str = ""
    body_text: str = ""
    body_html: str = ""
    headers: dict = field(default_factory=dict)


def decode_header_value(value: str | None) -> str:
    """Decode an RFC2047-encoded email header value."""
    if not value:
        return ""
    decoded_parts = []
    for part, charset in email.header.decode_header(value):
        if isinstance(part, bytes):
            decoded_parts.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            decoded_parts.append(part)
    return " ".join(decoded_parts)


def extract_body(msg: Message) -> tuple[str, str]:
    """Extract text/plain and text/html body from a message."""
    text_body = ""
    html_body = ""

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition", ""))
            if "attachment" in disposition:
                continue

            try:
                payload = part.get_payload(decode=True)
                if payload is None:
                    continue
                charset = part.get_content_charset() or "utf-8"
                decoded = payload.decode(charset, errors="replace")
            except Exception:
                continue

            if content_type == "text/plain" and not text_body:
                text_body = decoded
            elif content_type == "text/html" and not html_body:
                html_body = decoded
    else:
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                decoded = payload.decode(charset, errors="replace")
                if msg.get_content_type() == "text/html":
                    html_body = decoded
                else:
                    text_body = decoded
        except Exception as e:
            logger.warning("Failed to decode message body: %s", e)

    return text_body, html_body


def parse_email(uid: int, raw_bytes: bytes) -> ParsedEmail:
    """Parse raw email bytes into a ParsedEmail object."""
    msg = email.message_from_bytes(raw_bytes)

    from_addr = decode_header_value(msg.get("From", ""))
    to_addr = decode_header_value(msg.get("To", ""))
    subject = decode_header_value(msg.get("Subject", ""))
    date = msg.get("Date", "")
    text_body, html_body = extract_body(msg)

    return ParsedEmail(
        uid=uid,
        from_addr=from_addr,
        to_addr=to_addr,
        subject=subject,
        date=date,
        body_text=text_body,
        body_html=html_body,
        headers={k: decode_header_value(v) for k, v in msg.items()},
    )
